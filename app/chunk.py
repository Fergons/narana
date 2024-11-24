from transformers import AutoTokenizer
from app.models.documents import Document, TokenizedDocument
from typing import Generator
from uuid import uuid4


def chunk_text(*, tokenizer: AutoTokenizer, text: str, chunk_size: int, overlap: int) -> list[list[int]]:
    input_ids = tokenizer(text, add_special_tokens=False)['input_ids'][0]
    return [input_ids[i:i+chunk_size] for i in range(0, len(input_ids), chunk_size-overlap)]


def chunk_document_by_model_to_documents(*, model: str = 'BAAI/bge-m3', document: Document, chunk_size: int, overlap: int) -> Generator[Document]:
    tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    for chunk in chunk_text(tokenizer=tokenizer, text=document.text, chunk_size=chunk_size, overlap=overlap):
        yield Document(parent_id=document.document_id, title=document.title, text=tokenizer.decode(chunk))



def chunk_document_by_model_to_tokenized_documents(*, model: str = 'BAAI/bge-m3', document: Document, chunk_size: int, overlap: int) -> Generator[TokenizedDocument]:
    tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    for chunk in chunk_text(tokenizer=tokenizer, text=document.text, chunk_size=chunk_size, overlap=overlap):
        yield TokenizedDocument(parent_id=document.document_id, title=document.title, text=tokenizer.decode(chunk), tokens=chunk, model=model, size=len(chunk))