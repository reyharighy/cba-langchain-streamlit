"""Entrypoint to the streamlit app."""

# standard
from typing import Dict, Literal
from uuid import UUID

# internal
from cache.dev import generate_uuid
from core import UserApplication

uuids: Dict[Literal["user_id", "project_id"], UUID] = generate_uuid()
user_app: UserApplication = UserApplication()
user_app.run(uuids)
