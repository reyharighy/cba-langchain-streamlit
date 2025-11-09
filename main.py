"""Entrypoint to the Streamlit application."""

# standard
from typing import Dict, Literal
from uuid import UUID

# internal
from cache.dev import generate_uuid
from cache import cold_start
from core import Application

if __name__ == "__main__":
    # Inbound data related to user information, still in dev process
    uuids: Dict[Literal["user_id", "project_id"], UUID] = generate_uuid()

    cold_start()
    app: Application = Application()
    app.run(uuids)
