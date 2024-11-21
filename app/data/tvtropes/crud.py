import pandas as pd
from dataclasses import dataclass
from .config import config
from .models import TropeExample, DATASET_CHOICE
from typing import Literal
from pydantic import TypeAdapter



@dataclass
class TropeExamplesCRUD:
    name: DATASET_CHOICE
    df: pd.DataFrame

    @classmethod
    def load_from_csv(cls, name: DATASET_CHOICE):
        df = pd.read_csv(config.get_csv_file_path(name))
        return cls(name=name, df=df)
    
    def save_to_csv(self):
        self.df.to_csv(config.get_csv_file_path(self.name), index=True)
    
    def get_trope_examples_for_title_id(self, title_id: str) -> list[TropeExample]:
        """Returns a list of TropeExamples for a given title_id."""
        filtered_df = self.df[self.df['title_id'] == title_id]
        return [TypeAdapter(TropeExample).validate_python({'name': self.name, **row}) for _, row in filtered_df.iterrows()]