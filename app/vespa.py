from vespa.package import (
    ApplicationPackage,
    Field,
    ImportedField,
    Document,
    Schema,
    FieldSet,
    RankProfile,
    DocumentSummary,
    SecondPhaseRanking,
    Function,
    FirstPhaseRanking,
    HNSW,
)
from vespa.deployment import VespaDocker


app_package = ApplicationPackage(name="narana")

# the original data from tvtropes dataset is split into multiple tables in the CSV files
# I merged them into a single table, only difference is the name of the field Example and Description
# for a definition of a trope and example of a trope in the story
trope_example_schema = Schema(
    name="trope_examples",
    document=Document(
        fields=[
            Field(
                name="title",
                type="string",
                indexing=["summary", "attribute"],
            ),
            Field(
                name="trope",
                type="string",
                indexing=["summary", "attribute"],
            ),
            Field(name="author", type="string", indexing=["attribute", "summary"]),
            Field(
                name="example",
                type="string",
                indexing=["summary", "index"],
                index="enable-bm25",
            ),
            Field(name="trope_id", type="string", indexing=["attribute", "summary"]),
            Field(name="title_id", type="string", indexing=["attribute", "summary"]),
        ]
    ),
    fieldsets=[
        # this data will be mainly retrieved based on trope information
        FieldSet(name="default", fields=["trope", "example"]),
    ],
    rank_profiles=[RankProfile(name="bm25", first_phase="bm25(example)")],
)


trope_example_embedding_schema = Schema(
    name="trope_example_embeddings",
    inherits="trope_examples",
    document=Document(
        inherits="trope_examples",
        fields=[
            Field(name="model", type="string", indexing=["attribute", "summary"]),
            Field(name="version", type="string", indexing=["attribute", "summary"]),
            Field(
                name="dense_rep",
                type="tensor<bfloat16>(x[1024])",
                indexing=["attribute", "index"],
                ann=HNSW(distance_metric="angular"),
            ),
            Field(
                name="colbert_rep",
                type="tensor<bfloat16>(token{}, x[1024])",
                indexing=["attribute", "index"],
                ann=HNSW(distance_metric="angular"),
            ),
        ],
    ),
    rank_profiles=[
        RankProfile(
            name="dense",
            inputs=[("query(q_dense)", "tensor<bfloat16>(x[1024])")],
            inherits="default",
            first_phase="closeness(field, dense_rep)",
            match_features=["closeness(field, dense_rep)"],
        ),
        RankProfile(
            name="colbert",
            inputs=[("query(q_colbert)", "tensor<bfloat16>(qt{}, x[1024])")],
            functions=[
                Function(
                    name="max_sim",
                    expression="sum(reduce(sum(query(q_colbert) * attribute(colbert_rep), x), max, token), qt) / query(q_len_colbert)",
                ),
            ],
            first_phase=FirstPhaseRanking(
                expression="max_sim",
                rank_score_drop_limit=0.3,
            ),
        ),
    ],
)


document_schema = Schema(
    name="documents",
    global_document=True,
    document=Document(
        fields=[
            Field(name="document_id", type="string", indexing=["attribute", "summary"]),
            Field(name="parent_id", type="string", indexing=["attribute", "summary"]),
            Field(name="title", type="string", indexing=["summary", "attribute"]),
            Field(
                name="authors", type="array<string>", indexing=["summary", "attribute"]
            ),
            Field(
                name="chunks",
                type="array<string>",
                indexing=["summary", "index"],
                bolding=True,
                index="enable-bm25",
            ),
            Field(name="max_chunk_size", type="int", indexing=["attribute", "summary"]),
        ]
    ),
    fieldsets=[
        FieldSet(name="default", fields=["title", "chunks", "authors"]),
    ],
    rank_profiles=[RankProfile(name="bm25", first_phase="bm25(chunks)")],
)


doc_embedding_schema = Schema(
    name="document_embeddings",
    inherits="documents",
    document=Document(
        inherits="documents",
        fields=[
            Field(name="model", type="string", indexing=["attribute", "summary"]),
            # version is a literal with values dense, colbert or hybrid
            Field(name="version", type="string", indexing=["attribute", "summary"]),
            Field(
                name="dense_rep",
                type="tensor<bfloat16>(chunk{},x[1024])",
                indexing=["index", "attribute"],
                ann=HNSW(distance_metric="angular"),
            ),
            Field(
                name="colbert_rep",
                type="tensor<bfloat16>(chunk{},token{},x[1024])",
                indexing=["index", "attribute"],
                ann=HNSW(distance_metric="angular")
            ),
            Field(name="document_id", type="string", indexing=["attribute", "summary"]),
        ],
    ),
    fieldsets=[FieldSet(name="default", fields=["chunks", "title", "authors"])],
    rank_profiles=[
        RankProfile(
            name="dense",
            inputs=[("query(q_dense)", "tensor<bfloat16>(x[1024])")],
            inherits="default",
            first_phase="closeness(field, dense_rep)",
            match_features=["closeness(field, dense_rep)"],
        ),
        RankProfile(
            name="colbert",
            inputs=[
                ("query(q_colbert)", "tensor<bfloat16>(qt{}, x[1024])"),
                ("query(q_len_colbert)", "float"),
            ],
            functions=[
                Function(
                    name="max_sim",
                    expression="sum(reduce(sum(query(q_colbert) * attribute(colbert_rep), x), max, token), qt, chunk) / query(q_len_colbert)",
                ),
                Function(
                    name="per_chunk_max_sim",
                    expression="sum(reduce(sum(query(q_colbert) * attribute(colbert_rep), x), max, token), qt) / query(q_len_colbert)",
                )
            ],
            first_phase=FirstPhaseRanking(
                expression="max_sim",
            ),
            match_features=["max_sim", "per_chunk_max_sim"],
        ),
        RankProfile(
            name="hybrid",
            inputs=[
                ("query(q_dense)", "tensor<bfloat16>(x[1024])"),
                ("query(q_colbert)", "tensor<bfloat16>(qt{}, x[1024])"),
                ("query(q_len_colbert)", "float"),
            ],
            functions=[
                Function(
                    name="max_dense",
                    expression="reduce(cosine_similarity(query(q_dense), attribute(dense_rep), x), max, chunk)",
                ),
                Function(
                    name="avg_dense",
                    expression="reduce(cosine_similarity(query(q_dense), attribute(dense_rep), x), avg, chunk)",
                ),
                Function(
                    name="per_chunk_dense",
                    expression="cosine_similarity(query(q_dense), attribute(dense_rep), x)",
                ),
                # max_sim to handle an extra dimension chunk{} and token{}
                # - sum over x dimension: sum(query(q_colbert)*attribute(colbert_rep), x)
                #   This leaves dimensions qt{}, chunk{}, token{}.
                # - reduce with max over token dimension: reduce(..., max, token)
                #   This now leaves qt{}, chunk{}. (qt values are sim. scores with max sim tokens from each cunk)
                # - sum over qt and normalize by len of query (q_len_colbert)
                # - finally divide return max over chunks
                Function(
                    name="max_sim",
                    expression="reduce(sum(reduce(sum(query(q_colbert) * attribute(colbert_rep), x), max, token), qt) / query(q_len_colbert), max, chunk)"
                ),
            ],
            first_phase=FirstPhaseRanking(
                expression="max_dense + bm25(chunks)",
                rank_score_drop_limit=0.3,
            ),
            second_phase=SecondPhaseRanking(
                expression="max_sim",
                rerank_count=100,
            ),
            match_features=["avg_dense", "max_dense", "max_sim", "per_chunk_dense", "bm25(chunks)"],
        ),
    ],
)


app_package.add_schema(trope_example_schema)
app_package.add_schema(trope_example_embedding_schema)
app_package.add_schema(document_schema)
app_package.add_schema(doc_embedding_schema)

vespa_docker = VespaDocker()
app = vespa_docker.deploy(application_package=app_package)
