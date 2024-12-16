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
    document_id: UUID4 = Field(default=uuid4)
    parent_id: UUID4
    title: str | None
    text: str

class TokenizedDocument(Document):
    model: str
    tokens: list
    size: int



class DocumentTropeMatch(BaseModel):
    """
    Titles from literature tropes that can be sourced from libgen.
    """
    document_id: UUID4
    title_id: str
    title: str
    author: str | None
    download_url: HttpUrl


class Embedding(BaseModel):
    model: str
    document_id: UUID4
    embedding: list[float]


class Book(BaseModel):
    title_id: str = Field(..., alias="title_id")
    title: str
    author: str | None
    download_url: HttpUrl
    format: Literal["epub", "pdf", "txt"]

    model_config = ConfigDict(extra='ignore')


# class EpubBook(BaseModel):
#     title_id: str = Field(..., alias="title_id")
#     text: str
#     paragraph_spans: list[tuple[int, int]]
#     chapter_spans: dict[str, tuple[int, int]]
#     chapter_names: dict[str, str]

#     model_config = ConfigDict(extra='ignore')


