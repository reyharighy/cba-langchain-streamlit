"""A module to manage the project session."""

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

# third-party
import pandas as pd
import streamlit as st

# internal
from .chain import Chain
from cache import (
    load_dataframe,
    load_manifest
)
from database import (
    index_prompt_manifest,
    show_prompt_manifest,
    store_prompt_manifest,
)
from model import (
    Project,
    PromptManifest,
    PromptManifestCreate,
    PromptManifestIndex,
    PromptManifestShow
)
from utils import streamlit_status_container

@dataclass
class SessionContext:
    """Provide context required by several process within the session."""

    total_manifest: int = 0
    prompt: str = ""
    response: Optional[Dict[str, Any]] = None
    prompt_manifest_context: Optional[str] = None

class Session:
    """Manage the project assigned in the session."""

    # Set true to run the session in the mockup mode
    mockup: bool = False

    def __init__(self, project: Project) -> None:
        """Initialize session attributes when handling the project inside the Streamlit app."""
        self.context: SessionContext = SessionContext()
        self.project: Project = project
        self.chain: Chain = Chain()

    def run(self) -> None:
        """Run the project session.
        
        The implementation redesigns the rerun process of the Sreamlit app from top to bottom.
        """
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

        self.chain.context.dataset_dir = self.project.dataset_dir
        self.chain.context.dataset_file = self.project.dataset_file

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

        prompt_manifests: List[PromptManifest] = index_prompt_manifest(params)

        if prompt_manifests:
            for prompt_manifest in prompt_manifests:
                prompt_manifest_context: Dict[Literal["prompt", "context"], str] = {
                    "prompt": prompt_manifest.prompt,
                    "context": prompt_manifest.context
                }

                self.chain.context.all_contexts.append(prompt_manifest_context)
                self.execute_manifest_file(prompt_manifest.manifest_file)

        self.context.total_manifest = len(prompt_manifests)
        self.chain.context.total_manifest = self.context.total_manifest

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
            self.context.response = {
                "input": f"{self.context.prompt}",
                "output": "Example output from the response in mockup mode."
            }

            self.context.prompt_manifest_context = "Example context from mockup mode."
        else:
            self.chain.prepare_agent()
            self.context.response = self.chain.run_agent(self.context.prompt)

            if self.context.response:
                self.chain.prepare_context()

                self.context.prompt_manifest_context = self.chain.run_context(
                    prompt=self.context.prompt,
                    response=self.context.response["output"]
                )

        self.store_new_prompt_manifest()

    def store_new_prompt_manifest(self) -> None:
        """Create the new prompt manifest model and store it to database.

        This method will always be called in every chat request.
        Though, the execution is determined from response and prompt manifest context.
        If both exist, the prompt manifest is stored to database.
        Then, the new manifest file will be created.
        """
        if self.context.response and self.context.prompt_manifest_context:
            self.context.total_manifest += 1

            prompt_manifest_create: PromptManifestCreate = PromptManifestCreate(
                project_id=self.project.project_id,
                user_id=self.project.user_id,
                prompt_manifest_no=self.context.total_manifest,
                prompt=self.context.response["input"],
                context=self.context.prompt_manifest_context
            )

            new_prompt_manifest = prompt_manifest_create()
            store_prompt_manifest(new_prompt_manifest)

            self.create_manifest_file()

    def create_manifest_file(self) -> None:
        """Create a new manifest file based-on the final answer of AI agent.
        
        The new file will be stored inside the specified directory of the project metadata.
        The extension of file should be in .py.
        """
        manifest_file: str = f"manifest_{self.context.total_manifest}.py"
        response_input: str = ""
        response_output: str = ""

        if self.context.response and self.context.prompt:
            response_input = self.context.prompt
            response_output = self.context.response["output"]

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

        new_prompt_manifest: Optional[PromptManifest] = show_prompt_manifest(
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
        if self.context.response:
            for word in str(self.context.response["output"]).split(" "):
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
