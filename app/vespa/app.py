from vespa.package import ApplicationPackage, Field, Document, Schema, FieldSet


app_package = ApplicationPackage(name="tropes_search")

# the original data from tvtropes dataset is split into multiple tables in the CSV files
# I merged them into a single table, only difference is the name of the field Example and Description
# for a definition of a trope and example of a trope in the story
merged_schema = Schema(
    name="tropes",
    document=Document(
        fields=[
            Field(name="id", type="string", indexing=["attribute", "summary"]),
            Field(name="title", type="string", indexing=["attribute", "summary"], optional=True),
            Field(name="trope", type="string", indexing=["attribute", "summary"], optional=True),
            Field(
                name="example",
                type="string",
                indexing=["index", "summary"],
                index="enable-bm25"
            ),
            Field(name="tropeid", type="string", indexing=["attribute", "summary"], optional=True),
            Field(name="title_id", type="string", indexing=["attribute", "summary"], optional=True),
            Field(
                name="description",
                type="string",
                indexing=["index", "summary"],
                index="enable-bm25"
            ),
            Field(
                name="lexical_rep",
                type="tensor<bfloat16>(t{})",
                indexing=["attribute", "summary"]
            ),
            Field(
                name="dense_rep",
                type="tensor<bfloat16>(x[1024])",
                indexing=["attribute", "summary"],
                attribute=["distance-metric: angular"]
            ),
            Field(
                name="colbert_rep",
                type="tensor<bfloat16>(t{}, x[1024])",
                indexing=["attribute", "summary"]
            )
        ]
    ),
    fieldsets=[FieldSet(name="default", fields=["example", "description"])]
)


app_package.add_schema(merged_schema)
app_package.to_files("./tropes_search_app")