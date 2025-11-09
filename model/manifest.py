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
    num: int
    query: str
    response: str
    context: str

    def __call__(self) -> 'Manifest':
        """Define a callable to create a new manifest model from class attributes."""
        return Manifest(
            project_id=self.project_id,
            user_id=self.user_id,
            num=self.num,
            query=self.query,
            response=self.response,
            context=self.context,
            file_name=f"manifest_{self.num}.py"
        )

class ManifestIndex(BaseModel):
    """Define the input to query all manifests from given project_id and user_id."""

    project_id: UUID
    user_id: UUID

class ManifestShow(BaseModel):
    """Define the input attribute when fetching a manifest model from database."""

    project_id: UUID
    user_id: UUID
    num: int

class Manifest(BaseModel):
    """Define the attributes of a manifest model."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    user_id: UUID
    num: int = Field(ge=1)
    query: str = Field(min_length=0)
    response: str = Field(min_length=0)
    context: str = Field(min_length=0)
    file_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
