"""A package to manage utility for other packages.

Modules:
- **decorator**: Module to provide convenience of using various Streamlit decorators.
- **prompt**: Not a module, but a place to store all prompt template used to contraint LLM response.
- **statements**: Not a module, but a place to store all statements used to query PostgreSQL.
"""

from .decorator import streamlit_status_container, streamlit_cache

from .prompt import AGENT_SYSTEM_PROMPT, CONTEXT_CHAIN_SYSTEM_PROMPT

from .statements import (
    STORE_PROJECT_STATEMENT,
    SHOW_PROJECT_STATEMENT,
    STORE_PROMPT_MANIFEST_STATEMENT,
    INDEX_PROMPT_MANIFEST_STATEMENT,
    SHOW_PROMPT_MANIFEST_STATEMENT
)

agent_chain_sys_prompt_template = AGENT_SYSTEM_PROMPT
context_chain_sys_prompt_template = CONTEXT_CHAIN_SYSTEM_PROMPT

store_project_statement = STORE_PROJECT_STATEMENT
show_project_statement = SHOW_PROJECT_STATEMENT
store_prompt_manifest_statement = STORE_PROMPT_MANIFEST_STATEMENT
index_prompt_manifest_statement = INDEX_PROMPT_MANIFEST_STATEMENT
show_prompt_manifest_statement = SHOW_PROMPT_MANIFEST_STATEMENT

__all__ = [
    "streamlit_status_container",
    "streamlit_cache",

    "agent_chain_sys_prompt_template",
    "context_chain_sys_prompt_template",

    "store_project_statement",
    "show_project_statement",
    "store_prompt_manifest_statement",
    "index_prompt_manifest_statement",
    "show_prompt_manifest_statement"
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
