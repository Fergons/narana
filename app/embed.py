from litellm import aembedding
from app.models.documents import Document, EmbeddedDocument
from app.models.tvtropes import TropeExample
from typing import Sequence


async def async_embed_document(embed_func, doc: Document) -> EmbeddedDocument:
    model, embeddings = await embed_func(doc.chunks)
    return EmbeddedDocument(
        document_id=doc.document_id, model=model, chunk_embeddings=embeddings
    )


async def async_embed_tvtropes_examples(
    embed_func, trope_examples: Sequence[TropeExample]
) -> list[EmbeddedDocument]:
    model, embeddings = await embed_func(
        [example.example for example in trope_examples]
    )
    return [
        EmbeddedDocument(
            document_id=f"{example.title_id}_{example.trope_id}",
            model=model,
            chunk_embeddings=[embedding],
        )
        for example, embedding in zip(trope_examples, embeddings)
    ]


async def async_api_embed(
    model: str, input: Sequence[str], dimensions: int = 1024, **kwargs
) -> tuple[str, list[list[float]]]:
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
    response = await aembedding(model=model, input=input, **kwargs)

    assert len(response.data) == len(
        input
    ), f"Expected {len(input)} embeddings, got {len(response.data)}"
    # sort response embeddings to input order by data "index" key
    embeddings = sorted(response.data, key=lambda x: x["index"])
    return model, [embedding["embedding"] for embedding in embeddings]


# M3ModelOutputType = dict[
#     Literal["dense_vecs", "lexical_weights", "colbert_vecs"],
#     np.ndarray | List[dict[str, float]] | List[np.ndarray],
# ]


# class M3Embedder:
#     """
#     This is a AdalFlow wrapper for BGEM3FlagModel providing ModelClient interface.
#     """

#     def __init__(
#         self,
#         model_name: str = "BAAI/bge-m3",
#         max_length: int = 2048,
#         **kwargs,
#     ):
#         self.model_name = model_name
#         self.max_length = max_length

#     def init_model(self, model_name: str = None, **kwargs):
#         try:
#             from FlagEmbedding import BGEM3FlagModel

#             self.model = BGEM3FlagModel(
#                 model_name if model_name is None else self.model_name,
#                 normalize_embeddings=True,
#                 use_fp16=True,
#                 query_max_length=self.max_length,
#                 passage_max_length=self.max_length,
#                 **kwargs,
#             )
#             log.info(f"Done loading model {model_name}")

#         except Exception as e:
#             log.error(f"Error loading model {model_name}: {e}")
#             raise e

#     @staticmethod
#     def _embedding_type_to_dict_key(embedding_type: str) -> str:
#         match embedding_type:
#             case "dense":
#                 return "dense_vecs"
#             case "colbert":
#                 return "colbert_vecs"
#             case "lexical":
#                 return "lexical_weights"
#             case _:
#                 raise ValueError(f"Unknown embeddings type: {embedding_type}")

#     @staticmethod
#     def _embedding_type_to_param(self, embedding_type: str) -> str:
#         default = {"return_dense": False, "return_colbert_vecs": False, "return_sparse": False}
#         match embedding_type:
#             case "dense":
#                  default["return_dense"] = True
#                  return default
#             case "colbert":
#                  default["return_colbert_vecs"] = True
#                  return default
#             case "lexical":
#                  default["return_sparse"] = True
#                  return default
#             case _:
#                 raise ValueError(f"Unknown embeddings type: {embedding_type}")

#     def __call__(self, **kwargs) -> M3ModelOutputType:
#         input = kwargs.pop("input")
#         embedding_type = kwargs.pop("embedding_type", "dense")
#         kwargs.update(self._embedding_type_to_param(self, embedding_type))
#         return self.model.encode(sentences=input, **kwargs)[
#             self._embedding_type_to_dict_key(embedding_type)
#         ]


# class FlagClient(ModelClient):
#     support_models = {
#         "BAAI/bge-m3": {
#             "type": ModelType.EMBEDDER,
#         }
#     }

#     def __init__(self, model_name: str = "BAAI/bge-m3"):
#         super().__init__()
#         self._model_name = model_name
#         self.sync_client = None
#         self.async_client = None

#     def init_sync_client(self):
#         return M3Embedder()

#     def parse_embedding_response(self, response):
#         return EmbedderOutput(data=[Embedding(vec.tolist(), i) for i, vec in enumerate(response)], model=self._model_name)

#     def convert_inputs_to_api_kwargs(
#         self, input=None, model_kwargs=..., model_type=ModelType.UNDEFINED
#     ):
#         match model_type:
#             case ModelType.EMBEDDER:
#                 if input is None:
#                     raise ValueError("input is required for embedding")

#                 return {
#                     "input": input,
#                     "max_length": model_kwargs.get("max_length", 2048),
#                     "batch_size": model_kwargs.get("batch_size", 100),
#                     "embedding_type": model_kwargs.get("embedding_type", "dense")
#                 }
#             case _:
#                 raise ValueError(
#                     f"Not supported model type: {model_type} for client {type(self).__name__}"
#                 )

#     def call(self, api_kwargs: dict = {}, model_type: ModelType = ModelType.UNDEFINED):
#         if self.sync_client is None and model_type == ModelType.EMBEDDER:
#             self.sync_client = self.init_sync_client()
#         return self.sync_client(**api_kwargs)