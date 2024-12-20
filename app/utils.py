from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter, retry_if_result
import logging
from httpx import AsyncClient, Response
from anyio import open_file
import orjson
from typing import AsyncIterable, Iterable
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

basic_config = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




async def retry_fetch(session: AsyncClient, url: str, **kwargs) -> Response:
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential_jitter(max=30), retry=retry_if_result(lambda res: res.is_server_error)):
        with attempt:
            return await session.get(url, **kwargs)
        

async def async_load_jsonl(path: str) -> AsyncIterable[dict]:
    async with await open_file(path, mode='r') as f:
        async for line in f:
           yield orjson.loads(line)

def load_jsonl(path: str) -> list:
    with open(path, mode='r') as f:
        return [orjson.loads(line) for line in f]
        

async def async_dump_jsonl(path: str, data: Iterable[dict]):
    async with await open_file(path, mode='w') as f:
        for item in data:
            await f.write(orjson.dumps(item)+b'\n')


def epub_to_documents(path) -> list[str]:
    # Load the EPUB book
    book = epub.read_epub(path)
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
            docs.append(text)   
    return docs


def word_chunk(text, chunk_size, overlap):
    words = text.split(' ')
    for i in range(0, len(words), chunk_size-overlap):
        chunk = words[i:i+chunk_size]
        if len(chunk) < overlap:
            continue
        yield ' '.join(chunk)
    

 