"""A module for database to manage LLM context."""

# standard
from typing import (
    List,
    Optional
)

# third-party
from sqlalchemy import (
    CursorResult,
    text,
    Engine
)

# internal
from cache import connect_database
from common import (
    show_project_statement,
    store_project_statement,
    show_manifest_statement,
    index_manifest_statement,
    store_manifest_statement,
)
from model import (
    Project,
    ProjectShow,
    Manifest,
    ManifestIndex,
    ManifestShow
)

class ContextManager:
    """A class that implements the database for context management."""
    
    def __init__(self) -> None:
        """Initialize the context manager instance."""
        self.connection: Engine = connect_database()

    def store_project(self, params: Project) -> None:
        """Store the newly created project model to database.

        Args:
            params: Project base model.

        """
        with self.connection.begin() as connection:
            connection.execute(
                statement=text(store_project_statement),
                parameters=params.model_dump()
            )

    def show_project(self, params: ProjectShow) -> Optional[Project]:
        """Show a project model from the given project_id.

        Args:
            params: ProjectShow base model.

        Returns:
            Optional project model if exists in database given the params args.

        """
        with self.connection.begin() as connection:
            result: CursorResult = connection.execute(
                statement=text(show_project_statement),
                parameters=params.model_dump()
            )

            mappings: List[Project] = [Project.model_validate(row) for row in result.mappings()]

            return mappings.pop() if mappings else None

    def store_manifest(self, params: Manifest) -> None:
        """Store the newly created manifest model to database.

        Args:
            params: Manifest base model.

        """
        with self.connection.begin() as connection:
            connection.execute(
                statement=text(store_manifest_statement),
                parameters=params.model_dump()
            )

    def index_manifest(self, params: ManifestIndex) -> List[Manifest]:
        """Index all manifests model from the given project_id and user_id.

        Args:
            params: ManifestIndex base model.

        Returns:
            List of manifest model that exists in database given the params args.

        """
        with self.connection.begin() as connection:
            result: CursorResult = connection.execute(
                statement=text(index_manifest_statement),
                parameters=params.model_dump()
            )

            return [Manifest.model_validate(row) for row in result.mappings()]

    def show_manifest(self, params: ManifestShow) -> Optional[Manifest]:
        """Show a manifest model from the given project_id, user_id, and manifest_no.

        Args:
            params: ManifestShow base model.

        Returns:
            Optional manifest model if sexist in database given the params args.

        """
        with self.connection.begin() as connection:
            result: CursorResult = connection.execute(
                statement=text(show_manifest_statement),
                parameters=params.model_dump()
            )

            mappings: List[Manifest] = [
                Manifest.model_validate(row)
                for row in result.mappings()
            ]

            return mappings.pop() if mappings else None
