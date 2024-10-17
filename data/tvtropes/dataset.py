<<<<<<< ours
import os
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field

URL = "https://drive.usercontent.google.com/download?id=1Duyz5ATlLHzwMidj15bWVnWHpdE4aRXn&export=download"
ZIP_PATH = Path("data", "tvtropes", "TVTropesData.zip")
DATA_FOLDER_PATH= Path("data","tvtropes","TVTropesData")

def download(url=URL):
    import requests
    r = requests.get(url, allow_redirects=True)
    open(ZIP_PATH, 'wb').write(r.content)

def unzip(path=ZIP_PATH):
    import zipfile
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(".")


@dataclass
class TVTropesDataset:
    """TV Tropes dataset with attributes for each CSV file"""
    film_imdb_match: pd.DataFrame = field(default=None)
    film_tropes: pd.DataFrame = field(default=None)
    genderedness_filtered: pd.DataFrame = field(default=None)
    lit_goodreads_match: pd.DataFrame = field(default=None)
    lit_tropes: pd.DataFrame = field(default=None)
    tropes: pd.DataFrame = field(default=None)
    tv_imdb_match: pd.DataFrame = field(default=None)
    tv_tropes: pd.DataFrame = field(default=None)

    @classmethod
    def from_csv_files(cls, csv_dir: str = DATA_FOLDER_PATH) -> 'TVTropesDataset':
        """Initialize the dataset from CSV files in the specified directory"""
        dataset = cls()
        csv_files = {
            'film_imdb_match': 'film_imdb_match.csv',
            'film_tropes': 'film_tropes.csv',
            'genderedness_filtered': 'genderedness_filtered.csv',
            'lit_goodreads_match': 'lit_goodreads_match.csv',
            'lit_tropes': 'lit_tropes.csv',
            'tropes': 'tropes.csv',
            'tv_imdb_match': 'tv_imdb_match.csv',
            'tv_tropes': 'tv_tropes.csv',
        }

        for attr, filename in csv_files.items():
            file_path = csv_dir/filename
            setattr(dataset, attr, pd.read_csv(file_path))

        return dataset
    
|||||||
=======
import os
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field

URL = "https://drive.usercontent.google.com/download?id=1Duyz5ATlLHzwMidj15bWVnWHpdE4aRXn&export=download"
ZIP_PATH = Path("TVTropesData.zip")
DATA_FOLDER_PATH= Path("TVTropesData")

def download(url=URL):
    import requests
    r = requests.get(url, allow_redirects=True)
    open(ZIP_PATH, 'wb').write(r.content)

def unzip(path=ZIP_PATH):
    import zipfile
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(".")


@dataclass
class TVTropesDataset:
    """TV Tropes dataset with attributes for each CSV file"""
    film_imdb_match: pd.DataFrame = field(default=None)
    film_tropes: pd.DataFrame = field(default=None)
    genderedness_filtered: pd.DataFrame = field(default=None)
    lit_goodreads_match: pd.DataFrame = field(default=None)
    lit_tropes: pd.DataFrame = field(default=None)
    tropes: pd.DataFrame = field(default=None)
    tv_imdb_match: pd.DataFrame = field(default=None)
    tv_tropes: pd.DataFrame = field(default=None)

    @classmethod
    def from_csv_files(cls, csv_dir: str) -> 'TVTropesDataset':
        """Initialize the dataset from CSV files in the specified directory"""
        dataset = cls()
        csv_files = {
            'film_imdb_match': 'film_imdb_match.csv',
            'film_tropes': 'film_tropes.csv',
            'genderedness_filtered': 'genderedness_filtered.csv',
            'lit_goodreads_match': 'lit_goodreads_match.csv',
            'lit_tropes': 'lit_tropes.csv',
            'tropes': 'tropes.csv',
            'tv_imdb_match': 'tv_imdb_match.csv',
            'tv_tropes': 'tv_tropes.csv',
        }

        for attr, filename in csv_files.items():
            file_path = f"{csv_dir}/{filename}"
            setattr(dataset, attr, pd.read_csv(file_path))

        return dataset

>>>>>>> theirs
