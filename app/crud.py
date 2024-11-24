import pandas as pd
from dataclasses import dataclass
from .config import dataset_config
from .models.tvtropes import TropeExample, TROPE_EXAMPLES_TABLES, TROPES_TABLE, Trope, Title
from pydantic import TypeAdapter, AliasPath



@dataclass
class BaseTropesCRUD:
    name: TROPE_EXAMPLES_TABLES | TROPES_TABLE
    df: pd.DataFrame

    @classmethod
    def load_from_csv(cls, name: TROPE_EXAMPLES_TABLES | TROPES_TABLE):
        df = pd.read_csv(dataset_config.get_csv_file_path(name))
        return cls(name=name, df=df)

    def save_to_csv(self):
        self.df.to_csv(dataset_config.get_csv_file_path(self.name), index=True)


class TropeExamplesCRUD(BaseTropesCRUD):
    def get_trope_examples_for_title_id(self, title_id: str) -> list[TropeExample]:
        """Returns a list of TropeExamples for a given title_id."""
        filtered_df = self.df[self.df["title_id"] == title_id]
        return [
            TypeAdapter(TropeExample).validate_python({"name": self.name, **row})
            for _, row in filtered_df.iterrows()
        ]

    def get_titles_for_title_ids(self, title_ids: list[str]) -> list[str]:
        return self.df[self.df["title_id"].isin(title_ids)]["title"].unique().tolist()
    

    def get_titles(self, limit: int = 10, offset: int = 0, exclude_ids: list[str] = []) -> list[Title]:
        # get unique titles
        filtered_df = self.df.drop_duplicates(subset=['title_id'])
        filtered_df = filtered_df[~filtered_df["title_id"].isin(exclude_ids)]
        return TypeAdapter(list[Title]).validate_python(filtered_df[offset:offset + limit].to_dict(orient="records"))
       



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



litTropesCRUD = TropeExamplesCRUD.load_from_csv('lit_tropes')
goodreadsTropesCRUD = TropeExamplesCRUD.load_from_csv('lit_goodreads_match')

#TODO: add more tropes
# FilmTropesCRUD = TropeExamplesCRUD.load_from_csv('film_tropes')
# TvTropesCRUD = TropeExamplesCRUD.load_from_csv('tv_tropes')