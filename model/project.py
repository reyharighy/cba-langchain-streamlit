"""A module to define the project model."""

# standard
from uuid import UUID
from datetime import datetime

# third-party
from pydantic import (
    BaseModel,
    Field
)

class ProjectCreate(BaseModel):
    """Define the input attributes when creating a new project model."""

    project_id: UUID
    user_id: UUID
    title: str = Field(min_length=1, max_length=255)
    datasets: str = Field(min_length=1)

    def __call__(self) -> 'Project':
        """Define a callable to create a new project model from class attributes."""
        return Project(
            project_id=self.project_id,
            user_id=self.user_id,
            title=self.title,
            dataset_dir="outbound/datasets/",
            dataset_file=self.datasets,
            manifest_dir="manifests/"
        )

class ProjectShow(BaseModel):
    """Define the input attribute when fetching a project model from database."""

    project_id: UUID

class Project(BaseModel):
    """Define the attributes of a project model."""

    project_id: UUID
    user_id: UUID
    title: str = Field(min_length=1, max_length=255)
    dataset_dir: str
    dataset_file: str = Field(min_length=1)
    manifest_dir: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
