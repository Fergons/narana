def embed_dataset(dataset, model):
    embeddings = []
    for story in dataset:
        embeddings.append(model.encode(story.text))
    return embeddings