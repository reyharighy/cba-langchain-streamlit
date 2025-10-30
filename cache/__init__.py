"""A package to cache various data and resource result compurations.

Modules:
- **core**: Module to cache data and resource from core package.
- **dev**: Module to cache data and resource used during development.

The dev module is not publicly exposed.
Thus, the intention of using it must apply explicit import from the module.
"""

from .core import (
    connect_database,
    load_agent,
    load_agent_prompt_template,
    load_dataframe,
    load_df_info,
    load_llm,
    load_manifest,
    load_sentence_transformer,
    load_summary_prompt_template,
)
from .cold import cold_start

__all__ = [
    "cold_start",
    "connect_database",
    "load_agent",
    "load_agent_prompt_template",
    "load_dataframe",
    "load_df_info",
    "load_llm",
    "load_manifest",
    "load_sentence_transformer",
    "load_summary_prompt_template",
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
