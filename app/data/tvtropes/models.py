from pydantic import (BaseModel, Field, TypeAdapter,
                      FileUrl, FilePath, HttpUrl, DirectoryPath, UUID4,
                      field_validator, 
                      ValidationError)
from typing import Literal, Annotated

DATASET_CHOICE = Literal['lit_goodreads_match', 'lit_tropes',
                          'film_imdb_match', 'film_tropes',
                            'tv_imdb_match', 'tv_tropes',
                              'tropes', 'genderedness_filtered'] 

"""
     Title	            Trope	            Example	                    trope_id    title_id
1213 SixGunSnowWhite	AdultsAreUseless	Because none of the s...	t00330	    lit9089
"""
class LitTrope(BaseModel):
    name: Literal['lit_tropes']
    title: str = Field(..., alias="Title")
    trope: str = Field(..., alias="Trope")
    example: str = Field(..., alias="Example")
    trope_id: str
    title_id: str

    model_config = {'case_sensitive': False}


"""
        Title	                    Trope	    Example	                   \ 
188809	TheHitchhikersGuideToT...	Panspermia	The Hitchhiker's Guid...   \

CleanTitle	                author	        verified_gender	    title_id	trope_id
thehitchhikersguidetot...	Douglas Adams	male	            lit11735	t16621
"""     
class LitGoodreadsMatch(LitTrope):
    name: Literal['lit_goodreads_match']
    clean_title: str = Field(..., alias="CleanTitle")
    author: str
    verified_gender: str




"""
	    TropeID	    Trope	    Description
14949	t14950	    NailEm	    Nail guns are a commo...
"""
class Trope(BaseModel):
    trope_id: str = Field(..., alias="TropeID")
    trope: str = Field(..., alias="Trope")
    description: str = Field(..., alias="Description")



class DocumentTropeMatch(BaseModel):
    document_id: UUID4
    title_id: str
    download_url: HttpUrl



TropeExample = Annotated[LitTrope|LitGoodreadsMatch, Field(discriminator="name")]

