import asyncio
from vespa.application import Vespa, VespaAsync, VespaQueryResponse
from vespa.exceptions import VespaError
from utils.string import camel_to_string
from app.models.tvtropes import TropeExample, EmbedTropeExample
from app.models.documents import Document
from typing import Sequence, Literal
from dataclasses import dataclass, asdict
from app.config import vespa_config
import logging


basic_config = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VespaParams:
    max_connections: int | None = None
    max_workers: int | None = None
    max_queue_size: int | None = None
    num_concurrent_requests: int | None = None


def feed_callback(response: VespaQueryResponse, id: str):
    if not response.is_successful():
        logger.error(f"Feed failed for document {id}: {response.get_json()}")


@dataclass
class VespaCRUD:
    app: Vespa
    feedParams: VespaParams

    def feed_trope_examples(self, batch: list[TropeExample], **kwargs):
        self.app.feed_iterable(
            iter=[prepare_tvtrope_example(example) for example in batch],
            schema="trope_example_embeddings",
            namespace="narana",
            callback=feed_callback,
            **kwargs,
            # **asdict(self.feedParams),
        )

    def feed_documents(self, batch: list[Document], **kwargs):
        self.app.feed_iterable(
            iter=[prepare_document(example) for example in batch],
            schema="document_embeddings",
            namespace="narana",
            callback=feed_callback,
            **kwargs,
            # **asdict(self.feedParams),
        )

    def feed_embeddings(self, batch: list):
        self.app.feed_iterable()

    def get_tvtropes_ids(self):
        all_ids = []
        for slice in self.app.visit(
            schema="trope_example_embeddings",
            namespace="narana",
            selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
            slices=4,
            wanted_document_count=500,
        ):
            for response in slice:
                if response.is_successful():
                    all_ids.extend(
                        [
                            (doc["fields"]["title_id"], doc["fields"]["trope_id"])
                            for doc in response.documents
                        ]
                    )
        return all_ids
    
    def get_documents_without_embeddings(self) -> Document:
        for slice in self.app.visit(
            schema="document_embeddings",
            namespace="narana",
            selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
            slices=4,
            wanted_document_count=500,
        ):
            for response in slice:
                if response.is_successful():
                    return [
                        Document(
                            document_id=doc["fields"]["document_id"],
                            parent_id=doc["fields"]["parent_id"],
                            title=doc["fields"]["title"],
                            authors=doc["fields"]["authors"],
                            chunks=doc["fields"]["chunks"],
                            max_chunk_size=doc["fields"]["max_chunk_size"],
                        )
                        for doc in response.documents if doc.get("fields", {}).get("dense_rep") is None
                    ]


    def get_tvtopes_examples(self):
        all_examples = []
        for slice in self.app.visit(
            schema="trope_example_embeddings",
            namespace="narana",
            selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
            slices=4,
            wanted_document_count=500,
        ):
            for response in slice:
                if response.is_successful():
                    all_examples.extend(
                        [
                            TropeExample(
                                title=doc["fields"]["title"],
                                trope=doc["fields"]["trope"],
                                title_id=doc["fields"]["title_id"],
                                trope_id=doc["fields"]["trope_id"],
                                example=doc["fields"]["example"],
                            )
                            for doc in response.documents
                        ]
                    )


def prepare_tvtrope_example(trope_example: TropeExample) -> dict:
    return {
        "id": f"{trope_example.title_id}_{trope_example.trope_id}",
        "fields": {
            "title": camel_to_string(trope_example.title),
            "trope": camel_to_string(trope_example.trope),
            "example": f"Trope {camel_to_string(trope_example.trope)} can be found in {camel_to_string(trope_example.title)} as {trope_example.example}",
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


if __name__ == "__main__":
    crud = VespaCRUD(
        app=Vespa(url=vespa_config.url, port=vespa_config.port),
        feedParams=VespaParams(),
    )
    print(crud.get_tvtropes_ids())
