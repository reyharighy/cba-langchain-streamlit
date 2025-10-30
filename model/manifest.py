"""A module to define the manifest model."""

# standard
from datetime import datetime
from uuid import (
    UUID,
    uuid4
)

# third-party
from pydantic import (
    BaseModel,
    Field
)

class ManifestCreate(BaseModel):
    """Define the input attributes when creating a new manifest model."""

    project_id: UUID
    user_id: UUID
    manifest_no: int
    prompt: str
    context: str

    def __call__(self) -> 'Manifest':
        """Define a callable to create a new manifest model from class attributes."""
        return Manifest(
            project_id=self.project_id,
            user_id=self.user_id,
            manifest_no=self.manifest_no,
            prompt=self.prompt,
            context=self.context,
            manifest_file=f"manifest_{self.manifest_no}.py"
        )

class ManifestIndex(BaseModel):
    """Define the input to query all manifests from given project_id and user_id."""

    project_id: UUID
    user_id: UUID

class ManifestShow(BaseModel):
    """Define the input attribute when fetching a manifest model from database."""

    project_id: UUID
    user_id: UUID
    manifest_no: int

class Manifest(BaseModel):
    """Define the attributes of a manifest model."""

    manifest_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    user_id: UUID
    manifest_no: int = Field(ge=1)
    prompt: str = Field(min_length=0)
    context: str = Field(min_length=0)
    manifest_file: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
