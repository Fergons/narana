"""
This file contains functions for postprocessing the output CSV file
(combined_embeddings_with_clusters.csv). These functions operate solely on
the CSV outputs produced by clustering.py.
"""

import pandas as pd
from pathlib import Path


###############################################
# Function: Print Cluster Text Chunks
###############################################
def print_cluster_text_chunks(
    cluster_label,
    num_chunks=10,
    metadata_file=Path("data/books/embeddings/combined_embeddings_with_clusters.csv"),
    books_folder=Path("data/books"),
):
    """
    Loads combined_embeddings_with_clusters.csv and for each row belonging to the specified cluster,
    loads the corresponding text file from `books_folder` and extracts the chunk text using the
    'start_index' and 'end_index' values. It then prints up to `num_chunks` text chunks.
    """
    if not metadata_file.exists():
        print(f"Metadata file {metadata_file} not found.")
        return
    df = pd.read_csv(metadata_file)
    cluster_df = df[df["cluster"] == cluster_label]
    if cluster_df.empty:
        print(f"No chunks found for cluster {cluster_label}.")
        return
    printed = 0
    for idx, row in cluster_df.iterrows():
        book_id = row["book_id"]
        start_index = int(row["start_index"])
        end_index = int(row["end_index"])
        text_file = books_folder / f"{book_id}.txt"
        if not text_file.exists():
            print(f"Text file {text_file} not found. Skipping this row.")
            continue
        try:
            with open(text_file, "r", encoding="utf-8") as f:
                full_text = f.read()
        except Exception as e:
            print(f"Error reading {text_file}: {e}")
            continue
        chunk_text = full_text[start_index:end_index]
        print(
            f"--- Chunk from {book_id} (chunk_index={row['chunk_index']}) label={row['trope']} ---"
        )
        print(chunk_text)
        print("\n")
        printed += 1
        if printed >= num_chunks:
            break


###############################################
# Function: Compute Soft Cluster Labels from Trope Frequencies
###############################################
def compute_cluster_soft_labels(
    metadata_file=Path("data/books/embeddings/combined_embeddings_with_clusters.csv"),
):
    """
    Loads combined_embeddings_with_clusters.csv and computes a soft label for each cluster based on
    the frequency of 'trope' labels, along with the number of books per cluster and the number of
    chunks per book for each cluster.

    Returns a dictionary where each key is a cluster label and the value is a dictionary with:
        - 'soft_labels': a dictionary mapping trope names to their relative frequency (as proportions),
        - 'num_books': the total number of unique books in the cluster,
        - 'chunks_per_book': a dictionary mapping each book_id to its number of chunks in the cluster.
    """
    if not metadata_file.exists():
        print(f"Metadata file {metadata_file} not found.")
        return {}

    df = pd.read_csv(metadata_file)
    cluster_info = {}

    # Group by cluster and compute the required information
    for cluster, group in df.groupby("cluster"):
        # Compute soft labels for trope frequencies
        trope_counts = group["trope"].value_counts()
        soft_labels = (trope_counts / trope_counts.sum()).to_dict()

        # Compute number of unique books in the cluster
        num_books = group["book_id"].nunique()

        # Compute number of chunks per book in the cluster
        chunks_per_book = group["book_id"].value_counts().to_dict()

        cluster_info[cluster] = {
            "soft_labels": soft_labels,
            "num_books": num_books,
            "chunks_per_book": chunks_per_book,
        }

    return cluster_info


###############################################
# Function: Save Random Chunks for Each Cluster
###############################################
def save_random_chunks_for_each_cluster(
    cluster_labels,
    num_chunks=20,
    metadata_file=Path("data/books/embeddings/combined_embeddings_with_clusters.csv"),
    books_folder=Path("data/books"),
    output_folder=Path("notebook/clusters/chunks"),
):
    """
    Loads combined_embeddings_with_clusters.csv and for each cluster, randomly samples up to `num_chunks` rows.
    For each sampled row, loads the corresponding text chunk from the book text file (using start_index and end_index),
    and saves these chunks to a file named "cluster_<cluster>.txt" in the output_folder.
    """
    if not metadata_file.exists():
        print(f"Metadata file {metadata_file} not found.")
        return
    df = pd.read_csv(metadata_file)

    # Create the output folder if it doesn't exist.
    output_folder.mkdir(parents=True, exist_ok=True)

    # Group by cluster and process each group.
    for cluster, group in df.groupby("cluster"):
        if cluster not in cluster_labels:
            continue
        # Sample up to num_chunks random rows from the group.
        sampled = group.sample(n=min(num_chunks, len(group)), random_state=42)
        chunks_list = []
        for idx, row in sampled.iterrows():

            book_id = row["book_id"]
            start_index = int(row["start_index"])
            end_index = int(row["end_index"])
            text_file = books_folder / f"{book_id}.txt"
            if not text_file.exists():
                print(f"Text file {text_file} not found for book {book_id}. Skipping.")
                continue
            try:
                with open(text_file, "r", encoding="utf-8") as f:
                    full_text = f.read()
            except Exception as e:
                print(f"Error reading {text_file}: {e}")
                continue
            # Extract the chunk from the full text.
            chunk_text = full_text[start_index:end_index]
            header = f"--- Chunk from {book_id} (chunk_index={row['chunk_index']}) label={row.get('trope', 'Unknown')} ---\n"
            chunks_list.append(header + chunk_text + "\n\n")
        # If any chunks were found, save them to a text file for this cluster.
        if chunks_list:
            output_file = output_folder / f"cluster_{cluster}.txt"
            with open(output_file, "w", encoding="utf-8") as out_f:
                out_f.write("\n".join(chunks_list))
            print(
                f"Saved {len(chunks_list)} chunks for cluster {cluster} to {output_file}"
            )


###############################################
# Function: Count Estimated Number of Tokens per Book
###############################################
def count_tokens_per_book(
    metadata_file=Path("data/books/embeddings/combined_embeddings_with_clusters.csv"),
    chunk_length=512,
):
    """
    Loads the combined_embeddings_with_clusters.csv file and estimates the total number
    of tokens per book by assuming each chunk contains approximately `chunk_length` tokens.
    Returns a dictionary mapping each book_id to its estimated token count.
    """
    if not metadata_file.exists():
        print(f"Metadata file {metadata_file} not found.")
        return {}
    df = pd.read_csv(metadata_file)
    # Group by book_id: each row represents one chunk.
    chunks_per_book = df.groupby("book_id")
    df = pd.DataFrame({"num_chunks": chunks_per_book.size()})
    df["tokens_per_book"] = df * chunk_length
    return df


###############################################
# Main Routine for Postprocessing
###############################################
if __name__ == "__main__":
    # Example usage: Uncomment to test functions individually.
    cluster_stats = compute_cluster_soft_labels()
    interesting_clusters = []
    for cluster, stats in cluster_stats.items():
        if max(list(stats["soft_labels"].values())) < 0.7:
            interesting_clusters.append(cluster)
            print(f"Cluster {cluster}:")
            print(f"  Number of books: {stats['num_books']}")
            print(f"  Chunks per book: {stats['chunks_per_book']}")
            for trope, score in stats["soft_labels"].items():
                print(f"  {trope}: {score:.2f}")

    print(interesting_clusters)

    # save_random_chunks_for_each_cluster(num_chunks=20)
    # Example usage: Count and print estimated token counts per book.
    token_counts = count_tokens_per_book()
    print("Estimated token counts per book (based on 512 tokens per chunk):")
    print(token_counts.head())
    # dexribe in thousands
    pd.set_option("display.float_format", lambda x: "%.2f" % x)
    print(token_counts.describe())

    save_random_chunks_for_each_cluster(interesting_clusters, num_chunks=20)
