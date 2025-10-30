"""A module to manage natural language orchestrator."""

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
    load_df_info,
    load_llm,
    load_sentence_transformer,
    load_summary_prompt_template,
)
from common import streamlit_status_container
from model import ExecutePythonArgsSchema

@dataclass
class OrchestratorRuntime:
    """Provide runtime state required by several process within the orchestrator."""

    dataset_dir: str = ""
    dataset_file: str = ""
    df_attrs: str = ""
    total_manifest: int = 0
    all_contexts: List[Dict[Literal["prompt", "context"], str]] = field(default_factory=list)
    relevant_context: str = ""

class NaturalLanguageOrchestrator:
    """A class that implements the natural language orchestrator."""

    def __init__(self) -> None:
        """Initialize the natural language orchestrator instance."""
        self.rt: OrchestratorRuntime = OrchestratorRuntime()

    def prepare_react_agent(self) -> None:
        """Prepare all resources and runnables before running AI Agent.

        The AI Agent directly processes the prompt from the user.

        """
        self.rt.df_attrs = load_df_info(
            dataset_dir=self.rt.dataset_dir,
            dataset_file=self.rt.dataset_file
        )

        self.sentence_transformer: CrossEncoder = load_sentence_transformer()
        self.llm: ChatGroq = load_llm("openai/gpt-oss-120b")
        self.tools: List[StructuredTool] = self.get_tools()
        self.prompt_template: ChatPromptTemplate = load_agent_prompt_template()

        self.agent: Runnable[Any, Any] = load_agent(
            llm=self.llm,
            _tools=self.tools,
            prompt_template=self.prompt_template
        )

        self.agent_executor: AgentExecutor = AgentExecutor(
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
            args_schema=ExecutePythonArgsSchema.model_json_schema(),
            description="Execute python code in a Jupyter notebook."
        )

        return [
            execute_python
        ]

    @streamlit_status_container("Performing Data Analysis", "Analysis completed")
    def execute_python(self, code: str) -> Execution:
        """Execute python code inside the sandbox environment.

        This tool is only intended for the user's request that involves data analytics.

        Args:
            code: Python code as a plain string. Do not wrap in JSON, Markdown, or objects.

        Returns:
            Represents the result of a cell execution.

        """
        dataset_path = self.rt.dataset_dir + self.rt.dataset_file

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

    @streamlit_status_container("Running AI Agent", "AI Agent run completed", expanded=True)
    def run_react_agent(self, prompt: str) -> Dict[str, Any]:
        """Run AI Agent as configured within prepare_react_agent method.

        Args:
            prompt: The prompt input by the user through chat_input element.

        Returns:
            Optional dictionary data that's parsed by AI Agent with input and output.

        """
        if self.rt.total_manifest:
            self.rt.relevant_context = self.load_relevant_context(prompt)
        else:
            self.rt.relevant_context = ""

        response = self.agent_executor.invoke(
            input={
                "input": prompt,
                "dataset_path": self.rt.dataset_dir + self.rt.dataset_file,
                "df_attrs": self.rt.df_attrs,
                "tools": self.tools,
                "chat_history": self.rt.relevant_context
            }
        )

        return response

    @streamlit_status_container("Finding relevant contexts", "Contexts filtered")
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

        for context in self.rt.all_contexts:
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

            if self.sentence_transformer:
                score = self.sentence_transformer.predict((processed_prompt, context_pair_lang))
                sigmoid_score = 1 / (1 + np.exp(-score))

                if sigmoid_score > 0.9:
                    index += 1

                    self.stringify_context(index, context)

        if len(relevant_context):
            return header + relevant_context

        return header + self.stringify_context(1, self.rt.all_contexts[-1])

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

    def prepare_summary_agent(self) -> None:
        """Prepare all resources and runnables before running summary model.

        The summary model inferences summary from a pair of prompt and response.

        """
        self.llm = load_llm("openai/gpt-oss-20b")
        self.prompt_template = load_summary_prompt_template()

    @streamlit_status_container("Getting summary", "Summary obtained")
    def run_summary_agent(self, prompt: str, response: str) -> str:
        """Run summary model as configured within prepare_summary_agent method.

        The chain is constructed using LCEL (Langchain Expression Language).
        See more on https://python.langchain.com/docs/concepts/lcel/.

        Args:
            prompt: The prompt input by the user through chat_input element.
            response: The response from AI Agent based-on the prompt passed in.

        Returns:
            Optional string of summary that's inferenced by summary model.

        """
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
