from litellm import aembedding
from app.models.documents import Document, Embedding
from typing import Literal, Sequence

EMBEDDING_TYPES = Literal['cls', 'late_chunking', 'colbert', 'sparse', 'blackbox']
OLLAMA_EMBEDDING_MODELS = Literal['bge-m3', 'nomic-embed-text']
OPENAI_EMBEDDING_MODELS = Literal['text-embedding-ada-002']



async def async_embed_documents(model: str, docs: Sequence[Document]) -> list[Embedding]:
    response = await aembedding(
        model=model,
        docs=[doc.text for doc in docs],
    )
    return [Embedding(document_id=doc.document_id, embedding=embedding.data, model=model) for doc, embedding in zip(docs, response)]


    