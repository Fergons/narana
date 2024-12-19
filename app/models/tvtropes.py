from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    ConfigDict
)
from typing import Literal

TROPE_EXAMPLES_TABLES = Literal[
    "lit_goodreads_match",
    "lit_tropes",
    "film_imdb_match",
    "film_tropes",
    "tv_imdb_match",
    "tv_tropes",
]

TROPES_TABLE = Literal["tropes"]

"""
     Title	            Trope	            Example	                    trope_id    title_id
1213 SixGunSnowWhite	AdultsAreUseless	Because none of the s...	t00330	    lit9089
"""


class Title(BaseModel):
    title_id: str
    title: str = Field(..., alias="Title")
    clean_title: str | None = Field(default=None, alias="CleanTitle")
    author: str | None = Field(default=None)




class LibgenHit(BaseModel):
    authors: list[str]
    title: str
    download_urls: list[HttpUrl]
    format: Literal["epub", "pdf", "txt"]
    language: str


class LibgenSearchResult(BaseModel):
    title_id: str
    hits: list[LibgenHit]


class TropeExample(BaseModel):
    title: str = Field(..., alias="Title")
    trope: str = Field(..., alias="Trope")
    example: str = Field(..., alias="Example")
    trope_id: str
    title_id: str
    
    # Lit goodreads match
    clean_title: str | None = Field(default=None, alias="CleanTitle")
    author: str | None = Field(default=None)

    # IMDB match
    tconst: str | None = Field(default=None)

    model_config = ConfigDict(extra='ignore')

"""
        Title	                    Trope	    Example	                   \ 
188809	TheHitchhikersGuideToT...	Panspermia	The Hitchhiker's Guid...   \

CleanTitle	                author	        verified_gender	    title_id	trope_id
thehitchhikersguidetot...	Douglas Adams	male	            lit11735	t16621
"""




"""
	    TropeID	    Trope	    Description
14949	t14950	    NailEm	    Nail guns are a commo...
"""


class Trope(BaseModel):
    trope_id: str = Field(..., alias="TropeID")
    trope: str = Field(..., alias="Trope")
    description: str = Field(..., alias="Description")

    model_config = ConfigDict(extra='ignore')



class EmbedTropeExample(TropeExample):
    dense_rep: list[float]