
from adalflow import OllamaClient

character_identification_config = {
    "model_client": OllamaClient(host="http://localhost:11434"),
    "model_kwargs": {
        "model": "deepseek-r1:8b",
        # "temperature": 0.0,
        # "top_p": 0.9,
        # "top_k": 0,
        # "repetition_penalty": 1.0,
        # "max_tokens": 1000,
        # "stop": None
    },
    "text_splitter_config": {
        "split_by": "word",
        "chunk_size": 200,
        "chunk_overlap": 50
    }
}

