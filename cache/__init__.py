"""A package to cache data and resources within system that would take time to compute.

Modules:
- **cold**: Module to set up all data and resources to cold start the application.
- **core**: Module to cache data and resource that will be used directly inside the core package.
- **dev**: Module for development or testing purpose.

The dev module is not publicly exposed. Thus, the intention of using it must apply explicit import 
from the module.
"""

from .core import (
    connect_database,
    load_agent,
    load_cross_encoder,
    load_dataframe,
    load_df_info,
    load_llm,
    load_manifest,
    load_react_prompt_template,
    load_search_engine,
    load_summary_prompt_template,
    load_translator,
    load_vector_database,
)
from .cold import cold_start

__all__ = [
    "cold_start",
    "connect_database",
    "load_agent",
    "load_cross_encoder",
    "load_dataframe",
    "load_df_info",
    "load_llm",
    "load_manifest",
    "load_react_prompt_template",
    "load_search_engine",
    "load_summary_prompt_template",
    "load_translator",
    "load_vector_database",
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
