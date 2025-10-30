"""A package to manage the behaviour of Streamlit app accross rerun.

Modules:
- **project**: Module to define the project model.
- **manifest**: Module to define the manifest model.
- **tool_args**: Module to define the tools arguments model.
"""

from .project import (
    ProjectCreate,
    ProjectShow,
    Project
)
from .manifest import (
    ManifestCreate,
    ManifestIndex,
    ManifestShow,
    Manifest
)
from .tool_args_specification import ExecutePythonArgsSchema

__all__ = [
    "ProjectCreate",
    "ProjectShow",
    "Project",
    "ManifestCreate",
    "ManifestIndex",
    "ManifestShow",
    "Manifest",
    "ExecutePythonArgsSchema"
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
