
import os
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field
 
"""
Dataset description
Each line of reddit_short_stories.txt is one full short story.
Each short story begins with an "<sos>" token and ends with an "<eos>" token (eg. "<sos> once upon a time, the end <eos>").
Newline characters in a story are replaced with the "<nl>" token (eg. "<sos> line 1 <nl> line 2 <eos>")
"""
@dataclass
class Story:
    _id: int
    text: str

@dataclass
class RedditShortStoriesDataset:
    path = Path()
    def __init__ (self, path):
        self.path = path
        self.stories = self.__load()

    @staticmethod
    def process_line(line):
    # strip <sos> and <eos> tags and replace <nl> for newlines
        return line.replace("<sos> ", "").replace(" <eos>", "").replace(" <nl> ", "\n")
    
    def __load(self):
        with open(self.path) as f:
            for _id, line in enumerate(f):
                yield Story(_id, self.process_line(line))
        
    def __iter__(self):
        yield from self.stories


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
    def from_csv_files(cls, csv_dir: Path|str) -> 'TVTropesDataset':
        """Initialize the dataset from CSV files in the specified directory"""
        csv_dir = Path(csv_dir)
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
    