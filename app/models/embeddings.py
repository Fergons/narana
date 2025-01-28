from typing import Any
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, ValidationError

class Embedding(BaseModel):
    model: str
    version: str | None = None
    document_id: str
    document_chunk_index: int | None = None
    colbert: NDArray[Any] | None = None
    dense: NDArray[Any] | None = None
    lexical: NDArray[Any] | None = None

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

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )