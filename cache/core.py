"""Module to cache data and resource from core package."""

# standard
import os
from importlib.abc import Loader
from importlib.util import (
    module_from_spec,
    spec_from_file_location,
)
from pathlib import Path
from types import ModuleType
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)

# third-party
import pandas as pd
import numpy as np
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from sentence_transformers import CrossEncoder
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# internal
from common import (
    streamlit_cache,
    agent_chain_sys_prompt_template,
    summary_chain_sys_prompt_template,
)

@streamlit_cache("Connecting to database", "resource")
def connect_database() -> Engine:
    """Establish a connection to PostgreSQL database.

    The connection pool is cached using the default Streamlit st.cache_resource decorator.
    """
    host = os.getenv("PGSQL_HOST", "host")
    user = os.getenv("POSTGRES_USER", "admin")
    pwd = os.getenv("POSTGRES_PASSWORD", "admin")
    port = os.getenv("PGSQL_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "db")

    db_url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"

    return create_engine(db_url)

@streamlit_cache("Loading dataframe", "data")
def load_dataframe(dataset_dir: str, dataset_file: str) -> pd.DataFrame:
    """Load dataframe from a certain CSV file path.

    The result is cached using the default Streamlit st.cache_data decorator.

    Args:
        dataset_dir: Directory of the CSV file.
        dataset_file: Name of the CSV file including its extension.

    Returns:
        Pandas dataframe object.

    """
    dataset_path = dataset_dir + dataset_file

    return pd.read_csv(
        filepath_or_buffer=dataset_path,
        skip_blank_lines=True
    )

@streamlit_cache("Loading manifest", "resource")
def load_manifest(
    manifest_dir: str,
    manifest_file: str
) -> Tuple[Optional[Loader], Optional[ModuleType]]:
    """Load the module of the manifest file to be executed.

    The result is cached using the default Streamlit st.cache_resource decorator.

    Args:
        manifest_dir: Directory of manifest file is located.
        manifest_file: Name of the manifest file including its extension.

    Returns:
        A tuple Loader and ModuleType if both exist.

    """
    manifest_path = manifest_dir + manifest_file
    path_obj: Path = Path(manifest_path)

    spec = spec_from_file_location(
        name=path_obj.stem,
        location=manifest_path
    )

    return (spec.loader, module_from_spec(spec)) if spec else (None, None)

@streamlit_cache("Providing dataset context", "data")
def load_df_info(dataset_dir: str, dataset_file: str) -> str:
    """Get dataset information used to provide additional context for LLM.

    The information includes column names and example values contained.
    The result will be embedded into the system prompt.
    The result is cached using the default Streamlit st.cache_data decorator.

    Args:
        dataset_dir: Directory of the CSV file.
        dataset_file: Name of the CSV file including its extension.

    Returns:
        Formatted string in a list of items for each column.

    """
    col_value_dict: Dict[str, np.ndarray] = {}
    output: str = ""

    df: pd.DataFrame = load_dataframe(
        dataset_dir=dataset_dir,
        dataset_file=dataset_file
    )

    for column in df.columns:
        col_value_dict[column] = df[column].unique()[:5]

    for col_name, values in col_value_dict.items():
        output += f"\t- {col_name}: {list(values)}\n"

    return output

@streamlit_cache("Loading transformer model", "data")
def load_transformer() -> CrossEncoder:
    """Load the sentence transformer model for filtering relevant chat history.

    This model reranks each chunk of historical contexts with the prompt.
    The result is cached using the default Streamlit st.cache_data decorator.

    Returns:
        Cross encoder model of ms-marco-MiniLM-L6-v2.

    """
    return CrossEncoder(model_name_or_path="cross-encoder/ms-marco-MiniLM-L6-v2")

@streamlit_cache("Loading LLM", "resource")
def load_llm(model: str) -> ChatGroq:
    """Load the LLM used for AI Agent as runnable.

    The result is cached using the default Streamlit st.cache_resource decorator.

    Args:
        model: Model specification to use.

    Returns:
        Groq LLM as runnable according to parameters set.

    """
    return ChatGroq(
        model=model,
        temperature=0,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None
    )

@streamlit_cache("Loading AI Agent prompt template", "data")
def load_agent_prompt_template() -> ChatPromptTemplate:
    """Load the prompt template instructions for AI Agent to follow.

    The result is cached using the default Streamlit st.cache_data decorator.

    Returns:
        ChatPromptTemplate as runnable with messages defined.

    """
    return ChatPromptTemplate.from_messages([
        ("system", agent_chain_sys_prompt_template),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

@streamlit_cache("Loading AI Agent", "resource")
def load_agent(
    llm: ChatGroq,
    _tools: List[StructuredTool],
    prompt_template: ChatPromptTemplate
) -> Runnable:
    """Load the AI Agent that has access to provided tools.

    The result is cached using the default Streamlit st.cache_resource decorator.

    Args:
        llm: Groq LLM as runnable according to parameters set.
        _tools: Tools that the llm has access to.
        prompt_template: ChatPromptTemplate as runnable with messages defined.

    Returns:
        Runnable sequence that constructs AI Agent chain.

    """
    return create_tool_calling_agent(
        llm=llm,
        tools=_tools,
        prompt=prompt_template
    )

@streamlit_cache("Loading context prompt template", "data")
def load_context_prompt_template() -> ChatPromptTemplate:
    """Load the prompt template instructions for context LLM to follow.

    The result is cached using the default Streamlit st.cache_data decorator.

    Returns:
        ChatPromptTemplate as runnable with messages defined.

    """
    return ChatPromptTemplate.from_messages([
        ("system", summary_chain_sys_prompt_template),
        ("human", "{input}"),
    ])
