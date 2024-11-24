from pathlib import Path
import yaml
from typing import Self, Any
from pydantic import (BaseModel, Field,
                      DirectoryPath, FilePath, HttpUrl,
                      field_validator, model_validator)
from dotenv import dotenv_values


class TVTropesConfig(BaseModel):
    """
    Configuration for the TV Tropes dataset.
    Attributes:
        dataset_dir (DirectoryPath | None): The base directory of the dataset.
        documents_dir (DirectoryPath | None): The directory containing the raw document text files.
        csv_dir (DirectoryPath | None): The directory containing the CSV files.
        download_url (HttpUrl | None): URL to download the dataset.
        doc_zip_path (FilePath | None): The path to the zip file containing the raw document text files.
        csv_zip_path (FilePath | None): The path to the zip file containing the CSV files.
    """
    dataset_dir: DirectoryPath = Field(default=Path("./tvtropes"))
    csv_dir: DirectoryPath | None = None
    documents_dir: DirectoryPath | None = None
    download_url: HttpUrl | None = None
    doc_zip_path: FilePath | None= None
    csv_zip_path: FilePath | None = None
    csv_map: dict[str, str] = {
        "film_imdb_match": "film_imdb_match.csv",
        "film_tropes": "film_tropes.csv",
        "genderedness_filtered": "genderedness_filtered.csv",
        "lit_goodreads_match": "lit_goodreads_match.csv",
        "lit_tropes": "lit_tropes.csv",
        "tropes": "tropes.csv",
        "tv_imdb_match": "tv_imdb_match.csv",
        "tv_tropes": "tv_tropes.csv",
    }

    @model_validator(mode="after")
    def set_derived_directories(self):
        if self.csv_dir is None:
            self.csv_dir = self.dataset_dir
        if self.documents_dir is None:
            self.documents_dir = self.dataset_dir / "docs"
        return self
    
    @field_validator("doc_zip_path", "csv_zip_path")
    @classmethod
    def validate_zip_paths(cls, value: Any):
        if isinstance(value, str):
            value = Path(value)
        return value

    @classmethod
    def load_config_yaml(cls, dataset_dir: str | Path) -> Self:
        """
        Load the configuration from the specified config.yaml file.
        Args:
            config_path (str | Path): Path to the configuration file.
        Returns:
            TVTropesConfig: An instance of the TVTropesConfig object.
        """
        config_path = Path(dataset_dir) / "config.yaml"
        if not config_path.is_file():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
        with config_path.open('r') as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data.get("tvtropes", {}))
    
    def save_config_yaml(self, config_path: str | Path = None):
        """
        Save the configuration to the specified config.yaml file.
        Args:
            config_path (str | Path): Path to the configuration file.
        """
        if config_path is None:
            config_path = self.dataset_dir / "config.yaml"
        with config_path.open('w') as f:
            yaml.dump({"tvtropes": self.model_dump()}, f)

    def get_csv_file_path(self, dataset_name: str) -> FilePath:
        return self.csv_dir / self.csv_map[dataset_name]

env = dotenv_values(".env") 
dataset_config = TVTropesConfig.load_config_yaml(f"{env.get('DATA_FOLDER', './data')}/tvtropes")