from vespa.package import (ApplicationPackage, Field, Document, Schema, FieldSet, RankProfile, Function, FirstPhaseRanking)
from vespa.deployment import VespaDocker


app_package = ApplicationPackage(name="narana")

# the original data from tvtropes dataset is split into multiple tables in the CSV files
# I merged them into a single table, only difference is the name of the field Example and Description
# for a definition of a trope and example of a trope in the story
tvtropes_schema = Schema(
    name="tvtropes",
    document=Document(
        fields=[
            Field(name="title", type="string", indexing=["attribute", "summary"], optional=True),
            Field(name="trope", type="string", indexing=["attribute", "summary"], optional=True),
            Field(
                name="example",
                type="string",
                indexing=["index", "summary"],
                index="enable-bm25"
            ),
            Field(name="trope_id", type="string", indexing=["attribute", "summary"], optional=True),
            Field(name="title_id", type="string", indexing=["attribute", "summary"], optional=True),
            # Field(
            #     name="lexical_rep",
            #     type="tensor<bfloat16>(t{})",
            #     indexing=["attribute", "summary"]
            # ),
            Field(
                name="dense_rep",
                type="tensor<bfloat16>(x[1024])",
                indexing=["attribute", "summary"],
                attribute=["distance-metric: angular"]
            ),
            # Field(
            #     name="colbert_rep",
            #     type="tensor<bfloat16>(t{}, x[1024])",
            #     indexing=["attribute", "summary"]
            # )
        ]
    ),
    fieldsets=[
        FieldSet(name="default", fields=["trope", "example"]),
    ]
)

semantic = RankProfile(
    name="semantic",
    inputs=[
        ("query(q_dense)", "tensor<bfloat16>(x[1024])")
    ],
    functions=[
        Function(
            name="dense",
            expression="cosine_similarity(query(q_dense), attribute(dense_rep),x)",
        )
    ],
    first_phase=FirstPhaseRanking(
        expression="dense", rank_score_drop_limit=0.0
    ),
    match_features=["dense", "bm25(example)"],
)
tvtropes_schema.add_rank_profile(semantic)

app_package.add_schema(tvtropes_schema)
vespa_docker = VespaDocker()
app = vespa_docker.deploy(application_package = app_package)

