from app.models.tvtropes import TropeExample
from app.models.documents import Document
from app.crud.tvtropes import TropeExamplesCRUD
from app.crud.documents import DocumentsCRUD
from app.config import settings  
from app.crud.vespa import VespaDocumentsCRUD, VespaTropesCRUD
from vespa.application import Vespa
from typing import Sequence
import time

import argparse
from itertools import islice
import logging
from app.models.embeddings import Embedding


basic_config = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bgem3_embed_trope_examples(
    model: "BGEM3FlagModel",
    data: Sequence[TropeExample],
    return_colbert=False,
    return_dense=True,
    return_lexical=False,
):
    output = model.encode(
        batch_size=32,
        sentences=[example.example for example in data],
        return_dense=return_dense,
        return_colbert_vecs=return_colbert,
        return_sparse=return_lexical,
    )

    colbert = output["colbert_vecs"] if return_colbert else [None] * len(data)
    dense = output["dense_vecs"] if return_dense else [None] * len(data)
    lexical = (
        output["lexical_weights"] if return_lexical else [None] * len(data)
    )

    out = []
    for colbert, dense, lexical, example in zip(
        colbert, dense, lexical, data
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
    data: Sequence[Document],
    return_colbert=False,
    return_dense=True,
    return_lexical=False,
) -> list[Embedding]:
    flattend_chunks = [
        (document.document_id, chunk_index, chunk)
        for document in data
        for chunk_index, chunk in enumerate(document.chunks)
    ]

    output = model.encode(
        batch_size=32,
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
                colbert=colbert if return_colbert else None,
                dense=dense if return_dense else None,
                lexical=lexical if return_lexical else None,
            )
        )
    return out


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
        "--batch_size",
        type=int,
        default=32,
        help="Number data points in one processing batch",
    )

    argparse.add_argument(
        "--embed",
        action="store_true",
        default=False,
        help="Whether to encode text data in vespa",
    )

    print(settings.model_dump())
    args = argparse.parse_args()
    
    vespa = Vespa(
        url=settings.vespa.url,
        port=settings.vespa.port,
    )

    if args.schema == "trope_examples":
        data_crud = TropeExamplesCRUD.load_from_csv(config=settings.tvtropes, name="lit_goodreads_match")
        vespa_crud = VespaTropesCRUD(app=vespa, namespace=settings.vespa.namespace, content_cluster_name=settings.vespa.content_cluster)
        embedder = bgem3_embed_trope_examples
        
    elif args.schema == "documents":
        data_crud = DocumentsCRUD(config=settings.books)
        vespa_crud = VespaDocumentsCRUD(app=vespa, namespace=settings.vespa.namespace, content_cluster_name=settings.vespa.content_cluster)
        embedder = bgem3_embed_documents_with_chunks

    if args.mode == "embed":
        from FlagEmbedding import BGEM3FlagModel
        model = BGEM3FlagModel(
            model_name_or_path="BAAI/bge-m3", use_fp16=True, device="cuda"
        )
        doc_gen = vespa_crud.yield_without_embeddings()
        while True:
            try:
                data = list(islice(doc_gen, args.batch_size))
                if len(data) == 0:
                    break
                embeddings = embedder(
                    model=model,
                    data=data,
                    return_colbert=True,
                    return_dense=True,
                )
                vespa_crud.update_embeddings(
                    embeddings
                )
            except StopIteration:
                logger.info("All documents have been encoded.")
                break
            finally:
                time.sleep(5)

    if args.mode == "feed":
        gen = data_crud.batch_generator(
            batch_size=args.batch_size, limit=args.limit, offset=0, exclude_ids=[]
        )
        for batch in gen:
            vespa_crud.feed(batch)

           
