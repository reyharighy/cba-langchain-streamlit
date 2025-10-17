"""A module to manage database management."""

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
    show_prompt_manifest_statement,
    index_prompt_manifest_statement,
    store_prompt_manifest_statement,
)
from model import (
    Project,
    ProjectShow,
    PromptManifest,
    PromptManifestIndex,
    PromptManifestShow
)

class DatabaseManagement:
    """A class that implements the database management."""
    
    def __init__(self) -> None:
        """Initialize the database management instance."""
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

    def store_prompt_manifest(self, params: PromptManifest) -> None:
        """Store the newly created prompt manifest model to database.

        Args:
            params: PromptManifest base model.

        """
        with self.connection.begin() as connection:
            connection.execute(
                statement=text(store_prompt_manifest_statement),
                parameters=params.model_dump()
            )

    def index_prompt_manifest(self, params: PromptManifestIndex) -> List[PromptManifest]:
        """Index all prompt manifests model from the given project_id and user_id.

        Args:
            params: PromptManifestIndex base model.

        Returns:
            List of prompt manifest model that exists in database given the params args.

        """
        with self.connection.begin() as connection:
            result: CursorResult = connection.execute(
                statement=text(index_prompt_manifest_statement),
                parameters=params.model_dump()
            )

            return [PromptManifest.model_validate(row) for row in result.mappings()]

    def show_prompt_manifest(self, params: PromptManifestShow) -> Optional[PromptManifest]:
        """Show a prompt manifest model from the given project_id, user_id, and prompt_manifest_no.

        Args:
            params: PromptManifestShow base model.

        Returns:
            Optional prompt manifest model if sexist in database given the params args.

        """
        with self.connection.begin() as connection:
            result: CursorResult = connection.execute(
                statement=text(show_prompt_manifest_statement),
                parameters=params.model_dump()
            )

            mappings: List[PromptManifest] = [
                PromptManifest.model_validate(row)
                for row in result.mappings()
            ]

            return mappings.pop() if mappings else None
