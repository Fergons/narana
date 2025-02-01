import numpy as np
import matplotlib.pyplot as plt
import umap
from scipy.cluster.hierarchy import dendrogram, linkage
import pandas as pd
from pathlib import Path
from matplotlib.patches import Circle
import hdbscan

###############################################
# Data Loading & Merging Functions
###############################################

def load_embeddings_and_metadata(embeddings_dir=Path("data/books/embeddings")):
    """
    Loads all *_embeddings.npy files and corresponding metadata CSVs from embeddings_dir.
    Returns the stacked embeddings and concatenated metadata.
    """
    embedding_files = sorted(embeddings_dir.glob("*_embeddings.npy"))
    metadata_files = {f.stem.split("_")[0]: f for f in embeddings_dir.glob("*_metadata.csv")}
    
    all_embeddings = []
    metadata_list = []
    for emb_file in embedding_files:
        # Extract book_id from filename (assumes format "<bookid>_embeddings.npy")
        book_id = emb_file.stem.split("_")[0]
        emb = np.load(emb_file)
        all_embeddings.append(emb)
        meta_file = metadata_files.get(book_id)
        if meta_file is not None:
            meta_df = pd.read_csv(meta_file)
            # Add book_id column.
            meta_df["book_id"] = book_id
            metadata_list.append(meta_df)
    
    embeddings = np.vstack(all_embeddings)
    metadata = pd.concat(metadata_list, ignore_index=True)
    print(f"Loaded embeddings with shape: {embeddings.shape}")
    return embeddings, metadata

def merge_genre_data(metadata):
    """
    Loads genre information from lit_goodreads_genre_filtered.csv and merges it into metadata.
    """
    genre_df = pd.read_csv("notebooks/lit_goodreads_genre_filtered.csv")
    # Keep first occurrence per book_id.
    genre_df = genre_df.drop_duplicates(subset=["title_id"])
    # Rename to match the metadata.
    genre_df.rename(columns={"title_id": "book_id", "Trope": "trope"}, inplace=True)
    merged_metadata = pd.merge(metadata, genre_df[["book_id", "trope"]], on="book_id", how="left")
    # Fill missing values.
    merged_metadata["trope"] = merged_metadata["trope"].fillna("Unknown")
    print(f"Merged metadata now has {merged_metadata['trope'].nunique()} unique genres.")
    return merged_metadata

###############################################
# UMAP & Clustering Functions
###############################################

def run_umap(embeddings, n_neighbors=15, n_components=5):
    """
    Runs UMAP dimensionality reduction on the embeddings.
    """
    umap_vis = umap.UMAP(n_neighbors=n_neighbors, n_components=n_components, metric='euclidean')
    embeddings_umap = umap_vis.fit_transform(embeddings)
    print(f"UMAP (visualization) reduced shape: {embeddings_umap.shape}")
    return embeddings_umap


def run_clustering(embeddings_umap, merged_metadata, embeddings_dir=Path("data/books/embeddings")):
    """
    Runs clustering (using HDBSCAN) on the UMAP projection,
    updates merged_metadata with cluster labels, and saves the result.
    """
    # Use HDBSCAN to produce cluster labels without computing the full pairwise distance matrix.
    clusterer = hdbscan.HDBSCAN(min_cluster_size=50, metric='euclidean')
    cluster_labels = clusterer.fit_predict(embeddings_umap)
    # Exclude noise (-1) when counting clusters.
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)

    print(f"Found {n_clusters} clusters using HDBSCAN")
    
    merged_metadata['cluster'] = cluster_labels
    combined_meta_file = embeddings_dir / "combined_embeddings_with_clusters.csv"
    merged_metadata.to_csv(combined_meta_file, index=False)
    print(f"Saved clustering results to {combined_meta_file}")
    return merged_metadata

###############################################
# Visualization Functions
###############################################

def plot_umap(embeddings_umap, merged_metadata):
    """
    Plots the UMAP scatter with points colored by genre and annotates each cluster.
    Also draws circles around cluster boundaries.
    """
    unique_tropes = sorted(merged_metadata["trope"].unique())
    n_tropes = len(unique_tropes)
    colors_list = plt.get_cmap("tab20", n_tropes).colors
    color_map = {trope: colors_list[i] for i, trope in enumerate(unique_tropes)}
    
    point_colors = [color_map[gt] for gt in merged_metadata["trope"]]
    
    plt.figure(figsize=(10, 8))
    plt.scatter(embeddings_umap[:, 0], embeddings_umap[:, 1], c=point_colors, s=5, alpha=0.7)
    plt.title("UMAP Projection of Chunk Embeddings (Colored by Genre Trope)")
    plt.xlabel("UMAP 1")
    plt.ylabel("UMAP 2")
    
    # Create and display a legend for genre tropes.
    patches = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color_map[t],
                            markersize=8, label=t) for t in unique_tropes]
    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc='upper left', title="Genre Trope")
    plt.tight_layout()
    plt.savefig("umap_projection_by_genre.png")
    
    # Annotate clusters on UMAP.
    clusters = merged_metadata['cluster'].unique()
    for cluster in clusters:
        cluster_mask = merged_metadata['cluster'] == cluster
        # Calculate the centroid (mean) of points in the cluster.
        centroid = embeddings_umap[cluster_mask].mean(axis=0)
        books_in_cluster = merged_metadata.loc[cluster_mask, 'book_id'].unique()
        if len(books_in_cluster) <= 3:
            label = f"Cluster {cluster}: " + ", ".join(books_in_cluster)
        else:
            label = f"Cluster {cluster}: {len(books_in_cluster)} books"
        plt.annotate(label, 
                     xy=centroid, 
                     xytext=(centroid[0] + 0.5, centroid[1] + 0.5),
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     fontsize=8,
                     bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
        # Draw a circle around the cluster's boundaries.
        cluster_points = embeddings_umap[cluster_mask]
        distances = np.linalg.norm(cluster_points - centroid, axis=1)
        radius = distances.max() + 0.5
        circle = Circle(centroid, radius, fill=False, edgecolor='blue', linewidth=1.5, linestyle='--')
        plt.gca().add_patch(circle)
    
    # Print cluster summary.
    cluster_summary = merged_metadata.groupby('cluster')['book_id'].nunique().reset_index().rename(columns={'book_id': 'num_books'})
    print("Cluster Summary:")
    print(cluster_summary)
    plt.show()

def plot_dendrogram(embeddings_umap, subsample_size=2000):
    """
    For visualization purposes, subsamples the UMAP embeddings to construct an annotated dendrogram.
    """
    if embeddings_umap.shape[0] > subsample_size:
        sub_idx = np.random.choice(embeddings_umap.shape[0], size=subsample_size, replace=False)
        dendro_data = embeddings_umap[sub_idx].astype(np.float16)
    else:
        dendro_data = embeddings_umap.astype(np.float16)
    
    plt.figure(figsize=(12, 6))
    ddata = dendrogram(linkage(dendro_data, method='ward'),
                       truncate_mode='lastp', p=20, show_leaf_counts=True)
    plt.title("Hierarchical Clustering Dendrogram (Subsampled)")
    plt.xlabel("Cluster Size")
    plt.ylabel("Distance")
    for i, d in zip(ddata['icoord'], ddata['dcoord']):
        x = 0.5 * sum(i[1:3])
        y = d[1]
        plt.plot(x, y, 'ro')
        plt.annotate(f"{y:.2f}", (x, y),
                     textcoords="offset points",
                     xytext=(0, -10),
                     ha='center',
                     fontsize=8,
                     color="red")
    plt.savefig("dendrogram_annotated.png")
    plt.show()

###############################################
# Main
###############################################
if __name__ == "__main__":
    embeddings, metadata = load_embeddings_and_metadata()
    merged_metadata = merge_genre_data(metadata)
    embeddings_umap = run_umap(embeddings)
    merged_metadata = run_clustering(embeddings_umap, merged_metadata)
    plot_umap(embeddings_umap, merged_metadata)
    plot_dendrogram(embeddings_umap)

