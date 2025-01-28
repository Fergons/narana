from dataclasses import dataclass
import logging
from typing import List, Literal, Optional, Any, Union

import numpy as np

from vespa.application import Vespa
from vespa.io import VespaQueryResponse
from vespa.exceptions import VespaError

from adalflow.core.retriever import Retriever
from adalflow.core.types import (
    RetrieverOutput,
    RetrieverStrQueryType,
    RetrieverStrQueriesType,
    Document,
    EmbedderOutputType,
    EmbedderInputType,
    Embedding,
    EmbedderOutput,
    ModelType,
)

log = logging.getLogger(__name__)


class VespaRetriever(Retriever[Any, RetrieverStrQueryType]):
    """
    A Vespa-based retriever that can handle:
      - BM25 textual queries
      - Dense vector queries
      - ColBERT multi-vector queries

    Depending on the rank_profile passed at initialization.
    """

    def __init__(
        self,
        embedder: Any = None,
        top_k: int = 3,
        vespa_url: str = "http://localhost:8080",
        vespa_port: int = 8080,
        schema: str = "*",
        rank_profile: str = "dense",
    ):
        """
        Args:
            embedder (Embedder, optional): Optional embedder to generate query vectors.
            top_k (int, optional): How many hits to retrieve from Vespa. Defaults to 3.
            vespa_url (str, optional): URL of your Vespa endpoint.
            vespa_port (int, optional): Port of your Vespa endpoint.
            schema (str, optional): Vespa schema name to query.
            rank_profile (str, optional): "bm25", "dense" or "colbert"
        """
        super().__init__()
        self.embedder = embedder
        self.top_k = top_k
        self.vespa_url = vespa_url
        self.vespa_port = vespa_port
        self.rank_profile = rank_profile
        self.schema = schema

        # Create a Vespa object, used via context manager in the query methods:
        self.app = Vespa(url=self.vespa_url, port=self.vespa_port)

    def call(
        self,
        input: RetrieverStrQueriesType,
        top_k: Optional[int] = None,
        **kwargs,
    ) -> List[RetrieverOutput]:
        """
        Handle single or batch queries, using the rank_profile to either utilize a text-based or vector-based method.
        """
        top_k = top_k or self.top_k
        queries = input if isinstance(input, list) else [input]
        query_embeddings = None
        if self.embedder is not None:
            query_embeddings = self.embedder(queries, embedding_type=self.rank_profile, **kwargs)

        # If you have an embedder, embed all queries up-front (used in "dense"/"colbert" retrievals)

        outputs: List[RetrieverOutput] = []
        for i, query_text in enumerate(queries):
            # Switch based on your rank_profile
            if self.rank_profile.lower() == "bm25":
                response = self._query_text(query_text=query_text, top_k=top_k)
            elif self.rank_profile.lower() == "dense":
                # If user already passed in a dense vector, or embedder is used:
                # If you want to read from "kwargs", you could do:
                # dense_vector = kwargs.get("dense_rep") or ...
                # otherwise we rely on `query_embeddings.data[i]`.
                if query_embeddings is None:
                    raise ValueError(
                        "No embedder found for 'dense' rank profile. Provide an embedder or pass precomputed vectors."
                    )
                dense_vector = query_embeddings.data[i].embedding
                response = self._query_dense(query_text, dense_vector, top_k=top_k)

            elif self.rank_profile.lower() == "colbert":
                # ColBERT is multi-vector. We assume embedder returns a shape [#tokens, 1024]
                # plus we need query length for normalization.
                # Adjust according to how your embedder returns multi-vector outputs.
                if query_embeddings is None:
                    raise ValueError(
                        "No embedder found for 'colbert' rank profile. "
                        "Provide an embedder that returns multi-vector embeddings or pass them explicitly."
                    )
                colbert_tensor = query_embeddings.data[i].embedding  # shape [qt, 1024]
                query_len = float(colbert_tensor.shape[0])  # number of tokens
                response = self._query_colbert(colbert_tensor, query_len, top_k=top_k)
            else:
                raise ValueError(f"Unsupported rank profile: {self.rank_profile}")

            # Build output
            outputs.append(self._build_retriever_output(query_text, response))

        return outputs

    def _build_retriever_output(
        self, query_text: str, response: Optional[VespaQueryResponse]
    ) -> RetrieverOutput:
        """
        Convert Vespa query response into `RetrieverOutput`.
        """
        if response is None or not response.is_successful():
            log.warning(f"Query failed or response is None: {query_text}")
            return RetrieverOutput(
                doc_indices=[],
                doc_scores=[],
                query=query_text,
                documents=[],
            )

        hits = (
            response.hits
        )  # each entry is a dict with "id", "relevance", "fields", ...
        doc_indices = [hit["id"] for hit in hits]
        doc_scores = [hit["relevance"] for hit in hits]
        documents = self._format_docs(hits)
        return RetrieverOutput(
            doc_indices=doc_indices,
            doc_scores=doc_scores,
            query=query_text,
            documents=documents,
        )

    def _format_docs(self, hits: List[dict]) -> List[Document]:
        """
        Convert raw Vespa hits to adalflow Document objects.
        """
        docs: List[Document] = []
        for hit in hits:
            # The entire record is in hit["fields"] - parse as needed.
            doc_dict = {
                "id": hit["id"],  # or a unique doc field
                "metadata": hit["fields"],  # store everything in metadata
            }
            print(doc_dict)
            docs.append(Document.from_dict(doc_dict))
        return docs

    def _query_text(self, query_text: str, top_k: int) -> Optional[VespaQueryResponse]:
        """
        BM25 or textual retrieval, using userQuery().
        Example:
           select * from <schema> * where userQuery();
        """
        # yql = f"select * from {self.schema} * where userQuery()"
        yql = f"select * from sources {self.schema} where userQuery()"
        try:
            with self.app.syncio() as session:
                response = session.query(
                    yql=yql,
                    query=query_text,
                    hits=top_k,
                    ranking=self.rank_profile,
                )
            return response
        except VespaError as e:
            log.error(f"BM25 query failed: {str(e)}")
            return None

    def _query_dense(
        self, query: str, dense_vector: Union[np.ndarray, list], top_k: int = None
    ) -> Optional[VespaQueryResponse]:
        """
         Vector-based query using 'dense' rank_profile.
         Vespa schema:
            inputs=[("query(q_dense)", "tensor<bfloat16>(x[1024])")]
            first_phase="closeness(dense_rep)"
        "input.query(q_dense)" in the request body.
        """
        body = {
            "yql": f"select * from sources {self.schema} where  {{targetHits: {top_k}}} nearestNeighbor(dense_rep, q_dense)",
            "query": query,
            "ranking": "dense",  # "dense"
            "input.query(q_dense)": self._to_vespa_tensor_string(dense_vector),
        }

        try:
            with self.app.syncio() as session:
                response = session.query(
                    hits=top_k if top_k else self.top_k,
                    body=body,
                )
            return response
        except VespaError as e:
            log.error(f"Dense query failed: {str(e)}")
            return None

    def _query_colbert(
        self,
        query: str,
        colbert_tensor: Union[np.ndarray, list],
        query_len: float,
        top_k: int,
        timeout: int = None,
    ) -> Optional[VespaQueryResponse]:
        """
        Vector-based query using 'colbert' rank_profile.
        Vespa schema:
          inputs=[
            ("query(q_colbert)", "tensor<bfloat16>(qt{}, x[1024])"),
            ("query(q_len_colbert)", "int"),
          ]
          first_phase="max_sim"
        Pass "input.query(q_colbert)" with shape [qt, 1024], and
        "query(q_len_colbert)" with the number of tokens for normalization.
        """
        body = {
            "yql": f"select * from sources {self.schema} where true",
            "query": query,
            "ranking": "colbert",  # "colbert"
            "input.query(q_colbert)": self._to_vespa_colbert_tensor(colbert_tensor),
            "input.query(q_len_colbert)": query_len,
        }

        try:
            with self.app.syncio() as session:
                response = session.query(hits=top_k, body=body, timeout=timeout)
            return response
        except VespaError as e:
            log.error(f"ColBERT query failed: {str(e)}")
            return None

    def _query_hybrid(
        self,
        query: str,
        dense_vector: Union[np.ndarray, list],
        colbert_tensor: Union[np.ndarray, list],
        query_len: float,
        top_k: int,
        timeout: int = None,
    ) -> Optional[VespaQueryResponse]:
        """
        Vector-based query using 'hybrid' rank_profile.
        Vespa schema:
          inputs=[
            ("query(q_dense)", "tensor<bfloat16>(x[1024])"),
            ("query(q_colbert)", "tensor<bfloat16>(qt{}, x[1024])"),
            ("query(q_len_colbert)", "int"),
          ]
          first_phase="max_sim"
        Pass "input.query(q_dense)" with shape [1024], and
        "input.query(q_colbert)" with shape [qt, 1024], and
        "query(q_len_colbert)" with the number of tokens for normalization.
        """
        body = {
            "yql": f"select * from sources {self.schema} where {{targetHits: {top_k}}}nearestNeighbor(dense_rep, q_dense)",
            "query": query,
            "ranking": "hybrid",  # "hybrid"
            "input.query(q_dense)": self._to_vespa_tensor_string(dense_vector),
            "input.query(q_colbert)": self._to_vespa_colbert_tensor(colbert_tensor),
            "input.query(q_len_colbert)": query_len,
        }

        try:
            with self.app.syncio() as session:
                response = session.query(hits=top_k, body=body, timeout=timeout)
            return response
        except VespaError as e:
            log.error(f"Hybrid query failed: {str(e)}")
            return None

    def _to_vespa_tensor_string(self, vector: Union[np.ndarray, list]) -> str:
        """
        Convert a 1D vector (e.g. shape [1024]) to a Vespa JSON tensor string.
        """
        if isinstance(vector, list):
            return vector

        # vector.shape = (1024,)
        return vector.tolist()

    def _to_vespa_colbert_tensor(self, colbert_tensor: Union[np.ndarray, list]) -> str:
        """
        Convert a 2D colBERT tensor shape [qt, 1024] to Vespa's JSON tensor format:
        tensor<bfloat16>(qt{}, x[1024]).

        Example:
            {
              "blocks": [
                {"address": {"qt": 0}, "values": [0.1, 0.2 ...]},
                {"address": {"qt": 1}, "values": [0.3, 0.4 ...]},
                {"address": {"qt": 2, "values": [0.5, 0.6 ...]},
                ...
              ]
            }
        """
        # convert to np array if it's a python list
        if isinstance(colbert_tensor, list):
            colbert_tensor = np.array(colbert_tensor, dtype=np.float16)

        # colbert_tensor.shape = (qt, 1024)
        qt_size, _ = colbert_tensor.shape

        blocks = []
        for i_qt in range(qt_size):
            blocks.append(
                {"address": {"qt": i_qt}, "values": colbert_tensor[i_qt].tolist()}
            )

        return {"blocks": blocks}


class M3Embdder:
    _model_name = "BAAI/bge-m3"
    def __init__(self, max_length=512, batch_size=64):
        self.model = None        
        self.max_length = max_length

    def init_model(self):
        from FlagEmbedding import BGEM3FlagModel

        self.model = BGEM3FlagModel(
            "BAAI/bge-m3",
            normalize_embeddings=True,
            max_length=self.max_length,
            use_fp16=True,
            batch_size=64,
        )

    @staticmethod
    def _embedding_type_to_dict_key(embedding_type: str) -> str:
        match embedding_type:
            case "dense":
                return "dense_vecs"
            case "colbert":
                return "colbert_vecs"
            case "lexical":
                return "lexical_weights"
            case _:
                raise ValueError(f"Unknown embeddings type: {embedding_type}")

    @staticmethod
    def _embedding_type_to_param(embedding_type: str) -> str:
        default = {
            "return_dense": False,
            "return_colbert_vecs": False,
            "return_sparse": False,
        }
        match embedding_type:
            case "dense":
                default["return_dense"] = True
                return default
            case "colbert":
                default["return_colbert_vecs"] = True
                return default
            case "lexical":
                default["return_sparse"] = True
                return default
            case "dense+colbert":
                default["return_dense"] = True
                default["return_colbert_vecs"] = True
                return default
            case _:
                raise ValueError(f"Unknown embeddings type: {embedding_type}")

    def __call__(self, input, embedding_type: str = "dense", **kwds):
        if self.model is None:
            self.init_model()
        
        return self.parse_embedding_response(self.model.encode(input, **self._embedding_type_to_param(embedding_type))[self._embedding_type_to_dict_key(embedding_type)])

    def parse_embedding_response(self, response):
        return EmbedderOutput(data=[Embedding(vec.tolist(), i) for i, vec in enumerate(response)], model=self._model_name)

if __name__ == "__main__":
    from app.config import settings

    queries = [
        "The quick brown fox jumps over the lazy dog",
        "Who is Hercuile Poirot?",
        "Heroes never die.",
    ]

    embedder = M3Embdder(max_length=2048, batch_size=64)

    retriever = VespaRetriever(
        embedder=embedder,
        vespa_url=settings.vespa_url,
        vespa_port=settings.vespa_port,
        top_k=3,
        schema="document_embeddings",
        rank_profile="dense",
    )

    print(retriever.call(
        queries, top_k=3
    ))
    # from FlagEmbedding import BGEM3FlagModel

    # model = BGEM3FlagModel(model_name="BAAI/bge-m3", normalize_embeddings=True)

    # model_output = model.encode(queries, return_dense=True, return_sparse=False, return_colbert_vecs=False)
    # response = retriever._query_dense(queries[1], model_output["dense_vecs"][1],  top_k=10)

    # model_output = model.encode(queries, return_dense=False, return_sparse=False, return_colbert_vecs=True)
    # response = retriever._query_colbert(queries[1], model_output["colbert_vecs"][1], query_len=float(model_output["colbert_vecs"][1].shape[0]),  top_k=100, timeout = 1000)

    # model_output = model.encode(queries, return_dense=True, return_sparse=True, return_colbert_vecs=True)
    # response = retriever._query_hybrid(
    #     queries[1],
    #     model_output["dense_vecs"][1],
    #     model_output["colbert_vecs"][1],
    #     query_len=float(model_output["colbert_vecs"][1].shape[0]),
    #     top_k=2,
    #     timeout=1000,
    # )

    # print(str(response.get_json()).encode("utf-8"))
