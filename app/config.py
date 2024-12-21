# config.py
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Literal

from pydantic import (
    BaseModel,
    DirectoryPath,
    FilePath,
    HttpUrl,
    Field,
    AnyHttpUrl,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class TVTropesConfig(BaseModel):
    """
    Configuration for the TVTropes dataset.
    - AppSettings override 'dataset_dir' from environment, then load config.yaml if present.
    """
    dataset_dir: DirectoryPath = Field(default=Path("./data/tvtropes"))
    csv_dir: Optional[DirectoryPath] = None
    documents_dir: Optional[DirectoryPath] = None
    download_url: Optional[HttpUrl] = None
    doc_zip_path: Optional[FilePath] = None
    csv_zip_path: Optional[FilePath] = None

    csv_map: Dict[str, str] = Field(
        default_factory=lambda: {
            "film_imdb_match": "film_imdb_match.csv",
            "film_tropes": "film_tropes.csv",
            "genderedness_filtered": "genderedness_filtered.csv",
            "lit_goodreads_match": "lit_goodreads_match.csv",
            "lit_tropes": "lit_tropes.csv",
            "tropes": "tropes.csv",
            "tv_imdb_match": "tv_imdb_match.csv",
            "tv_tropes": "tv_tropes.csv",
        }
    )

    def load_yaml_overrides(self) -> "TVTropesConfig":
        """
        If 'config.yaml' is present in dataset_dir, override fields
        from the 'tvtropes' section.
        """
        config_path = self.dataset_dir / "config.yaml"
        if config_path.is_file():
            with config_path.open("r") as f:
                data = yaml.safe_load(f) or {}
            tv_data = data.get("tvtropes", {})
            # merges fields from tv_data into a copy of self
            return self.model_copy(update=tv_data)
        return self

    def finalize(self) -> "TVTropesConfig":
        """
        Set derived fields if not provided (csv_dir, documents_dir).
        """
        if self.csv_dir is None:
            object.__setattr__(self, "csv_dir", self.dataset_dir)
        if self.documents_dir is None:
            object.__setattr__(self, "documents_dir", self.dataset_dir / "docs")
        return self

    def get_csv_file_path(self, dataset_name: str) -> FilePath:
        """
        Return absolute path for the CSV name from csv_map.
        """
        csv_filename = self.csv_map[dataset_name]  # May raise KeyError if not in map
        return (self.csv_dir or self.dataset_dir) / csv_filename



class BooksConfig(BaseModel):
    """
    Configuration for the Books dataset or chunking logic.
    """
    dir: DirectoryPath = Field(default=Path("./data/books"))
    max_chunk_size: int = Field(default=1000, description="Max chunk size in words")
    overlap: int = Field(default=250, description="Overlap in words")

    def finalize(self) -> "BooksConfig":
        """
        E.g. ensure overlap < max_chunk_size.
        """
        if self.overlap >= self.max_chunk_size:
            object.__setattr__(self, "overlap", self.max_chunk_size // 2)
        return self



class VespaConfig(BaseModel):
    """
    Configuration for connecting to a Vespa instance.
    - Also no direct env reading here, we let AppSettings do it.
    """
    url: AnyHttpUrl = Field(default="http://localhost")
    port: int = Field(default=8080)
    namespace: str = Field(default="narana")
    content_cluster: str = Field(default="narana_content")

    def finalize(self) -> "VespaConfig":
        return self

    @property
    def endpoint(self) -> str:
        return f"{self.url.rstrip('/')}:{self.port}"



class AppSettings(BaseSettings):
    """
    Main settings class that loads environment variables from .env
    (like DATA_FOLDER, VESPA_URL, VESPA_PORT, etc.),
    merges them into sub-config models, and calls finalize methods.
    """
    model_config = SettingsConfigDict(env_file=".env")
    environment: Literal["dev", "prod", "test"] = Field(default="dev", env="ENVIRONMENT")

    # General environment overrides
    data_folder: DirectoryPath = Field(default=Path("./data"), env="DATA_FOLDER")
    proxy: str = Field(default="", env="PROXY")

    # VESPA environment overrides
    vespa_url: AnyHttpUrl = Field(default="http://localhost", env="VESPA_URL")
    vespa_port: int = Field(default=8080, env="VESPA_PORT")
    vespa_namespace: str = Field(default="narana", env="VESPA_NAMESPACE")
    vespa_content_cluster: str = Field(default="narana_content", env="VESPA_CONTENT_CLUSTER")

    # Sub-configs
    tvtropes: TVTropesConfig = TVTropesConfig()
    books: BooksConfig = BooksConfig()
    vespa: VespaConfig = VespaConfig()

    def post_init(self) -> "AppSettings":
        """
        - Merge environment-based directory paths into tvtropes and books.
        - Possibly load config.yaml for tvtropes, then finalize.
        - Merge env-based vespa fields into VespaConfig, finalize.
        """

        new_tvt = self.tvtropes.model_copy(update={
            "dataset_dir": self.data_folder / "tvtropes",
        })
        new_tvt = new_tvt.finalize()

    
        new_books = self.books.model_copy(update={
            "dir": self.data_folder / "books",
        }).finalize()


        new_vespa = self.vespa.model_copy(update={
            "url": self.vespa_url,
            "port": self.vespa_port,
            "namespace": self.vespa_namespace,
            "content_cluster": self.vespa_content_cluster,
        }).finalize()

        object.__setattr__(self, "tvtropes", new_tvt)
        object.__setattr__(self, "books", new_books)
        object.__setattr__(self, "vespa", new_vespa)

        return self
    

settings = AppSettings().post_init()