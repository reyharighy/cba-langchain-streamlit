"""Entrypoint to the streamlit app."""

# standard
from uuid import UUID

# internal
from cache.dev import generate_uuid, set_project
from core import Session
from model import Project

project_id: UUID = generate_uuid()["project_id"]
project: Project = set_project(project_id)
session: Session = Session(project)
session.run()
