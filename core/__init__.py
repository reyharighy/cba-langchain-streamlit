"""A package to manage the behaviour of core functionalities within AI system.

Modules:
- **database_management**: Module to manage database management.
- **natural_language_orchestrator**: Module to manage natural language orchestrator.
- **user_application**: module to manage user application.
"""

from .database_management import DatabaseManagement
from .natural_language_orchestrator import NaturalLanguageOrchestrator
from .user_application import UserApplication

__all__ = [
    "DatabaseManagement",
    "NaturalLanguageOrchestrator",
    "UserApplication",
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
