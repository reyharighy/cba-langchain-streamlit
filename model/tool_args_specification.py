"""A module to define the tools arguments model."""

# third-party
from pydantic import (
    BaseModel,
    Field
)

class ExecutePythonCodeArgsSchema(BaseModel):
    """Arguments schema for execute_python_code tool that must be conformed by AI Agent."""

    code: str = Field(
        ...,
        title="code",
        description="Python code to run in a sandbox environment."
    )

class PineconeSearchArgsSchema(BaseModel):
    """Arguments schema for pinecone_search tool that must be conformed by AI Agent."""

    query: str = Field(
        ...,
        title="query",
        description="Query to use for searching information in a vector database."
    )

class TavilySearchArgsSchema(BaseModel):
    """Arguments schema for tavily_search tool that must be conformed by AI Agent."""

    query: str = Field(
        ...,
        title="query",
        description="Query to use for searching information on the internet."
    )
