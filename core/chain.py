"""A module related to chain construction using Langchain framework."""

# standard
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
)

# third-party
import numpy as np
from e2b_code_interpreter import Execution
from e2b_code_interpreter.code_interpreter_sync import Sandbox
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langdetect import detect
from nltk.corpus import stopwords
from sentence_transformers import CrossEncoder
from translate import Translator

# internal
from cache import (
    load_agent,
    load_agent_prompt_template,
    load_context_prompt_template,
    load_df_info,
    load_llm,
    load_transformer,
)
from model import ExecutePythonArgs
from utils import streamlit_status_container

@dataclass
class ChainContext:
    """Provide context required by several process within the chain."""

    dataset_dir: str = ""
    dataset_file: str = ""
    df_attrs: str = ""
    total_manifest: int = 0
    all_contexts: List[Dict[Literal["prompt", "context"], str]] = field(default_factory=list)
    relevant_context: str = ""

class Chain:
    """Class to manage the orchestration of the runnable chain of Langchain."""

    def __init__(self) -> None:
        """Initialize the chain orchestrator."""
        self.context: ChainContext = ChainContext()
        self.transformer: Optional[CrossEncoder] = None
        self.llm: Optional[ChatGroq] = None
        self.tools: List[StructuredTool] = []
        self.prompt_template: Optional[ChatPromptTemplate] = None
        self.agent: Optional[Runnable[Any, Any]] = None
        self.agent_executor: Optional[AgentExecutor] = None

    @streamlit_status_container("Preparing AI Agent model", "AI Agent model preparation completed")
    def prepare_agent(self) -> None:
        """Prepare all resources and runnables before running AI Agent.

        The AI Agent directly processes the prompt from the user.
        """
        self.context.df_attrs = load_df_info(
            dataset_dir=self.context.dataset_dir,
            dataset_file=self.context.dataset_file
        )

        self.transformer = load_transformer()
        self.llm = load_llm("openai/gpt-oss-120b")
        self.tools = self.get_tools()
        self.prompt_template = load_agent_prompt_template()

        self.agent = load_agent(
            llm=self.llm,
            _tools=self.tools,
            prompt_template=self.prompt_template
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True
        )

    def get_tools(self) -> List[StructuredTool]:
        """Assign all tools for AI Agent to use.

        Returns:
            List of structured tools with defined schema args.

        """
        execute_python = StructuredTool.from_function(
            func=self.execute_python,
            args_schema=ExecutePythonArgs.model_json_schema(),
            description="Execute python code in a Jupyter notebook."
        )

        return [
            execute_python
        ]

    def execute_python(self, code: str) -> Execution:
        """Execute python code in a Jupyter notebook inside the sandbox environment.

        This tool is only intended for the user's request that involves data analytics.

        Args:
            code: Python code as a plain string. Do not wrap in JSON, Markdown, or objects.

        Returns:
            Represents the result of a cell execution.

        """
        dataset_path = self.context.dataset_dir + self.context.dataset_file

        with Sandbox() as sandbox:
            with open(dataset_path, "rb") as dataset:
                sandbox.files.write(dataset_path, dataset.read())

            execution: Execution = sandbox.run_code(
                code=code,
                language="python",
                on_stdout=lambda stdout: print("[Code Interpreter stdout]", stdout),
                on_stderr=lambda stderr: print("[Code Interpreter stderr]", stderr)
            )

            return execution

    @streamlit_status_container("Running AI Agent", "AI Agent run completed")
    def run_agent(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Run AI Agent as configured within prepare_agent method.

        Args:
            prompt: The prompt input by the user through chat_input element.

        Returns:
            Optional dictionary data that's parsed by AI Agent with input and output.

        """
        if self.context.total_manifest:
            self.context.relevant_context = self.load_relevant_context(prompt)
        else:
            self.context.relevant_context = ""

        if self.agent_executor:
            response = self.agent_executor.invoke(
                input={
                    "input": prompt,
                    "dataset_path": self.context.dataset_dir + self.context.dataset_file,
                    "df_attrs": self.context.df_attrs,
                    "tools": self.tools,
                    "chat_history": self.context.relevant_context
                }
            )

            return response

        return None

    def load_relevant_context(self, prompt: str) -> str:
        """Load relevant contexts to be embedded into AI Agent system prompt.

        The similarity score will be standardized using logistic sigmoid.
        Recalculated score will be between 0 and 1.
        IMPORTANT: This method is experimental purpose.

        Args:
            prompt: Prompt for the user to calculate context similarity score.

        Returns:
            A collection of contexts with similarity score above 0.9.
            If no contexts are passing the threshold score, return the last context.

        """
        index = 0
        original_prompt_lang = detect(prompt)
        header = "You have relevant contexts to answer the current question:"
        relevant_context = ""

        for context in self.context.all_contexts:
            processed_prompt = prompt
            context_pair = " ".join(context.values())
            context_pair_lang = detect(context_pair)

            if original_prompt_lang != context_pair_lang:
                translator = Translator(
                    from_lang=original_prompt_lang,
                    to_lang=context_pair_lang
                )

                processed_prompt = translator.translate(processed_prompt)

            processed_prompt = " ".join(
                [
                    word for word in processed_prompt.replace("?", "").split(" ")
                    if word not in stopwords.words()
                ]
            )

            if self.transformer:
                score = self.transformer.predict((processed_prompt, context_pair_lang))
                sigmoid_score = 1 / (1 + np.exp(-score))

                if sigmoid_score > 0.9:
                    index += 1

                    self.stringify_context(index, context)

        if len(relevant_context):
            return header + relevant_context

        return header + self.stringify_context(1, self.context.all_contexts[-1])

    def stringify_context(
        self,
        index: int,
        context: Dict[Literal["prompt", "context"], str]
    ) -> str:
        """Convert to string a pair of prompt and context.

        Stringified contexts are collected as relevant context when running AI Agent.

        Args:
            index: Number of context pair.
            context: Context to format as string.

        Returns:
            String formatted context.

        """
        stringfied_context = ""

        for key_type, text in context.items():
            if key_type == "prompt":
                stringfied_context += '\n' + f"Questin No. {index}: {text}"
            else:
                stringfied_context += '\n' + f"Response Context No. {index}: {text}"

        return stringfied_context

    @streamlit_status_container("Preparing context model", "Context model preparation completed")
    def prepare_context(self) -> None:
        """Prepare all resources and runnables before running context model.

        The context model inferences context from a pair of prompt and response.
        """
        self.llm = load_llm("openai/gpt-oss-20b")
        self.prompt_template = load_context_prompt_template()

    @streamlit_status_container("Getting response context", "Context response obtained")
    def run_context(self, prompt: str, response: str) -> Optional[str]:
        """Run context model as configured within prepare_context method.

        The chain is constructed using LCEL (Langchain Expression Language).
        See more on https://python.langchain.com/docs/concepts/lcel/.

        Args:
            prompt: The prompt input by the user through chat_input element.
            response: The response from AI Agent based-on the prompt passed in.

        Returns:
            Optional string of context that's inferenced by context model.

        """
        if self.llm and self.prompt_template:
            chain = self.prompt_template | self.llm

            reponse = chain.invoke(
                input={
                    "input": {
                        "question": prompt,
                        "answer": response
                    }
                }
            )

            return str(reponse.content)

        return None
