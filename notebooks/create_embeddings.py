import os
import re
import numpy as np
import pandas as pd
import nltk
from pathlib import Path
from FlagEmbedding import BGEM3FlagModel
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

# Download NLTK sentence tokenizer (if not already)
nltk.download('punkt')

# Initialize BGEM3 model (using FP16 for speed if desired)
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
tokenizer = model.tokenizer
BATCH_SIZE=64

# Parameters
MAX_TOKENS = 512          # maximum tokens per chunk (without special tokens)
OVERLAP_TOKENS = 64       # number of tokens to overlap between chunks


def get_embedded_book_ids(dir="data/books/embeddings"):
    if not Path(dir).exists():
        return set()
    return set([f.stem.split("_")[0] for f in Path(dir).iterdir() if f.is_file() and f.suffix == ".npy"])



def epub_to_text(epub_path):
    """
    Reads an EPUB file and extracts plain text from each document item,
    removing extra whitespaces.
    """
    try:
        book = epub.read_epub(str(epub_path))
    except Exception as e:
        print(f"Error reading EPUB {epub_path}: {e}")
        return ""
    
    text = ""
    # Loop through all document items (usually HTML or XHTML)
    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            try:
                soup = BeautifulSoup(item.get_content(), features="html.parser")
                item_text = soup.get_text(separator="\n")
                text += item_text + "\n"
            except Exception as e:
                print(f"Error parsing an item in {epub_path}: {e}")
    
    # Remove extra whitespaces: replace 2 or more whitespace characters with a single space.
    text = re.sub(r'\s+', ' ', text)
    return text


def chunk_text_with_overlap(text, tokenizer, max_tokens=512, overlap_tokens=64):
    """
    Splits the text into chunks based on sentence boundaries while ensuring an overlapping window between chunks.
    In addition to returning the chunk texts, it also returns metadata with the start and end character indices 
    (as found in the original text) for each chunk.

    The method uses NLTK's PunktSentenceTokenizer with its span_tokenize() method to obtain sentence
    boundaries (character offsets). Then, it tokenizes each sentence with the model's tokenizer (without adding 
    special tokens) and accumulates sentences until adding another sentence would exceed max_tokens. When a chunk 
    is complete, the function "backs up" by selecting as many trailing sentences as needed (by token count) to 
    reach at least overlap_tokens. These sentences are prepended to the next chunk.

    Returns:
        chunks (list of str): List of text chunks.
        metadata (list of dict): Each dict contains:
            - 'chunk_index': integer index of the chunk
            - 'start_index': start character index in the original text
            - 'end_index': end character index in the original text
    """
    # Use NLTK's pre-trained Punkt tokenizer to get sentence spans.
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
    sentence_spans = list(sent_detector.span_tokenize(text))
    
    chunks = []
    metadata = []
    current_chunk_spans = []   # list of (start, end) for sentences in current chunk
    current_token_count = 0    # accumulated token count for the current chunk

    for (start, end) in sentence_spans:
        sentence = text[start:end].strip()
        if not sentence:
            continue
        sentence_tokens = tokenizer(sentence, add_special_tokens=False)['input_ids']
        num_tokens = len(sentence_tokens)
        
        # Check if adding this sentence would exceed max_tokens (if we already have something in the chunk)
        if current_chunk_spans and (current_token_count + num_tokens > max_tokens):
            # Finalize the current chunk
            chunk_start = current_chunk_spans[0][0]
            chunk_end = current_chunk_spans[-1][1]
            chunk_text = text[chunk_start:chunk_end]
            chunks.append(chunk_text)
            metadata.append({
                'chunk_index': len(chunks) - 1,
                'start_index': chunk_start,
                'end_index': chunk_end
            })
            
            # Determine the overlapping sentences: work backwards until reaching at least overlap_tokens
            overlap_spans = []
            overlap_token_count = 0
            for s, e in reversed(current_chunk_spans):
                sent_text = text[s:e].strip()
                sent_tokens = tokenizer(sent_text, add_special_tokens=False)['input_ids']
                overlap_spans.insert(0, (s, e))  # prepend to maintain original order
                overlap_token_count += len(sent_tokens)
                if overlap_token_count >= overlap_tokens:
                    break
            # Start the new chunk with these overlapping sentences.
            current_chunk_spans = overlap_spans.copy()
            current_token_count = 0
            for s, e in current_chunk_spans:
                sent_text = text[s:e].strip()
                current_token_count += len(tokenizer(sent_text, add_special_tokens=False)['input_ids'])
        
        # Append the current sentence to the chunk.
        current_chunk_spans.append((start, end))
        current_token_count += num_tokens

    # Add any remaining sentences as the final chunk.
    if current_chunk_spans:
        chunk_start = current_chunk_spans[0][0]
        chunk_end = current_chunk_spans[-1][1]
        chunk_text = text[chunk_start:chunk_end]
        chunks.append(chunk_text)
        metadata.append({
            'chunk_index': len(chunks) - 1,
            'start_index': chunk_start,
            'end_index': chunk_end
        })
    
    return chunks, metadata


# Directory where your book files are stored (EPUBs in this example)
books_dir = Path("data/books")

# (Optionally) load a CSV listing downloaded book IDs.
# If not available, list all .txt files in the directory.
books_csv = Path("notebooks/books_downloaded.csv")
if books_csv.exists():
    df_books = pd.read_csv(books_csv)
    book_ids = df_books['title_id'].tolist()
else:
    # Assuming the stem of each file is the book ID (modify if needed)
    book_ids = [f.stem for f in books_dir.iterdir() if f.is_file() and f.suffix == ".txt"]

print(f"Found {len(book_ids)} books.")

# Create a directory for saving embeddings batches.
embeddings_dir = Path("data/books/embeddings")
embeddings_dir.mkdir(exist_ok=True)

for book_id in book_ids:
    book_file = books_dir / f"{book_id}.epub"
    if not book_file.exists():
        print(f"Book {book_id} not found, skipping.")
        continue
    if book_id in get_embedded_book_ids():
        print(f"Book {book_id} already embedded, skipping.")
        continue
    try:
        text = epub_to_text(book_file)
        if not text.strip():
            print(f"No text found in {book_id}")
            continue
    except Exception as e:
        print(f"Error reading {book_id}: {e}")
        continue

    # Save the processed text as a .txt file in the data/books folder.
    text_file = books_dir / f"{book_id}.txt"
    try:
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved processed text for {book_id} to {text_file}")
    except Exception as e:
        print(f"Error writing text file for {book_id}: {e}")

    # Chunk the text using our overlapping-chunk function.
    chunks, chunk_metadata = chunk_text_with_overlap(text, tokenizer, max_tokens=MAX_TOKENS, overlap_tokens=OVERLAP_TOKENS)
    if not chunks:
        print(f"No chunks generated for {book_id}")
        continue
    # Print one of the chunks for inspection.
    print(chunks[len(chunks) // 2])

    # Encode the chunks using the model. We request dense embeddings.
    try:
        vectors = model.encode(chunks, max_length=1024, batch_size=32, return_dense=True)
    except Exception as e:
        print(f"Error encoding {book_id}: {e}")
        continue

    # Expect dense embeddings in the 'dense_vecs' key (each entry is a numpy array)
    dense_vecs = vectors.get('dense_vecs', None)
    if dense_vecs is None:
        print(f"No dense embeddings for {book_id}")
        continue

    # Batch saving: Save embeddings and metadata for each book as soon as they are computed.
    try:
        embeddings_array = np.stack(dense_vecs)  # shape: (num_chunks, embedding_dim)
    except Exception as e:
        print(f"Error stacking embeddings for {book_id}: {e}")
        continue

    # Save the embeddings for this book
    embeddings_file = embeddings_dir / f"{book_id}_embeddings.npy"
    np.save(embeddings_file, embeddings_array)
    
    # Add the book_id to each metadata entry and save metadata as CSV.
    for meta in chunk_metadata:
        meta['book_id'] = book_id
    metadata_file = embeddings_dir / f"{book_id}_metadata.csv"
    pd.DataFrame(chunk_metadata).to_csv(metadata_file, index=False)
    
    print(f"Processed and saved book {book_id}: {len(chunks)} chunks.")

print("Batch saving complete. Check the 'data/books/embeddings' folder for output files.")

