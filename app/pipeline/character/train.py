"""Training script for character identification using BookCompanion dataset"""

from pathlib import Path
import pandas as pd
from typing import Dict, List, Tuple

from adalflow import ModelClient, Trainer
from adalflow.core.types import Document


from app.data.bookcompanion.dataset import BookCompanion
from app.pipeline.character.adal import CharacterIdentificationAdal, CharacterIdentificationSample




def load_datasets() -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Load and prepare datasets from BookCompanion"""

    # Load BookCompanion data
    dataset = BookCompanion.load_from_csv()
    # Get books with both character lists and text files

    valid_books = dataset.book_list[
        (dataset.book_list["scraped_character_list"] == True)
        & (dataset.book_list["text_file_path"].notna())
    ]
  
    # Prepare training samples
    samples = []
    for _, book in valid_books.iterrows():
        try:
            # Load book text
            with open(book["text_file_path"], "r", encoding="utf-8") as f:
                text = f.read()

            # Get character list
            characters = dataset.get_character_list_for_character_list_url(
                book["character_list_url"]
            )

            # Create training sample
            sample = CharacterIdentificationSample(
                document=Document(text=text, meta_data={"title": book["title"]}),
                id=book["title"],
                ground_truth_characters={

                    f"{char['first_name'] if char['first_name'] != 'nan' else ''} {char['last_name'] if char['last_name'] != 'nan' else ''}".strip(): char[
                        "description"
                    ].strip()
                    for char in characters
                },
            )
            samples.append(sample)


        except Exception as e:
            print(f"Error loading {book['title']}: {e}")
            continue

    # Split into train/val/test (80/10/10)
    n = len(samples)
    train_size = int(0.8 * n)
    val_size = int(0.1 * n)

    train = samples[:train_size]
    val = samples[train_size : train_size + val_size]
    test = samples[train_size + val_size :]

    return train, val, test


def train(
    *,
    model_client: ModelClient,
    model_kwargs: Dict,
    text_splitter_config: Dict,
    train_batch_size: int = 4,
    raw_shots: int = 0,
    bootstrap_shots: int = 1,
    max_steps: int = 12,
    num_workers: int = 4,
    strategy: str = "constrained",
    optimization_order: str = "sequential",
    debug: bool = False,
):
    """Train character identification pipeline"""

    # Initialize AdalComponent
    adal_component = CharacterIdentificationAdal(
        model_client=model_client,
        model_kwargs=model_kwargs,
        text_splitter_config=text_splitter_config,
        text_optimizer_model_config={"model_client": model_client, "model_kwargs": model_kwargs},
        backward_engine_model_config={"model_client": model_client, "model_kwargs": model_kwargs},
        teacher_model_config={"model_client": model_client, "model_kwargs": model_kwargs},
    )

    # Initialize trainer
    trainer = Trainer(
        train_batch_size=train_batch_size,
        adaltask=adal_component,
        strategy=strategy,
        max_steps=max_steps,
        num_workers=num_workers,
        raw_shots=raw_shots,
        bootstrap_shots=bootstrap_shots,
        debug=debug,
        weighted_sampling=True,
        optimization_order=optimization_order,
        exclude_input_fields_from_bootstrap_demos=True,
    )

    # Load datasets
    train_dataset, val_dataset, test_dataset = load_datasets()

    # Train
    trainer.fit(
        train_dataset=train_dataset,
        val_dataset=test_dataset,
        debug=debug,
    )


if __name__ == "__main__":
    import argparse
    from app.pipeline.character.config import character_identification_config


    parser = argparse.ArgumentParser()
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--max_steps", type=int, default=12)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    train(
        **character_identification_config,
        train_batch_size=args.batch_size,
        max_steps=args.max_steps,
        debug=args.debug,
    )
