
import data.tvtropes.dataset as dataset
from logging import getLogger
logger = getLogger(__name__)


def tokenize_dataset(dataset: dataset.TVTropesDataset, model_name: str = "dunzhang/stella_en_1.5B_v5") -> dataset.TVTropesDataset:
    """
    Tokenize only the tropes descriptions and examples.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name, trust_remote_code=True).cuda()
    
    for attr in ["film_tropes", "lit_tropes", "tv_tropes", "tropes"]:
        logger.debug(f"Tokenizing {attr}")
        df = getattr(dataset, attr)
        column_name = "Description" if attr == "tropes" else "Example"
        df[f"Tokenized"] = model.encode(df[column_name])
        df = df[[f"Tokenized"]]
        df.save(f"{attr}_tokenized_{model_name}.csv")
        logger.debug(f"Saved {attr} to {attr}_tokenized.csv")
    return df


if __name__ == "__main__":
    data = dataset.TVTropesDataset.from_csv_files()
    tokenize_dataset(data)