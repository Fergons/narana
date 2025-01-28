from pydantic import (
    BaseModel,
    Field,
    FileUrl,
    FilePath,
    HttpUrl,
    DirectoryPath,
    UUID4,
    field_validator,
    ValidationError,
    ConfigDict
)
from typing import Literal
from uuid import uuid4


class Document(BaseModel):
    document_id: str = Field(default=uuid4)
    parent_id: str | None
    title: str | None
    authors: list[str] | None
    chunks: list[str]
    max_chunk_size: int


class DocumentTropeMatch(BaseModel):
    """
    Titles from literature tropes that can be sourced from libgen.
    """
    document_id: str
    title_id: str
    title: str
    author: str | None
    download_url: HttpUrl


class EmbeddedDocument(BaseModel):
    document_id: str
    model: str
    chunk_embeddings: list[float]
