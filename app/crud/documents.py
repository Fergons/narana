from app.config import BooksConfig
from app.models.documents import Document
from app.utils import epub_to_documents, word_chunk
from dataclasses import dataclass


@dataclass
class DocumentsCRUD:
    def __init__(self, config: "BooksConfig") -> None:
        self.config = config

    def get_epub_paths(
        self, limit: int = 10, offset: int = 0, exclude_ids: list[str] = []
    ):
        epubs = list(self.config.dir.glob("*.epub"))[offset : offset + limit]
        return [epub for epub in epubs if epub.stem not in exclude_ids]

    def get_document_ids(
        self, limit: int = 10, offset: int = 0, exclude_ids: list[str] = []
    ):
        return [epub.stem for epub in self.get_epub_paths(limit, offset, exclude_ids)]

    def get_documents_from_epub(self, document_id) -> list[Document]:
        epub_path = self.config.dir / f"{document_id}.epub"
        extracted_text = epub_to_documents(epub_path)
        docs = []
        for i, doc in enumerate(extracted_text):
            chunks = list(
                word_chunk(doc, self.config.max_chunk_size, self.config.overlap)
            )
            docs.append(
                Document(
                    document_id=f"{document_id}_{i}",
                    parent_id=document_id,
                    title=None,
                    authors=None,
                    chunks=chunks,
                    max_chunk_size=self.config.max_chunk_size,
                )
            )

    def document_generator(
        self,
        limit: int = 10,
        offset: int = 0,
        exclude_ids: list[str] = [],
    ):
        epubs = self.get_epub_paths(limit, offset, exclude_ids)
        for epub in epubs:
            extracted_text = epub_to_documents(epub)
            for i, doc in enumerate(extracted_text):
                chunks = list(
                    word_chunk(doc, self.config.max_chunk_size, self.config.overlap)
                )
                # chunks = [chunk for chunk in chunks if chunk]
                if len(chunks) == 0:
                    continue

                yield Document(
                    document_id=f"{epub.stem}_{i}",
                    parent_id=epub.stem,
                    title=None,
                    authors=None,
                    chunks=chunks,
                    max_chunk_size=self.config.max_chunk_size,
                )

    def batch_generator(
        self,
        batch_size: int = 8,
        limit: int = 10,
        offset: int = 0,
        exclude_ids: list[str] = [],
    ):
        docs = []
        for doc in self.document_generator(limit, offset, exclude_ids):
            docs.append(doc)
            if len(docs) == batch_size:
                yield docs
                docs = []


    