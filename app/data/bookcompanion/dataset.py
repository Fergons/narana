from dataclasses import dataclass
import pandas as pd
from pathlib import Path
from dotenv import dotenv_values

config = dotenv_values(".env")

@dataclass
class BookListItem:
    title: str
    author: str
    links_url: str
    character_list_url: str
    scraped_character_list: bool
    goodreads_link: str | None
    text_file_path: str

    @classmethod
    def from_row(cls, row: dict):
        return cls(
            title=row['title'],
            author=row['author'],
            links_url=row['links_url'],
            character_list_url=row['character_list_url'],
            scraped_character_list=row['scraped_character_list'],
            goodreads_link=row['goodreads_link'],
            text_file_path=row['text_file_path']
        )

@dataclass
class BookCompanion:
    DATASET_PATH = Path(config.get('DATA_FOLDER'), 'bookcompanion')
    _file_names = {
        'book_list': 'book_list.csv',
        'characters': 'characters.csv'
    }

    book_list: pd.DataFrame 
    characters: pd.DataFrame

    @classmethod
    def load_from_csv(cls):
        book_list = pd.DataFrame()
        characters = pd.DataFrame()
        if (cls.DATASET_PATH / cls._file_names['book_list']).exists():
            book_list = pd.read_csv(cls.DATASET_PATH / cls._file_names['book_list'])
        if (cls.DATASET_PATH / cls._file_names['characters']).exists():
            characters = pd.read_csv(cls.DATASET_PATH / cls._file_names['characters'])
        return cls(book_list, characters)
      
   
    def save_book_list(self):
        if not self.DATASET_PATH.exists():
            self.DATASET_PATH.mkdir(parents=True)
        self.book_list.to_csv(self.DATASET_PATH / self._file_names['book_list'], index=False)
    
    def save_characters(self):
        self.characters.to_csv(self.DATASET_PATH / self._file_names['characters'], index=False)
    
    def save(self):
        self.save_book_list()
        self.save_characters()
    
    def update_book_list(self, new_book_list: pd.DataFrame):
        self.book_list = pd.concat([self.book_list, new_book_list]).drop_duplicates(subset=['character_list_url']).reset_index(drop=True)

    def update_characters(self, new_characters: pd.DataFrame):
        self.characters = pd.concat([self.characters, new_characters]).drop_duplicates().reset_index(drop=True)

    def get_txt_for_title(self, title: str) -> Path:
        return self.book_list[self.book_list['title'] == title]['text_file_path'].values[0]
    
    def get_character_list_for_title(self, title: str) -> Path:
        return self.characters.groupby('title').get_group(title)['character_list'].values[0]
    
    def get_character_list_for_character_list_url(self, character_list_url: str) -> dict:
        return self.characters[self.characters['character_list_url'] == character_list_url].to_dict(orient='records')
    
    def get_goodreads_link_for_title(self, title: str) -> Path:
        return self.book_list[self.book_list['title'] == title]['goodreads_link'].values[0]
   


    