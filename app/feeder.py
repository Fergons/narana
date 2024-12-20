from utils.string import camel_to_string
from app.models.tvtropes import TropeExample
from app.models.documents import Document
from app.crud.tvtropes import TropeExamplesCRUD, BaseTropesCRUD
from app.crud.documents import DocumentsCRUD
from app.config import vespa_config, tvtropes_config, books_config
from app.crud.vespa import VespaCRUD, VespaParams
import asyncio
from vespa.application import Vespa, VespaAsync
from typing import Sequence
import time
from pydantic import BaseModel, ValidationError
import argparse


class Embedding(BaseModel):
    model: str
    version: str | None
    document_id: str
    document_chunk_index: int | None
    colbert: list[float] | None
    dense: list[float] | None
    lexical: list[float] | None

    def model_post_init(self, __context):
        match (self.colbert, self.dense, self.lexical):
            case (c, d, l) if c is not None and d is not None and l is not None:
                self.version = "dense+colbert+lexical"
            case (c, d, l) if c is not None and d is not None:
                self.version = "dense+colbert"
            case (c, d, l) if d is not None:
                self.version = "dense"
            case (c, d, l) if c is not None:
                self.version = "colbert"
            case (c, d, l) if l is not None:
                self.version = "lexical"
            case _:
                raise ValidationError(
                    "At least one of colbert, dense, lexical must be not None"
                )


def bgem3_embed_trope_examples(
    model: "BGEM3FlagModel",
    trope_examples: Sequence[TropeExample],
    return_colbert=False,
    return_dense=True,
    return_lexical=False,
):
    output = model.encode(
        batch_size=32,
        sentences=[example.example for example in trope_examples],
        return_dense=return_dense,
        return_colbert_vecs=return_colbert,
        return_sparse=return_lexical,
    )

    colbert = output["colbert_vecs"] if return_colbert else [None] * len(trope_examples)
    dense = output["dense_vecs"] if return_dense else [None] * len(trope_examples)
    lexical = (
        output["lexical_weights"] if return_lexical else [None] * len(trope_examples)
    )

    out = []
    for colbert, dense, lexical, example in zip(
        colbert, dense, lexical, trope_examples
    ):
        out.append(
            Embedding(
                model="BAAI/bge-m3",
                document_id=f"{example.title_id}_{example.trope_id}",
                colbert=colbert,
                dense=dense,
                lexical=lexical,
            )
        )
    return out


def bgem3_embed_documents_with_chunks(
    model: "BGEM3FlagModel",
    documents: Sequence[Document],
    return_colbert=False,
    return_dense=True,
    return_lexical=False,
):
    flattend_chunks = [
        (document.document_id, chunk_index, chunk)
        for document in documents
        for chunk_index, chunk in enumerate(document.chunks)
    ]

    output = model.encode(
        batch_size=8,
        sentences=[chunk for _, _, chunk in flattend_chunks],
        return_dense=return_dense,
        return_colbert_vecs=return_colbert,
        return_sparse=return_lexical,
    )

    colbert = (
        output["colbert_vecs"] if return_colbert else [None] * len(flattend_chunks)
    )
    dense = output["dense_vecs"] if return_dense else [None] * len(flattend_chunks)
    lexical = (
        output["lexical_weights"] if return_lexical else [None] * len(flattend_chunks)
    )

    out = []
    for colbert, dense, lexical, (document_id, chunk_index, _) in zip(
        colbert, dense, lexical, flattend_chunks
    ):
        out.append(
            Embedding(
                model="BAAI/bge-m3",
                document_id=document_id,
                document_chunk_index=chunk_index,
                colbert=colbert,
                dense=dense,
                lexical=lexical,
            )
        )
    return out


def feed_tropes_to_vespa(
    trope_examples_crud: BaseTropesCRUD, vespa_crud: VespaCRUD, limit: int = 10
):
    for trope_example in trope_examples_crud.batch_generator(
        batch_size=32, limit=10, offset=1000, exclude_ids=[]
    ):
        vespa_crud.feed_trope_examples(trope_example, operation_type="feed")


def feed_documents_to_vespa(
    documents_crud: DocumentsCRUD,
    vespa_crud: VespaCRUD,
    limit: int = 10,
    trope_examples_crud=None,
):
    for batch in documents_crud.batch_generator(
        batch_size=8, limit=10, offset=0, exclude_ids=[]
    ):
        if trope_examples_crud is not None:
            batch = trope_examples_crud.add_info_to_documents(batch)
        vespa_crud.feed_documents(batch)


if __name__ == "__main__":
    argparse = argparse.ArgumentParser()
    argparse.add_argument(
        "--mode",
        type=str,
        default="feed",
        help="Feed data to Vespa",
    )
    argparse.add_argument(
        "--schema",
        type=str,
        default="trope_examples",
        help="Schema to feed",
    )

    argparse.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of data points to feed",
    )

    argparse.add_argument(
        "--embed",
        action="store_true",
        default=False,
        help="Whether to encode text data in vespa",
    )

    vespa_crud = VespaCRUD(
        app=Vespa(url=vespa_config.url, port=vespa_config.port),
        feedParams=VespaParams(),
    )

    args = argparse.parse_args()
    if args.mode == "embed":
        from FlagEmbedding import BGEM3FlagModel

        model = BGEM3FlagModel(
            model_name_or_path="BAAI/bge-m3", use_fp16=True, device="cuda"
        )

        vespa_crud

    if args.mode == "feed":
        if args.schema == "trope_examples":
            trope_examples_crud = TropeExamplesCRUD.load_from_csv("lit_goodreads_match")
            feed_tropes_to_vespa(trope_examples_crud, vespa_crud, limit=args.limit)

        elif args.schema == "documents":
            documents_crud = DocumentsCRUD(config=books_config)
            trope_examples_crud = TropeExamplesCRUD.load_from_csv("lit_goodreads_match")
            feed_documents_to_vespa(
                documents_crud,
                vespa_crud,
                limit=args.limit,
                trope_examples_crud=trope_examples_crud,
            )
