"""Module to cache data and resource used during development.

This module not tied to any package.
Mainly for setting up the session in main.py as Streamlit entrypoint.
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
    """Generate UUID for user_id and project_id."""
    return {
        "user_id": uuid4(),
        "project_id": uuid4()
    }
