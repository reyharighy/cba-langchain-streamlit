"""A module to manage user application."""

# standard
from dataclasses import dataclass
from time import sleep
from typing import (
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
from .context_management import ContextManager
from .natural_language_orchestration import NaturalLanguageOrchestrator
from cache import (
    load_dataframe,
    load_manifest,
)
from common import streamlit_status_container
from model import (
    Manifest,
    ManifestCreate,
    ManifestIndex,
    ManifestShow,
    Project,
    ProjectCreate,
    ProjectShow,
)

@dataclass
class AppRuntime:
    """Provide runtime state required by several process within the user application."""

    total_manifest: int = 0
    query: Optional[str] = None
    response: Optional[str] = None
    summary: Optional[str] = None

class Application:
    """A class that implements the user application."""

    # Set true to run the session in the mockup mode
    mockup: bool = False

    def __init__(self) -> None:
        """Initialize the user application instance."""
        self.rt: AppRuntime = AppRuntime()
        self.ctm: ContextManager = ContextManager()
        self.nlo: NaturalLanguageOrchestrator = NaturalLanguageOrchestrator()

    def run(self, uuids: Dict[Literal["user_id", "project_id"], UUID]) -> None:
        """Run the project session.

        The implementation redesigns the rerun process of the Streamlit application that executes 
        code from top to bottom.

        Args:
            uuids: UUID of the project and user to consume.

        """
        self.project: Project = self.get_project(uuids)

        st.set_page_config(
            page_title=self.project.title,
            layout="wide",
            initial_sidebar_state="auto"
        )

        st.title(self.project.title)
        self.display_dataframe()
        self.load_manifests()

        if chat_input := st.chat_input("Chat with AI"):
            st.divider()
            self.rt.query = chat_input

            try:
                self.process_request()
                self.stream_new_manifest()
                st.session_state["success_message"] = True
                st.rerun()
            except Exception as _:
                with st.expander('Click to toggle cell', expanded=True):
                    with st.container(border=True):
                        st.error("Sorry, there's an error on our end.")

                sleep(3)
                st.session_state["error_message"] = True
                st.rerun()

        if "init_app" not in st.session_state:
            self.init_session_state()

        self.show_toast()

    def get_project(self, uuids: Dict[Literal["user_id", "project_id"], UUID]) -> Project:
        """Get the project metadata from database.

        If unset, create the new one and store it to database.

        Args:
            uuids: UUID of the project and user to consume.

        Returns:
            Base model of the project.

        """
        project_show_params: ProjectShow = ProjectShow(project_id=uuids["project_id"])
        project: Optional[Project] = self.ctm.show_project(project_show_params)

        if project is None:
            project_create_params: ProjectCreate = ProjectCreate(
                project_id=uuids["project_id"],
                user_id=uuids["user_id"],
                title="Data Penjualan Cafe Saujana",
                datasets="dataset.csv"
            )

            new_project: Project = project_create_params()
            self.ctm.store_project(new_project)

            return new_project

        return project

    def display_dataframe(self) -> None:
        """Display the dataframe inside the expander element from a given dataset path.

        Dataset path will passed to the orchestrator that is required for the sandbox environment 
        to locate the dataset that should be worked on. It will also then be used to load the 
        dataframe information that will be embedded to the system prompt.

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

        self.nlo.rt.dataset_dir = self.project.dataset_dir
        self.nlo.rt.dataset_file = self.project.dataset_file

    def load_manifests(self) -> None:
        """Load all manifest model from database.

        All fetched manifests will be added to orchestrator runtime states for filtering relevant 
        turns for the next user's query. It then run all manifest files to render all UI elements.
        Finally, save total manifest count inside runtime state to infer the next manifest file 
        number.

        """
        manifest_index_params: ManifestIndex = ManifestIndex(
            project_id=self.project.project_id,
            user_id=self.project.user_id
        )

        manifests: List[Manifest] = self.ctm.index_manifest(manifest_index_params)

        if manifests:
            for manifest in manifests:
                manifest_pair: Dict[Literal["query", "response", "summary"], str] = {
                    "query": manifest.query,
                    "response": manifest.response,
                    "summary": manifest.context
                }

                self.nlo.rt.manifest_turns.append(manifest_pair)
                self.execute_manifest_file(manifest.file_name)

        self.rt.total_manifest = len(manifests)

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
        """Process the request when the user input the query inside the chat_input element.

        All process defined within NaturalLanguageOrchestrator class will be implemented here.
        Mockup mode is used to start the session process without running LLM inference.

        """
        if self.mockup:
            self.rt.response = "Example output from the response in mockup mode."
            self.rt.summary = "Example contextual summary from mockup mode."
        else:
            if self.rt.query:
                self.nlo.prepare_react_agent()
                self.rt.response = self.nlo.run_react_agent(self.rt.query)

            if self.rt.query and self.rt.response:
                self.nlo.prepare_summary_agent()
                self.rt.summary = self.nlo.run_summary_agent(
                    query=self.rt.query,
                    response=self.rt.response
                )

        self.store_new_manifest()

    def store_new_manifest(self) -> None:
        """Create the new manifest model and store it to database.

        This method will always be called in every chat request.
        Though, the execution is determined from react agent response and its summary.
        If both exist, the manifest is stored to database.
        Then, the new manifest file will be created.

        """
        if self.rt.query and self.rt.response and self.rt.summary:
            self.rt.total_manifest += 1

            manifest_create_params: ManifestCreate = ManifestCreate(
                project_id=self.project.project_id,
                user_id=self.project.user_id,
                num=self.rt.total_manifest,
                query=self.rt.query,
                response=self.rt.response,
                context=self.rt.summary
            )

            new_manifest = manifest_create_params()
            self.ctm.store_manifest(new_manifest)

            self.create_manifest_file()

    def create_manifest_file(self) -> None:
        """Create a new manifest file based-on the final answer of AI agent.

        The new file will be stored inside the specified directory of the project metadata.
        The extension of file should be in .py.

        """
        manifest_file: str = f"manifest_{self.rt.total_manifest}.py"

        if self.rt.query and self.rt.response:
            with open(self.project.manifest_dir + manifest_file, "w", encoding="utf-8") as file:
                content: str = ""

                code_lines: List[str] = [
                    "import streamlit as st",
                    "def load_manifest():",
                    "\tst.divider()",
                    "\twith st.expander('Click to toggle cell', expanded=True):",
                    "\t\twith st.container(border=True):",
                    "\t\t\tst.badge('Your Query', color='orange')",
                    f"\t\t\tst.write(\"\"\"{self.rt.query}\"\"\")",
                    "\t\tst.badge('AI Response', color='blue')",
                    f"\t\tst.markdown(\"\"\"{self.rt.response}\"\"\", unsafe_allow_html=True)",
                    "load_manifest()"
                ]

                for line in code_lines:
                    content += line + '\n'

                file = file.write(content)

    def stream_new_manifest(self) -> None:
        """Fetch a newly created manifest model from database.

        The new model content will be rendered in a stream-like process to the app UI.

        """
        manifest_show_params: ManifestShow = ManifestShow(
            project_id=self.project.project_id,
            user_id=self.project.user_id,
            num=self.rt.total_manifest
        )

        manifest: Optional[Manifest] = self.ctm.show_manifest(manifest_show_params)

        if manifest:
            st.divider()

            with st.expander('Click to toggle cell', expanded=True):
                with st.container(border=True):
                    st.badge('Your Query', color='orange')
                    st.write(self.rt.query)

                st.badge('AI Response', color='blue')
                st.write_stream(self.stream_generator)

    def stream_generator(self) -> Generator:
        """Write sequence of the response output as word chunks.

        Returns:
            Generator to stream a sequence of word from LLM response

        """
        if self.rt.response:
            for word in str(self.rt.response).split(" "):
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
            st.toast(
                "###### **AI Agent could not process your request. Please try again**", 
                duration="long"
            )

            st.session_state["error_message"] = False
