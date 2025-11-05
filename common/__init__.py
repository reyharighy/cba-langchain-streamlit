"""A package to manage small helper modules for core system.

Modules:
- **custom_decorators**: Module to provide convenience of using various Streamlit decorators.
- **orm_statements**: Not a module, but a place to store all statements used to query PostgreSQL.
- **prompt_templates**: Not a module, but a place to store all prompt templates for LLM guidance.
"""

from .custom_decorators import streamlit_status_container, streamlit_cache
from .orm_statements import (
    STORE_PROJECT_STATEMENT,
    SHOW_PROJECT_STATEMENT,
    STORE_MANIFEST_STATEMENT,
    INDEX_MANIFEST_STATEMENT,
    SHOW_MANIFEST_STATEMENT
)
from .prompt_templates import (
    REACT_SYSTEM_PROMPT, 
    SUMMARY_SYSTEM_PROMPT,
    EXECUTE_PYTHON_CODE_TOOL_DESCRIPTION,
    PINECONE_SEARCH_TOOL_DESCRIPTION,
    TAVILY_SEARCH_TOOL_DESCRIPTION,
)

react_sys_prompt_template = REACT_SYSTEM_PROMPT
summary_sys_prompt_template = SUMMARY_SYSTEM_PROMPT
execute_python_code_tool_description = EXECUTE_PYTHON_CODE_TOOL_DESCRIPTION
pinecone_search_tool_description = PINECONE_SEARCH_TOOL_DESCRIPTION
tavily_search_tool_description = TAVILY_SEARCH_TOOL_DESCRIPTION

store_project_statement = STORE_PROJECT_STATEMENT
show_project_statement = SHOW_PROJECT_STATEMENT
store_manifest_statement = STORE_MANIFEST_STATEMENT
index_manifest_statement = INDEX_MANIFEST_STATEMENT
show_manifest_statement = SHOW_MANIFEST_STATEMENT

__all__ = [
    "streamlit_status_container",
    "streamlit_cache",
    "react_sys_prompt_template",
    "summary_sys_prompt_template",
    "execute_python_code_tool_description",
    "pinecone_search_tool_description",
    "tavily_search_tool_description",
    "store_project_statement",
    "show_project_statement",
    "store_manifest_statement",
    "index_manifest_statement",
    "show_manifest_statement"
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
