"""A module to define the prompt manifest model."""

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

class PromptManifestCreate(BaseModel):
    """Define the input attributes when creating a new prompt manifest model."""

    project_id: UUID
    user_id: UUID
    prompt_manifest_no: int
    prompt: str
    context: str

    def __call__(self) -> 'PromptManifest':
        """Define a callable to create a new prompt manifest model from class attributes."""
        return PromptManifest(
            project_id=self.project_id,
            user_id=self.user_id,
            prompt_manifest_no=self.prompt_manifest_no,
            prompt=self.prompt,
            context=self.context,
            manifest_file=f"manifest_{self.prompt_manifest_no}.py"
        )

class PromptManifestIndex(BaseModel):
    """Define the input to query all prompt manifests from given project_id and user_id."""

    project_id: UUID
    user_id: UUID

class PromptManifestShow(BaseModel):
    """Define the input attribute when fetching a prompt manifest model from database."""

    project_id: UUID
    user_id: UUID
    prompt_manifest_no: int

class PromptManifest(BaseModel):
    """Define the attributes of a prompt manifest model."""

    prompt_manifest_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    user_id: UUID
    prompt_manifest_no: int = Field(ge=1)
    prompt: str = Field(min_length=0)
    context: str = Field(min_length=0)
    manifest_file: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
