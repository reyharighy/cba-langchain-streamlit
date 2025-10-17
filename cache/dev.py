"""Module to cache data and resource used during development.

This module not tied to any package.
Mainly for setting up the session in main.py as Streamlit entrypoint.
"""

# standard
import nltk
from dotenv import load_dotenv
from typing import (
    Dict,
    Literal,
)
from uuid import (
    UUID,
    uuid4,
)

# third-party
import streamlit as st

@st.cache_data(show_spinner="Setting up UUID...")
def generate_uuid() -> Dict[Literal["project_id", "user_id"], UUID]:
    """Generate UUID for user_id and project_id."""
    load_dotenv()
    nltk.download("stopwords")
    user_id = uuid4()
    project_id = uuid4()

    return {
        "project_id": project_id,
        "user_id": user_id
    }
