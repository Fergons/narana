from litellm import aembedding
from app.models.documents import Document, EmbeddedDocument
from app.models.tvtropes import TropeExample
from typing import Sequence
from sentence_transformers import SentenceTransformer



    
async def async_embed_document(embed_func, doc: Document) -> EmbeddedDocument:
    model, embeddings = await embed_func(doc.chunks)
    return EmbeddedDocument(document_id=doc.document_id, model=model, chunk_embeddings=embeddings)


async def async_embed_tvtropes_examples(embed_func, trope_examples: Sequence[TropeExample]) -> list[EmbeddedDocument]:
    model, embeddings = await embed_func([example.example for example in trope_examples])
    return [EmbeddedDocument(document_id=f'{example.title_id}_{example.trope_id}', model=model, chunk_embeddings=[embedding]) for example, embedding in zip(trope_examples, embeddings)]


async def async_api_embed(model: str, input: Sequence[str], dimensions: int=1024, **kwargs) -> tuple[str, list[list[float]]]:
    """
    Parameters:
    - model: The embedding model to use.
    - input: The input for which embeddings are to be generated.
    - encoding_format: Optional[str] The format to return the embeddings in. Can be either `float` or `base64`
    - dimensions: The number of dimensions the resulting output embeddings should have. Only supported in text-embedding-3 and later models.
    - timeout: The timeout value for the API call, default 10 mins
    - litellm_call_id: The call ID for litellm logging.
    - litellm_logging_obj: The litellm logging object.
    - logger_fn: The logger function.
    - api_base: Optional. The base URL for the API.
    - api_version: Optional. The version of the API.
    - api_key: Optional. The API key to use.
    - api_type: Optional. The type of the API.
    - caching: A boolean indicating whether to enable caching.
    - custom_llm_provider: The custom llm provider.
    """
    response = await aembedding(
        model=model,
        input=input,
        **kwargs
    )

    assert len(response.data) == len(input), f"Expected {len(input)} embeddings, got {len(response.data)}"
    # sort response embeddings to input order by data "index" key
    embeddings = sorted(response.data, key=lambda x: x["index"])
    return model, [embedding["embedding"] for embedding in embeddings]


def transformer_embed_batch(model: SentenceTransformer, input: Sequence[str], **kwargs) -> list[list]:
    """Input is a list of strings that are going to be tokenized, truncated and embedded."""










    

