from nltk import sent_tokenize

def sentence_chunking(input_text: str, tokenizer: callable):
    """
    Splits a text into sentences using nltk punk tokenizer.

    Parameters
    ----------
    input_text: str
        Text to be split.
    tokenizer: callable
        Tokenizer to be used.

    Returns
    -------
    dict
        Dictionary with the following keys:
        - 'sentences': List of sentences.
        - 'input_ids': List of input ids.
        - 'spans': List of spans.

    Example:
    --------
    >>> input_text = "This is a sample text."
    >>> out = sentence_chunking(input_text, tokenizer)
    >>> out == {'sentences': ['This is a sample text.'],
    >>>        'input_ids': [1, 2, 3, 4, 5],
    >>>        'spans': [(0, 5)]}
    """
    sentences = sent_tokenize(input_text)
    last_offset_index = 0
    final_chunk = []
    spans = []
    for sentence in sentences:
        tokens = tokenizer(sentence, return_tensors='pt', add_special_tokens=False)
        input_ids = tokens['input_ids'][0]
        final_chunk.extend(input_ids)
        spans.append((last_offset_index, last_offset_index + len(input_ids)))
        last_offset_index += len(input_ids)
    
    return {'sentences': sentences, 'input_ids': final_chunk, 'spans': spans}


def late_chunking(
    model_output: 'BatchEncoding', span_annotation: list, max_length=None
):
    token_embeddings = model_output[0]
    outputs = []
    for embeddings, annotations in zip(token_embeddings, span_annotation):
        if (
            max_length is not None
        ):  # remove annotations which go bejond the max-length of the model
            annotations = [
                (start, min(end, max_length - 1))
                for (start, end) in annotations
                if start < (max_length - 1)
            ]
        pooled_embeddings = []
        for start, end in annotations:
            if (end - start) >= 1:
                if start == 0:
                    start += 1
                    end += 1
                pooled_embeddings.append(
                    embeddings[start:end].sum(dim=0) / (end - start)
                )



        pooled_embeddings = [
            embedding.detach().cpu().numpy() for embedding in pooled_embeddings
        ]
      
        outputs.append(pooled_embeddings)

    return outputs


def split_doc_to_chunks(tokens: list[int], spans: list[(int, int)], max_length: int, overlap: int = 0):
    """
    Assembles the max possible chunks (up to (max_length - 2) of tokens) from whole document tokens
    while respecting max_length of model's context and sentence boundries or other boundaries set by spans. (e.g. last sentence that fits whole into the context will be included, the next sentece is going to end up in the next chunk).

    Parameters
    ----------
    tokens: list[int]
        list of input ids for the whole document.
    spans: list[(int,int)]
        list of (start, end) tuples.
    max_length: int
        max number of tokens per chunk usually set it to model's context - 2 to leave room for [CLS] and [SEP] tokens
    overlap: int
        number of tokens to overlap between chunks.
    
    Returns
    -------
    dict
        Dictionary with the following keys:
        - 'batched_input_ids': List of lists of input ids.
        - 'spans': List of spans.
    
    Example:
    --------
    >>> tokens = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> spans = [(0, 5), (6, 10)]
    >>> out = split_doc_to_chunks(tokens, spans, max_length=5)
    >>> out == {'batched_input_ids': [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]], 'spans': [(0, 5), (6, 10)]}
    """
    chunks = []
    chunk_spans = []
    last_chunk_span = (0,0)
    for i, span in enumerate(spans):
        start, end = span
        if (end - last_chunk_span[1] > max_length):
            new_chunk_span = (last_chunk_span[1], spans[i-1][1])
            chunk_spans.append(new_chunk_span)
            last_chunk_span = new_chunk_span
        if end >= len(tokens):
            new_chunk_span = (last_chunk_span[1], end)
            chunk_spans.append(new_chunk_span)

    if overlap > 0:
        for i, span in enumerate(chunk_spans):
            start, end = span
            new_start = start - overlap
            new_end = end + overlap
            if new_start < 0:
                new_start = 0
            if new_end > len(tokens):
                new_end = len(tokens)
            chunk_spans[i] = (new_start, new_end)
            
    return {'batched_input_ids': [tokens[start:end] for (start, end) in chunk_spans], 'spans':chunk_spans}  

