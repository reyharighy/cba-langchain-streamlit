"""A module to manage natural language orchestrator."""

# standard
import re
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
import markdown
import numpy as np
from bs4 import BeautifulSoup
from e2b_code_interpreter import Execution
from e2b_code_interpreter.code_interpreter_sync import Sandbox
from langchain.agents.agent import AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langdetect import detect
from nltk.corpus import stopwords
from pinecone import SearchQuery
from pinecone.db_data import _Index
from pinecone.db_data.models import SearchRecordsResponse
from sentence_transformers import CrossEncoder

# internal
from cache import (
    load_agent,
    load_cross_encoder,
    load_df_info,
    load_llm,
    load_react_prompt_template,
    load_search_engine,
    load_summary_prompt_template,
    load_translator,
    load_vector_database,
)
from common import (
    execute_python_code_tool_description,
    pinecone_search_tool_description,
    streamlit_status_container,
    tavily_search_tool_description,
)
from model import (
    ExecutePythonCodeArgsSchema,
    PineconeSearchArgsSchema,
    TavilySearchArgsSchema,
)

@dataclass
class OrchestratorRuntime:
    """Provide runtime state required by several process within the orchestrator."""

    dataset_dir: str = ""
    dataset_file: str = ""
    manifest_turns: List[Dict[Literal["query", "response", "summary"], str]] = field(default_factory=list) # noqa: E501

class NaturalLanguageOrchestrator:
    """A class that implements the natural language orchestrator."""

    def __init__(self) -> None:
        """Initialize the natural language orchestrator instance."""
        self.rt: OrchestratorRuntime = OrchestratorRuntime()

    def prepare_react_agent(self) -> None:
        """Prepare all resources and runnables before running react agent."""
        self.llm: ChatGroq = load_llm("openai/gpt-oss-120b")
        self.prompt_template: ChatPromptTemplate = load_react_prompt_template()
        self.vector_database: _Index = load_vector_database()
        self.search_engine: TavilySearch = load_search_engine()
        self.cross_encoder: CrossEncoder = load_cross_encoder()

        tools: List[StructuredTool] = self.load_tools()
        agent: Runnable[Any, Any] = load_agent(
            llm=self.llm,
            _tools=tools,
            prompt_template=self.prompt_template
        )

        self.agent_executor: AgentExecutor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=False
        )

    def load_tools(self) -> List[StructuredTool]:
        """Assign all tools for AI Agent to use.

        Returns:
            List of structured tools with defined schema args.

        """
        execute_python_code = StructuredTool.from_function(
            func=self.execute_python_code,
            args_schema=ExecutePythonCodeArgsSchema.model_json_schema(),
            description=execute_python_code_tool_description.replace('\n', '')
        )

        pinecone_search = StructuredTool.from_function(
            func=self.pinecone_search,
            args_schema=PineconeSearchArgsSchema.model_json_schema(),
            description=pinecone_search_tool_description.replace('\n', '')
        )

        tavily_search = StructuredTool.from_function(
            func=self.tavily_search,
            args_schema=TavilySearchArgsSchema.model_json_schema(),
            description=tavily_search_tool_description.replace('\n', '')
        )

        return [
            execute_python_code,
            pinecone_search,
            tavily_search,
        ]

    @streamlit_status_container("Performing data analysis", "Analysis completed")
    def execute_python_code(self, code: str) -> Execution:
        """Perform Python code execution inside the sandbox environment.
        
        This tool is only intended for the user's request that involves data analytics process 
        using Python libraries.

        Args:
            code: Python code to run in a sandbox environment.

        Returns:
            Represents the result of a cell execution.

        """
        dataset_path = self.rt.dataset_dir + self.rt.dataset_file

        with Sandbox() as sandbox:
            with open(dataset_path, "rb") as dataset:
                sandbox.files.write(dataset_path, dataset.read())

            execution: Execution = sandbox.run_code(
                code=code,
                language="python"
            )

            return execution

    @streamlit_status_container("Retrieving private knowledge", "Knowledge retrieved")
    def pinecone_search(self, query: str) -> SearchRecordsResponse:
        """Perform private knowledge retrieval from vector database.

        This tool is only intended for the user's request that requires various private knowledge 
        retrieval of the user.

        Args:
            query: Query to use for searching information in a vector database.

        Returns:
            Represents a list of search record response from vector database.

        """
        search_query: SearchQuery = SearchQuery(
            inputs={"text": query},
            top_k=3
        )

        search_response: SearchRecordsResponse = self.vector_database.search(
            namespace="internal-docs",
            query=search_query
        )

        return search_response["result"]["hits"]

    @streamlit_status_container("Searching on internet", "Search completed")
    def tavily_search(self, query: str) -> List[Dict[str, str]]:
        """Perform information retrieval on the internet using tavily search engine.

        This tool is only intended for the user's requests that requires various information
        that could be found on the internet.

        Args:
            query: Query to use for searching informasion on the internet.

        Returns:
            Represents a list of search results based-on the query given.

        """
        results = self.search_engine.invoke({"query": query})["results"]

        return [
            {
                "title": result["title"],
                "content": result["content"]
            } for result in results
        ]

    @streamlit_status_container("Running AI Agent", "AI Agent run completed", expanded=True)
    def run_react_agent(self, query: str) -> str:
        """Run react agent as configured within prepare_react_agent method.

        At first, it will try to load the dataframe attributes for certain dataset path. It will 
        then filter relevant turns based-on the current user's query. Finally, all information will 
        be embedded into system prompt as a guidance for LLM to follow.

        Args:
            query: The query input by the user through chat_input element.

        Returns:
            Optional dictionary data that's parsed by LLM with input and output.

        """
        df_attributes: str = load_df_info(
            dataset_dir=self.rt.dataset_dir,
            dataset_file=self.rt.dataset_file
        )

        relevant_turns: List[HumanMessage | AIMessage] = []

        if self.rt.manifest_turns:
            relevant_turns = self.load_relevant_turns(query)

        raw_output = self.agent_executor.invoke(
            input={
                "query": query,
                "chat_history": relevant_turns,
                "dataset_path": self.rt.dataset_dir + self.rt.dataset_file,
                "df_attributes": df_attributes,
            }
        )

        return raw_output["output"]

    @streamlit_status_container("Finding relevant contexts", "Contexts filtered")
    def load_relevant_turns(self, query: str) -> List[HumanMessage | AIMessage]:
        """Load relevant turns to be embedded into system prompt.

        This process is part of window-context management. The relevant turns is semantically 
        measured with similarity score. It will be standardized using logistic sigmoid. 
        Recalculated score will be between 0 and 1. If no turns are found to be relevant, the last 
        turn will be passed if it does exist.

        IMPORTANT: This method is experimental purpose.

        Args:
            query: The current query of the user to calculate context similarity score.

        Returns:
            A collection of relevant turns with similarity score above 0.75.
            If none are passing the threshold score, return the last context.

        """
        if len(self.rt.manifest_turns) == 1:
            return self.compose_turn_message(self.rt.manifest_turns[0])

        query_lang = detect(query)
        relevant_turns: List[HumanMessage | AIMessage] = []

        for manifest_turn in self.rt.manifest_turns:
            turn_pair = " ".join(manifest_turn.values())
            turn_pair = self.markdown_to_plain_text(turn_pair)
            turn_pair_lang = detect(turn_pair)

            if query_lang != turn_pair_lang:
                translator = load_translator(
                    query_lang=query_lang,
                    turn_pair_lang=turn_pair_lang
                )

                query = translator.translate(query)

            query = self.remove_stopwords(query)
            turn_pair = self.remove_stopwords(turn_pair)

            score = self.cross_encoder.predict((query, turn_pair))
            sigmoid_score = 1 / (1 + np.exp(-score))

            if sigmoid_score > 0.75:
                relevant_turns += self.compose_turn_message(manifest_turn)

        if len(relevant_turns):
            return relevant_turns

        return self.compose_turn_message(self.rt.manifest_turns[-1])

    def markdown_to_plain_text(self, md: str) -> str:
        """Convert Markdown (with or without HTML) into plain text.

        Args:
            md: string.

        Returns:
            A string.

        """
        html = markdown.markdown(md)
        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(separator=" ")
        text = re.sub(r"[^A-Za-z0-9()?.,:]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def remove_stopwords(self, query: str) -> str:
        """Remove the stopwords before measuring the similarity score.

        The goal of this method is to remove the words that are not semantically contributed when 
        measuring the similarity score.

        Args:
            query: The user's query that's going to be preprocessed for removing the stopwords.

        Returns:
            The processed query with stopwords being removed.

        """
        return " ".join(
            [
                word for word in query.replace("?", "").split(" ")
                if word not in stopwords.words()
            ]
        )

    def compose_turn_message(self, turn: Dict[Literal["query", "response", "summary"], str]
    ) -> List[HumanMessage | AIMessage]:
        """Format the relevant turns into a collection of BaseMessage classes.

        AIMessage is composed with the summary of the LLM response, not the response itself. 
        BaseMessage is built-in class provided by LangChain that's used to embed the memory of chat 
        history in the system prompt.

        Args:
            turn: Turn to format as a list of BaseMessage between user and AI Agent.

        Returns:
            A collection of BaseMessage that are constructed with HumanMessage and AIMessage.

        """
        messages: List[HumanMessage | AIMessage] = []

        for key_type, text in turn.items():
            if key_type == "query":
                messages.append(HumanMessage(text))
            elif key_type == "summary":
                messages.append(AIMessage(text))

        return messages

    def prepare_summary_agent(self) -> None:
        """Prepare all resources and runnables before running summary agent.

        The summary agent inferences summary from a turn resulting from the react agent process.
        """
        self.llm = load_llm("openai/gpt-oss-20b")
        self.prompt_template = load_summary_prompt_template()

    @streamlit_status_container("Getting summary", "Summary obtained")
    def run_summary_agent(self, query: str, response: str) -> str:
        """Run summary agent as configured within prepare_summary_agent method.

        It's preferable to embed the summary of the run_react_agent into system prompt for token 
        efficiency.

        The chain is constructed using LCEL (Langchain Expression Language).
        See more on https://python.langchain.com/docs/concepts/lcel/.

        Args:
            query: The query input by the user through chat_input element.
            response: The LLM response obtained from executing run_react_agent.

        Returns:
            Optional string of summary that's inferenced by summary model.

        """
        chain = self.prompt_template | self.llm

        raw_output = chain.invoke(
            input={
                "input": {
                    "question": query,
                    "answer": response
                }
            }
        )

        return str(raw_output.content)
