"""A package to manage the behaviour of Streamlit app accross rerun.

Modules:
- **chain**: Module to manage language models using Langchain framerowk and sentence transformer.
- **session**: Module to manage project's session within Streamlit application.
"""

from .chain import Chain

from .session import Session

__all__ = [
    "Session",
    "Chain"
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
