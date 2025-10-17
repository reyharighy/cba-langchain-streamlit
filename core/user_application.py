"""A module to manage user application."""

# standard
from dataclasses import dataclass
from time import sleep
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
)
from uuid import UUID

# third-party
import pandas as pd
import streamlit as st

# internal
from .database_management import DatabaseManagement
from .natural_language_orchestrator import NaturalLanguageOrchestrator
from cache import (
    load_dataframe,
    load_manifest,
)
from common import streamlit_status_container
from model import (
    Project,
    ProjectCreate,
    ProjectShow,
    PromptManifest,
    PromptManifestCreate,
    PromptManifestIndex,
    PromptManifestShow
)

@dataclass
class Context:
    """Provide context required by several process within Application class."""

    total_manifest: int = 0
    prompt: str = ""
    react_agent_response: Optional[Dict[str, Any]] = None
    response_summary: Optional[str] = None

class UserApplication:
    """A class that implements the user application."""

    # Set true to run the session in the mockup mode
    mockup: bool = False

    def __init__(self) -> None:
        """Initialize the user application instance."""
        self.context: Context = Context()
        self.db_management: DatabaseManagement = DatabaseManagement()
        self.nl_orchestrator: NaturalLanguageOrchestrator = NaturalLanguageOrchestrator()

    def run(self, uuids: Dict[Literal["user_id", "project_id"], UUID]) -> None:
        """Run the project session.

        The implementation redesigns the rerun process of the Sreamlit app from top to bottom.

        Args:
            uuids: UUID of the project and user to consume.

        """
        self.project: Project = self.setup_project(uuids)

        st.set_page_config(
            page_title=self.project.title,
            layout="wide",
            initial_sidebar_state="auto"
        )

        st.title(self.project.title)
        self.display_dataframe()
        self.load_prompt_manifests()

        if chat_input := st.chat_input("Chat with AI"):
            st.divider()

            try:
                self.context.prompt = chat_input
                self.process_request()
                self.stream_new_manifest()
                st.session_state["success_message"] = True
                st.rerun()
            except Exception as _:
                st.session_state["error_message"] = True
                sleep(3)
                st.rerun()

        if "init_app" not in st.session_state:
            self.init_session_state()

        self.show_toast()

    def setup_project(self, uuids: Dict[Literal["user_id", "project_id"], UUID]) -> Project:
        """Store project metadata to database if unset. Otherwise get the project metadata.

        This function always compute at initialization.
        Thus, we can start download stopwords, required when loading relevant contexts.

        Args:
            uuids: UUID of the project and user to consume.

        Returns:
            Base model of the project.

        """
        project_show: ProjectShow = ProjectShow(project_id=uuids["project_id"])
        project: Optional[Project] = self.db_management.show_project(project_show)

        if project is None:
            project_create: ProjectCreate = ProjectCreate(
                project_id=uuids["project_id"],
                user_id=uuids["user_id"],
                title="Data Penjualan Cafe Saujana",
                datasets="dataset.csv"
            )

            new_project: Project = project_create()
            self.db_management.store_project(new_project)

            return new_project

        return project

    def display_dataframe(self) -> None:
        """Display the dataframe inside the expander element from a given dataset path.

        All dataset information will passed to the chain context.
        This information is required for several process within the chain.
        """
        with st.expander("Click to toggle the table view", expanded=True):
            dataframe: pd.DataFrame = load_dataframe(
                dataset_dir=self.project.dataset_dir,
                dataset_file=self.project.dataset_file
            )

            st.dataframe(
                data=dataframe,
                hide_index=True,
                width="stretch"
            )

        self.nl_orchestrator.context.dataset_dir = self.project.dataset_dir
        self.nl_orchestrator.context.dataset_file = self.project.dataset_file

    def load_prompt_manifests(self) -> None:
        """Load all prompt manifest model from database and setting up several attributes.

        All fetched prompt manifests will be added to chat history of chain context.
        It then run all manifest files to render all UI elements.
        Finally, save total manifest count inside context to infer the next manifest file number.
        """
        params: PromptManifestIndex = PromptManifestIndex(
            project_id=self.project.project_id,
            user_id=self.project.user_id
        )

        prompt_manifests: List[PromptManifest] = self.db_management.index_prompt_manifest(
            params=params
        )

        if prompt_manifests:
            for prompt_manifest in prompt_manifests:
                prompt_manifest_context: Dict[Literal["prompt", "context"], str] = {
                    "prompt": prompt_manifest.prompt,
                    "context": prompt_manifest.context
                }

                self.nl_orchestrator.context.all_contexts.append(prompt_manifest_context)
                self.execute_manifest_file(prompt_manifest.manifest_file)

        self.context.total_manifest = len(prompt_manifests)
        self.nl_orchestrator.context.total_manifest = self.context.total_manifest

    def execute_manifest_file(self, manifest_file: str) -> None:
        """Execute manifest file related to the project.

        Args:
            manifest_file: Name of the manifest file to execute.

        """
        loader, module = load_manifest(
            manifest_dir=f"{self.project.manifest_dir}",
            manifest_file=manifest_file
        )

        if loader and module:
            loader.exec_module(module)

    @streamlit_status_container("Processing request", "Request process completed", mockup, True)
    def process_request(self) -> None:
        """Process the request when the user input the prompt inside the chat_input element.

        All process defined within Chain class will be implemented here.
        Mockup mode is used to start the session process without running LLM function.
        """
        if self.mockup:
            self.context.react_agent_response = {
                "input": f"{self.context.prompt}",
                "output": "Example output from the response in mockup mode."
            }

            self.context.response_summary = "Example contextual summary from mockup mode."
        else:
            self.nl_orchestrator.prepare_react_agent()
            self.context.react_agent_response = self.nl_orchestrator.run_react_agent(
                prompt=self.context.prompt
            )

            if self.context.react_agent_response:
                self.nl_orchestrator.prepare_summary_generation_agent()
                self.context.response_summary = self.nl_orchestrator.run_summary_generation_agent(
                    prompt=self.context.prompt,
                    response=self.context.react_agent_response["output"]
                )

        self.store_new_prompt_manifest()

    def store_new_prompt_manifest(self) -> None:
        """Create the new prompt manifest model and store it to database.

        This method will always be called in every chat request.
        Though, the execution is determined from react agent response and its summary.
        If both exist, the prompt manifest is stored to database.
        Then, the new manifest file will be created.
        """
        if self.context.react_agent_response and self.context.response_summary:
            self.context.total_manifest += 1

            prompt_manifest_create: PromptManifestCreate = PromptManifestCreate(
                project_id=self.project.project_id,
                user_id=self.project.user_id,
                prompt_manifest_no=self.context.total_manifest,
                prompt=self.context.react_agent_response["input"],
                context=self.context.response_summary
            )

            new_prompt_manifest = prompt_manifest_create()
            self.db_management.store_prompt_manifest(new_prompt_manifest)

            self.create_manifest_file()

    def create_manifest_file(self) -> None:
        """Create a new manifest file based-on the final answer of AI agent.

        The new file will be stored inside the specified directory of the project metadata.
        The extension of file should be in .py.
        """
        manifest_file: str = f"manifest_{self.context.total_manifest}.py"
        response_input: str = ""
        response_output: str = ""

        if self.context.react_agent_response:
            response_input = self.context.prompt
            response_output = self.context.react_agent_response["output"]

        with open(self.project.manifest_dir + manifest_file, "w", encoding="utf-8") as file:
            content: str = ""

            code_lines: List[str] = [
                "import streamlit as st",
                "def load_manifest():",
                "\tst.divider()",
                "\twith st.expander('Click to toggle cell', expanded=True):",
                "\t\twith st.container(border=True):",
                "\t\t\tst.badge('Your Prompt', color='orange')",
                f"\t\t\tst.write(\"\"\"{response_input}\"\"\")",
                "\t\tst.badge('AI Response', color='blue')",
                f"\t\tst.markdown(\"\"\"{response_output}\"\"\", unsafe_allow_html=True)",
                "load_manifest()"
            ]

            for line in code_lines:
                content += line + '\n'

            file = file.write(content)

    def stream_new_manifest(self) -> None:
        """Fetch a newly created prompt manifest model from database.

        The new model content will be rendered in a stream-like process to the app UI.
        """
        prompt_manifest_show_params: PromptManifestShow = PromptManifestShow(
            project_id=self.project.project_id,
            user_id=self.project.user_id,
            prompt_manifest_no=self.context.total_manifest
        )

        new_prompt_manifest: Optional[PromptManifest] = self.db_management.show_prompt_manifest(
            prompt_manifest_show_params
        )

        if new_prompt_manifest:
            st.divider()

            with st.expander('Click to toggle cell', expanded=True):
                with st.container(border=True):
                    st.badge('Your prompt', color='orange')
                    st.write(self.context.prompt)

                st.badge('AI Response', color='blue')
                st.write_stream(self.stream_generator)

    def stream_generator(self) -> Generator:
        """Write sequence of the response output as word chunks.

        Returns:
            Generator to stream a sequence of word from LLM response

        """
        if self.context.react_agent_response:
            for word in str(self.context.react_agent_response["output"]).split(" "):
                yield word + " "
                sleep(0.02)

    def init_session_state(self) -> None:
        """Initialize session state within Streamlit app."""
        if "success_message" not in st.session_state:
            st.session_state["success_message"] = False

        if "error_message" not in st.session_state:
            st.session_state["error_message"] = False

        st.session_state["init_app"] = not None
        st.rerun()

    def show_toast(self) -> None:
        """Show toast message each time user's request is processed."""
        if st.session_state["success_message"]:
            st.toast("###### **Your request is completed**", duration="long")
            st.session_state["success_message"] = False

        if st.session_state["error_message"]:
            st.toast("###### **AI Agent could not process your request**", duration="long")
            st.session_state["error_message"] = False
