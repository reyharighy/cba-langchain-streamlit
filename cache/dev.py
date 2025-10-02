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
import streamlit as st
import nltk
from dotenv import load_dotenv

# internal
from database import (
    show_project,
    store_project,
)
from model import (
    Project,
    ProjectCreate,
    ProjectShow,
)

@st.cache_data(show_spinner="Setting up UUID...")
def generate_uuid() -> Dict[Literal["project_id", "user_id"], UUID]:
    """Generate UUID for user_id and project_id."""
    user_id = uuid4()
    project_id = uuid4()

    return {
        "project_id": project_id,
        "user_id": user_id
    }

@st.cache_data(show_spinner="Setting up project metadata...")
def set_project(project_id: UUID) -> Project:
    """Store project metadata to database if unset. Otherwise get the project metadata.

    This function always compute at initialization.
    Thus, we can start download stopwords, required when loading relevant contexts.

    Args:
        project_id: UUID of the project to handle within the session.

    Returns:
        Base model of the project.

    """
    # At a later stage, it maybe defined at the Laravel end.
    # Possibly use connection with MySQL database.
    load_dotenv()
    nltk.download("stopwords")

    project_show: ProjectShow = ProjectShow(project_id=project_id)
    project: Project | None = show_project(project_show)

    if project is None:
        project_create: ProjectCreate = ProjectCreate(
            project_id=project_id,
            user_id=generate_uuid()["user_id"],
            title="Example Project Title",
            datasets="dataset_2.csv"
        )

        new_project: Project = project_create()
        store_project(new_project)

        return new_project

    return project
