"""A module to define the tools arguments model."""

# third-party
from pydantic import (
    BaseModel,
    Field
)

class ExecutePythonArgs(BaseModel):
    """Arguments schema for execute_python tool that must be conformed by AI Agent."""

    code: str = Field(..., description="Python code to run in order to answer the user's query.")
