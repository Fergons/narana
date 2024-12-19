from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import os
import tqdm
from pathlib import Path
from .dataset import BookCompanion
import re

def epub_to_txt(epub_path, txt_output_path):
    # Load the EPUB book
    book = epub.read_epub(epub_path)
    
    # Collect all text content from the book
    full_text = []

    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            # Parse the content with BeautifulSoup
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            soup.prettify(formatter=None)
            spans = soup.find_all('span')
            for span in spans:
                span.replace_with(span.text)

            # find all paragraphs
            # extract text from paragraphs
            para_texts = [soup.get_text(strip=True, separator=' ')]
            para_texts = [p.strip() for p in para_texts if p.strip()]
            text = '\n'.join(para_texts)
            
            clean_text = re.sub(r'\n{2,}', '\n', text)
            full_text.append(clean_text)

    # Combine all text segments into a single string
    complete_text = '\n\n'.join(full_text)

    # Write the complete text to a TXT file
    with open(txt_output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(complete_text)

    print(f"EPUB converted to TXT successfully: {txt_output_path}")

# Example usage
if __name__ == "__main__":
    
    epubs_dir = Path(BookCompanion.DATASET_PATH)
    for epub_file in tqdm.tqdm(epubs_dir.glob("*.epub")):
        txt_output_path = epub_file.with_suffix(".txt")
        try:
            epub_to_txt(epub_file, txt_output_path)
        except Exception as e:
            print(f"Failed to convert {epub_file}: {e}")
        

