
import os
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field
import numpy as np
 
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
    path: Path = None
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
        dataset.path = csv_dir
        return dataset

    def get_rows_for_trope_id(self, trope_id: str, n: int) -> pd.DataFrame:
        # merge dataframes
        merged = pd.concat([self.film_tropes, self.tv_tropes, self.lit_tropes])
        matches = merged[merged['trope_id'] == trope_id]
        #drop column with Nans in Example column and small not comprehensive examples
        merged = self.preprocess_examples(merged)
        return matches
    

    def preprocess_examples(self, df: pd.DataFrame, char_limit: int = 100) -> pd.DataFrame:
        # Drop rows with NaNs in the Example column and non-comprehensive examples
        new_df = df.dropna(subset=['Example'])
        new_df = new_df[new_df['Example'].str.len() > char_limit]
        return new_df

    def get_rows_for_trope_ids(self, trope_ids: list[str], n: int) -> pd.DataFrame:
        # Merge dataframes
        merged = pd.concat([self.film_tropes, self.tv_tropes, self.lit_tropes])
        # Filter by specified trope_ids
        filtered = merged[merged['trope_id'].isin(trope_ids)]
        # Drop rows with NaNs in Example column and non-comprehensive examples
        filtered = self.preprocess_examples(filtered)

        # Get distribution of rows by trope_id
        label_freq = filtered["trope_id"].value_counts()
        n_per_label = n // len(trope_ids)
        less_than_n = label_freq[label_freq <= n_per_label]
        more_than_n = label_freq[label_freq > n_per_label]

        final = pd.DataFrame()

        # Add all rows for trope_ids with fewer rows than n_per_label
        for trope_id, count in less_than_n.items():
            final = pd.concat([final, filtered[filtered['trope_id'] == trope_id]])

        # Sample rows for trope_ids with more rows than n_per_label
        for trope_id, count in more_than_n.items():
            final = pd.concat([final, filtered[filtered['trope_id'] == trope_id].sample(n_per_label)])

        return final.reset_index(drop=True)
    
    def get_split_for_n_examples_k_classes(self, n: int, k: int) -> pd.DataFrame:
        merged = pd.concat([self.film_tropes, self.tv_tropes, self.lit_tropes])
        merged = self.preprocess_examples(merged)
        label_freq = merged["trope_id"].value_counts()
        n_per_label = n // k
        more_than_n = label_freq[label_freq >= n_per_label]
        more_than_n = np.random.choice(more_than_n.index, k, replace=False)
       
        final = pd.DataFrame()

        for trope_id in more_than_n:
            final = pd.concat([final, merged[merged['trope_id'] == trope_id].sample(n_per_label)])

        return final
        