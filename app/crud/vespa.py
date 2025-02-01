import logging
from dataclasses import dataclass, asdict, field
from typing import List, Callable, Dict, Tuple, Generator
from vespa.application import Vespa, VespaResponse
from app.models.tvtropes import TropeExample
from app.models.embeddings import Embedding
from app.models.documents import Document
from utils.string import camel_to_string

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyParams:
    """
    Encapsulate default feeding parameters for feed_iterable.
    (These get passed as **kwargs to app.feed_iterable(...))
    """

    max_connections: int = 10
    max_workers: int = 10
    max_queue_size: int = 1000


def default_feed_callback(response: VespaResponse, doc_id: str):
    """
    Default callback if feed fails or succeeds. Overwrite as needed.
    """
    if not response.is_successful():
        logger.error(f"Feed failed for document {doc_id}: {response.get_json()}")


@dataclass
class BaseVespaCRUD:
    """
    A base CRUD that defines common feed/visit logic. Subclasses can override
    schema_name, namespace, content_cluster_name or provide them in methods.
    """

    app: Vespa
    namespace: str
    content_cluster_name: str
    schema_name: str
    feed_params: ConcurrencyParams = field(default_factory=ConcurrencyParams)
    feed_callback: Callable[[VespaResponse, str], None] = default_feed_callback

    def feed_iterable(
        self,
        docs: List[Dict],
        operation_type: str = "feed",
        auto_assign: bool = True,
        **kwargs,
    ):
        """
        Generic feed operation for a batch of documents (dicts).
        - docs must be a list of dicts, each with "id" and "fields".
        - operation_type is one of "feed", "update", or "delete".
        - auto_assign indicates if we do partial updates automatically or not.

        We pass down feedParams as **asdict(self.feed_params).
        """
        all_params = asdict(self.feed_params)
        all_params.update(kwargs)
        self.app.feed_iterable(
            iter=docs,
            schema=self.schema_name,
            namespace=self.namespace,
            operation_type=operation_type,
            callback=self.feed_callback,
            auto_assign=auto_assign,
            **all_params,
        )

    def visit_all(
        self,
        selection: str = "true",
        slices: int = 1,
        wanted_document_count: int = 100,
        **kwargs,
    ):
        """
        Generic visit operation over all documents in this schema & namespace.
        Yields slices; each slice is a generator of VespaResponse.

        Example usage:
            for slice_res in self.visit_all(selection="my_field contains 'foo'"):
                for resp in slice_res:
                    ...
        """
        return self.app.visit(
            content_cluster_name=self.content_cluster_name,
            schema=self.schema_name,
            namespace=self.namespace,
            selection=selection,
            slices=slices,
            wanted_document_count=wanted_document_count,
            **kwargs,
        )


@dataclass
class VespaTropesCRUD(BaseVespaCRUD):
    """
    Operations specific to the 'trope_example_embeddings' schema.
    Inherits generic feed/visit from BaseVespaCRUD.
    """

    schema_name: str = "trope_example_embeddings"

    def feed(self, examples: List[TropeExample], **kwargs):
        """
        Create or update (operation_type='feed') documents in the trope_example_embeddings schema.
        """
        docs = [prepare_tvtrope_example(ex) for ex in examples]
        self.feed_iterable(docs, operation_type="feed", **kwargs)

    def update_embeddings(self, embeddings: List[Embedding], **kwargs):
        """
        Partial update for embeddings.
        auto_assign=False ensures we keep the 'add' operations.
        """
        update_docs = prepare_update_tvtrope_examples_embeddings(embeddings)
        self.feed_iterable(
            update_docs, operation_type="update", auto_assign=False, **kwargs
        )

    def get_all_ids(self) -> List[Tuple[str, str]]:
        """
        Returns a list of (title_id, trope_id) from all docs in this schema.
        """
        result = []
        for slice_res in self.visit_all(
            selection="true", slices=4, wanted_document_count=500
        ):
            for vespa_response in slice_res:
                if vespa_response.is_successful():
                    for doc in vespa_response.documents:
                        fields = doc["fields"]
                        result.append((fields["title_id"], fields["trope_id"]))
        return result

    def get_all(self) -> List[TropeExample]:
        """
        Retrieve all TropeExamples from this schema as domain objects.
        """
        all_examples = []
        for slice_res in self.visit_all(
            selection="true", slices=4, wanted_document_count=500
        ):
            for vespa_response in slice_res:
                if vespa_response.is_successful():
                    for doc in vespa_response.documents:
                        f = doc["fields"]
                        all_examples.append(
                            TropeExample(
                                title=f["title"],
                                trope=f["trope"],
                                title_id=f["title_id"],
                                trope_id=f["trope_id"],
                                example=f["example"],
                            )
                        )
        return all_examples

    def yield_without_embeddings(self) -> Generator[TropeExample, None, None]:
        """
        Example: visit the schema to find documents missing a certain field.
        Return them as domain objects.
        """
        selection = f"{self.schema_name}.model == null"  # or any doc selection logic
        slices = 1
        wanted_count = 100
        for slice_res in self.visit_all(
            selection=selection,
            slices=slices,
            wanted_document_count=wanted_count,
        ):
            for vespa_response in slice_res:
                if vespa_response.is_successful():
                    for doc in vespa_response.documents:
                        yield TropeExample.model_validate(doc["fields"])


@dataclass
class VespaDocumentsCRUD(BaseVespaCRUD):
    """
    Operations specific to 'document_embeddings' schema.
    """

    schema_name: str = "document_embeddings"

    def feed(self, docs: List[Document], **kwargs):
        """
        Create new documents in Vespa or update them fully (operation_type='feed').
        """
        doc_dicts = [prepare_document(d) for d in docs]
        self.feed_iterable(doc_dicts, operation_type="feed", **kwargs)

    def update_embeddings(self, embeddings: List[Embedding], **kwargs):
        """
        Partial update for embeddings.
        auto_assign=False ensures we keep the 'add' operations.
        """
        update_docs = prepare_partial_update_doc_embeddings(embeddings)
        self.feed_iterable(
            update_docs, operation_type="update", auto_assign=False, **kwargs
        )

    def get_all_parent_ids(self) -> List[str]:
        """
        Returns a list of parent_ids from all docs in this schema using visit.
        """
        parent_ids = set()  # Using set to avoid duplicates
        
        # Visit all documents in batches
        for slice_res in self.visit_all(
            selection="true",
            slices=4,  # Number of parallel slices
            wanted_document_count=500  # Documents per batch
        ):
            for vespa_response in slice_res:
                if vespa_response.is_successful():
                    for doc in vespa_response.documents:
                        if "fields" in doc and "parent_id" in doc["fields"]:
                            parent_ids.add(doc["fields"]["parent_id"])
                else:
                    logger.warning(f"Visit response unsuccessful: {vespa_response.get_json()}")
                
        return list(parent_ids)
    
    def yield_without_embeddings(self) -> Generator[Document, None, None]:
        """
        Example: visit the schema to find documents missing a certain field.
        Return them as domain objects.
        """
        selection = f"{self.schema_name}.model == null"  # or any doc selection logic
        slices = 1
        wanted_count = 100
        for slice_res in self.visit_all(
            selection=selection,
            slices=slices,
            wanted_document_count=wanted_count,
        ):
            for vespa_response in slice_res:
                if vespa_response.is_successful():
                    for doc in vespa_response.documents:
                        yield Document.model_validate(doc["fields"])


def prepare_tvtrope_example(trope_example: TropeExample) -> dict:
    return {
        "id": f"{trope_example.title_id}_{trope_example.trope_id}",
        "fields": {
            "title": camel_to_string(trope_example.title),
            "trope": camel_to_string(trope_example.trope),
            "example": 
                f"Trope {camel_to_string(trope_example.trope)} " \
                f"can be found in {camel_to_string(trope_example.title)} " \
                f"as {trope_example.example}",
        
            "title_id": trope_example.title_id,
            "trope_id": trope_example.trope_id,
        },
    }


def prepare_document(doc: Document) -> dict:
    return {
        "id": doc.document_id,
        "fields": {
            "document_id": doc.document_id,
            "parent_id": doc.parent_id,
            "title": doc.title,
            "authors": doc.authors,
            "chunks": doc.chunks,
            "max_chunk_size": doc.max_chunk_size,
        },
    }


def prepare_partial_update_doc_embeddings(embeddings: list[Embedding]) -> list[dict]:
    return [
        {
            "id": e.document_id,
            "fields": {
                "model": {
                    "assign": e.model,
                },
                "version": {"assign": e.version},
                "dense_rep": {
                    "add": {
                        "blocks": [
                            {
                                "address": {
                                    "chunk": e.document_chunk_index,
                                },
                                "values": e.dense.tolist(),
                            },
                        ],
                    },
                },
                "colbert_rep": {
                    "add": {
                        "blocks": [
                            {
                                "address": {
                                    "chunk": e.document_chunk_index,
                                    "token": i,
                                },
                                "values": e.colbert[i].tolist(),
                            }
                            for i in range(e.colbert.shape[0])
                        ],
                    },
                },
            },
        }
        for e in embeddings
    ]


def prepare_update_tvtrope_examples_embeddings(
    embeddings: list[Embedding],
) -> list[dict]:
    return [
        {
            "id": e.document_id,
            "fields": {
                "model": {"assign": e.model},
                "version": {"assign": e.version},
                "dense_rep": {
                    "assign": e.dense.tolist(),
                },
                "colbert_rep": {
                    "assign": {
                        "blocks": [
                            {
                                "address": {
                                    "token": i,
                                },
                                "values": e.colbert[i].tolist(),
                            }
                            for i in range(e.colbert.shape[0])
                        ],
                    }
                },
            },
        }
        for e in embeddings
    ]


if __name__ == "__main__":
    app = Vespa(url="http://localhost", port=8080)
    crud = VespaDocumentsCRUD(
        app=app,
        content_cluster_name="narana_content",
        namespace="narana",
    )
    print(crud.schema_name)
    print(len(crud.get_all_parent_ids()))


