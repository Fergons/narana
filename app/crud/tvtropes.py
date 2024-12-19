from abc import abstractmethod
import pandas as pd
from dataclasses import dataclass
from app.config import tvtropes_config
from app.models.tvtropes import TropeExample, TROPE_EXAMPLES_TABLES, TROPES_TABLE, Trope, Title, TropeExample
from pydantic import TypeAdapter
from typing import Generator, Generic, TypeVar


@dataclass
class BaseTropesCRUD:
    name: str
    df: pd.DataFrame

    @classmethod
    def load_from_csv(cls, name: TROPE_EXAMPLES_TABLES | TROPES_TABLE):
        df = pd.read_csv(tvtropes_config.get_csv_file_path(name))
        return cls(df=df, name=name)

    def save_to_csv(self):
        self.df.to_csv(tvtropes_config.get_csv_file_path(self.name), index=True)

    @abstractmethod
    def batch_generator(self, batch_size: int, limit: int, offset: int, exclude_ids: list[str]) -> Generator[list,None, None]:
        raise NotImplementedError


class TropeExamplesCRUD(BaseTropesCRUD):
    def get_trope_examples_for_title_id(self, title_id: str) -> list[TropeExample]:
        """Returns a list of TropeExamples for a given title_id."""
        filtered_df = self.df[self.df["title_id"] == title_id]
        return TypeAdapter(list[TropeExample]).validate_python(filtered_df.to_dict(orient="records"))

    def get_titles_for_title_ids(self, title_ids: list[str]) -> list[str]:
        return self.df[self.df["title_id"].isin(title_ids)]["Title"].unique().tolist()
    

    def get_titles(self, limit: int = 10, offset: int = 0, exclude_ids: list[str] = []) -> list[Title]:
        # get unique titles
        filtered_df = self.df.drop_duplicates(subset=['title_id'])
        filtered_df = filtered_df[~filtered_df["title_id"].isin(exclude_ids)]
        return TypeAdapter(list[Title]).validate_python(filtered_df[offset:offset + limit].to_dict(orient="records"))
    
    def batch_generator(self, batch_size: int = 32, limit: int = 10, offset: int = 0, exclude_ids: list[str] = []) -> Generator[list[TropeExample], None, None]:
        filtered_df = self.df[~self.df["title_id"].isin(exclude_ids)]
        filtered_df = filtered_df.dropna(subset=["Example", "Title", "trope_id", "title_id"])
        filtered_df = filtered_df[offset:offset + limit]
        for i in range(0, len(filtered_df), batch_size):
            yield TypeAdapter(list[TropeExample]).validate_python(filtered_df[i:i + batch_size].to_dict(orient="records"))





class TropesCRUD(BaseTropesCRUD):
    def get_descriptions_for_trope_ids(self, trope_ids: list[str]) -> list[str]:
        return (
            self.df[self.df["trope_id"].isin(trope_ids)]["description"]
            .unique()
            .tolist()
        )

    def get_tropes_for_trope_ids(self, trope_ids: list[str]) -> list[Trope]:
        return [
            TypeAdapter(list[Trope]).validate_python({"name": self.name, **row})
            for _, row in self.df[self.df["trope_id"].isin(trope_ids)].iterrows()
        ]



# litTropesCRUD = TropeExamplesCRUD.load_from_csv('lit_tropes')
# goodreadsTropesCRUD = TropeExamplesCRUD.load_from_csv('lit_goodreads_match')

#TODO: add more tropes
# FilmTropesCRUD = TropeExamplesCRUD.load_from_csv('film_tropes')
# TvTropesCRUD = TropeExamplesCRUD.load_from_csv('tv_tropes')