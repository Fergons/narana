from bs4 import BeautifulSoup
import re
from ebooklib import epub, ITEM_DOCUMENT
import logging
import os

logger = logging.getLogger(__name__)

def epub_to_documents(path) -> list[str]:
    # Load the EPUB book
    try:
        book = epub.read_epub(path)
    except Exception as e:
        logger.error(f"Error loading EPUB file {path}: {e}")
        os.remove(path)
        return []
    
    docs = []
    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), features="xml")
            soup.prettify(formatter=None)
            exclude_tags = {'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
            spans = soup.find_all(lambda tag: tag.name not in exclude_tags if tag.name else False)
            for span in spans:
                span.unwrap()
            soup = BeautifulSoup(str(soup), features="xml")
            para_texts = [soup.get_text(strip=True, separator=' \n')]
            text = '\n'.join(para_texts)
            docs.append(re.sub(r'\s+', ' ', text))   
    return docs

def word_chunk(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into chunks of words with overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Number of words per chunk
        overlap: Number of words to overlap between chunks
        
    Returns:
        List of text chunks
    """
    words = text.split(' ')
    for i in range(0, len(words), chunk_size-overlap):
        chunk = words[i:i+chunk_size]
        if len(chunk) < overlap:
            continue
        yield ' '.join(chunk) 