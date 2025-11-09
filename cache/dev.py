"""Module for development or testing purpose.

This module not tied to any package.
Mainly for helping setting up the session.
"""

# standard
from typing import (
    Dict,
    Literal,
)
from uuid import (
    UUID,
    uuid4,
)

# third-party
from common import streamlit_cache

@streamlit_cache("Setting up UUID for development", "data")
def generate_uuid() -> Dict[Literal["user_id", "project_id"], UUID]:
    """Generate UUID for user and project.

    In deployment settings, this should come from external sources.
    UUID of user and project are required for saving the project metadata in databases.
    """
    return {
        "user_id": uuid4(),
        "project_id": uuid4()
    }
