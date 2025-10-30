"""A package to manage the behaviour of core functionalities within AI system.

Modules:
- **context_manager**: Module for database to manage LLM context.
- **natural_language_orchestration**: Module to manage natural language orchestrator.
- **user_application**: module to manage user application.
"""

from .context_management import ContextManager
from .natural_language_orchestration import NaturalLanguageOrchestrator
from .user_application import Application

__all__ = [
    "ContextManager",
    "NaturalLanguageOrchestrator",
    "Application",
]

def __getattr__(name: str):
    if name.startswith("_"):
        raise AttributeError(f"{name} is private to mypackage")
    raise AttributeError(f"mypackage has no attribute {name}")
