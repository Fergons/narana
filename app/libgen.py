from bs4 import BeautifulSoup
import httpx 
import asyncio
from app.models.tvtropes import LibgenSearchResult, Title
from app.crud import goodreadsTropesCRUD
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter, retry_if_result
import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio.streams.file import FileWriteStream
import re

import orjson
from app.config import dataset_config
import logging


basic_config = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_error_status_code(response: httpx.Response) -> None:
    logger.info(f"Status code: {response.status_code}")
    return response.status_code > 500

async def retry_fetch(session: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_exponential_jitter(max=30), retry=retry_if_result(is_error_status_code)):
        with attempt:
            return await session.get(url, **kwargs)

async def search(session: httpx.AsyncClient,*, q: str, criteria: str = '', language: str = 'English', format: str = 'epub', resolve_downloads: bool = False) -> LibgenSearchResult:
    if q is None:
        raise ValueError("q is required")
    
    url = 'https://libgen.is/fiction/'
    params = {
        'q': q,
        'criteria': criteria,
        'language': language,
        'format': format
    }
    
    response = await retry_fetch(session, url, params=params)
    if response.status_code != 200:
        raise ValueError(f"Libgen failed to return results for {q}.\nStatus code: {response.status_code}.\nResponse: {response.text}")
      
    data = extract_table_data(response.content)
    for item in data:
        item['language'] = language
        item['format'] = format
        item['download_urls'] = await resolve_download_links(session, item['download_urls'])

    return data


def extract_table_data(html_content: str | bytes) -> list[dict[str, str]]:
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the table and extract rows
    table = soup.find('table', {'class': 'catalog'})
    if not table:
        return []
    
    extracted_data = []
    rows = table.find_all('tr')[1:]  

    for row in rows:
        authors = []
        cells = row.find_all('td')
        authors = extract_authors(cells[0])
        title = extract_title(cells[2])
        download_links = extract_download_page_links(cells[5])
        extracted_data.append({
            'authors': authors,
            'title': title,
            'download_urls': download_links
        })
    return extracted_data

async def resolve_download_links(session: httpx.AsyncClient, download_links: list[str]) -> list[str]:
    resolved_links = []
    tasks = []
    for link in download_links:
        tasks.append(retry_fetch(session, link))
    responses = await asyncio.gather(*tasks)
    for response in responses:
        if response.status_code == 200:
            resolved_links.append(extract_download_link(response.content))
    return resolved_links

def extract_download_link(html_content: str | bytes) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    link = soup.find('a', href=True, text='GET')
    if link:
        if 'http' not in link['href']:
            return f'https://libgen.li/{link["href"]}'
        return link['href']
    
        
def extract_authors(td: BeautifulSoup) -> list[str]:
    authors = []
    authors_list = td.find_all('a')
    for author in authors_list:
        name = author.text.strip()
        authors.append(name)
    return authors

def extract_title(td: BeautifulSoup) -> str:
    title = td.find('a').text.strip()
    return title

def extract_download_page_links(td: BeautifulSoup) -> list[str]:
    links = []
    for link in td.find_all('a'):
        links.append(link['href'])
    return links



async def produce_search_results_for_title(session: httpx.AsyncClient, title: Title, send_stream: MemoryObjectSendStream):
    # substitute uppercase letters before that letter followed by a space
    processed_title = re.sub(r'([A-Z])', r' \1', title.title).strip()
    results = await search(session, q=f'{processed_title} {title.author if title.author else ""}')
    await send_stream.send({"title_id": title.title_id, 'hits': results})
    await send_stream.aclose()

async def save_search_results(file_stream: FileWriteStream, results_stream: MemoryObjectReceiveStream):
    async with results_stream:
        async for result in results_stream:
            logger.info(f"Saving {result}")
            await file_stream.send(orjson.dumps(result)+b'\n')  
            

async def find_tvtropes_titles_on_libgen(titles: list[Title]):
    csv_path = dataset_config.csv_dir / 'libgen.jsonl'
    send_stream, receive_stream = anyio.create_memory_object_stream[dict]()
    async with httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=2, max_connections=5, keepalive_expiry=5.0)) as session:
        async with await FileWriteStream.from_path(csv_path, append=True) as fstream:
            try: 
                async with anyio.create_task_group() as tg:
                    tg.start_soon(save_search_results, fstream, receive_stream)
                    async with send_stream:
                        for title in titles:
                            tg.start_soon(produce_search_results_for_title, session, title, send_stream.clone())
            except* ValueError as e:
                logger.error(e)
            
            except* httpx.TimeoutException as e:
                logger.error(e)

            except* httpx.RequestError as e:
                logger.error(e)
            
                    

async def main():
    
    exclude_ids = set()
    for _ in range(1000):
        async with await anyio.open_file(dataset_config.csv_dir / 'libgen.jsonl', mode='r') as f:
            async for line in f:
                item = orjson.loads(line)
                exclude_ids.add(item['title_id'])
        titles = goodreadsTropesCRUD.get_titles(limit=10, exclude_ids=list(exclude_ids))
        if len(titles) == 0:
            break
        await find_tvtropes_titles_on_libgen(titles)
        

    
if __name__ == "__main__":
    anyio.run(main)