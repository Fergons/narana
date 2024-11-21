
from pydantic import (BaseModel, Field,
                      FileUrl, FilePath, HttpUrl, DirectoryPath, UUID4,
                      field_validator, 
                      ValidationError)


class Document(BaseModel):
    document_id: UUID4
    chunk_id: UUID4
    neighbors: list[UUID4]
    chunk_size: int
    text: str
    model: str

class DocumentExcerpt(BaseModel):
    excerpt_id: str
    chunk_id: str
    trope_id: str
    title_id: str
    text: str
