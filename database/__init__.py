"""A package to manage database management.

Modules:
- **orm**: Module to manage the query-related tasks to database.
"""

from .orm import (
    store_project,
    show_project,
    store_prompt_manifest,
    index_prompt_manifest,
    show_prompt_manifest
)

__all__ = [
    "store_project",
    "show_project",
    "store_prompt_manifest",
    "index_prompt_manifest",
    "show_prompt_manifest"
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
