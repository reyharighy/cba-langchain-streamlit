"""A package to manage the behaviour of Streamlit app accross rerun.

Modules:
- **project**: Module to define the project model.
- **prompt_manifest**: Module to define the prompt manifest model.
- **tool_args**: Module to define the tools arguments model.
"""

from .project import (
    ProjectCreate,
    ProjectShow,
    Project
)
from .prompt_manifest import (
    PromptManifestCreate,
    PromptManifestIndex,
    PromptManifestShow,
    PromptManifest
)
from .tool_args_specification import ExecutePythonArgsSchema

__all__ = [
    "ProjectCreate",
    "ProjectShow",
    "Project",
    "PromptManifestCreate",
    "PromptManifestIndex",
    "PromptManifestShow",
    "PromptManifest",
    "ExecutePythonArgsSchema"
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
