from bs4 import BeautifulSoup
import httpx
import asyncio
from app.models.tvtropes import LibgenSearchResult, Title
from app.crud.tvtropes import TropeExamplesCRUD
from app.utils.file import retry_fetch
import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio.streams.file import FileWriteStream
from utils.string import camel_to_string

import orjson
from app.config import settings
import logging

from app.utils.file import  async_load_jsonl
from tqdm import tqdm
from pathlib import Path

from pydantic import TypeAdapter

from dotenv import dotenv_values

import argparse


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

environ = dotenv_values(".env")


async def search(
    session: httpx.AsyncClient,
    *,
    q: str,
    criteria: str = "",
    language: str = "English",
    format: str = "epub",
    resolve_downloads: bool = False,
) -> LibgenSearchResult:
    if q is None:
        raise ValueError("q is required")

    url = "https://libgen.is/fiction/"
    params = {"q": q, "criteria": criteria, "language": language, "format": format}

    response = await retry_fetch(session, url, params=params)
    response.raise_for_status()

    data = extract_table_data(response.content)
    for item in data:
        item["language"] = language
        item["format"] = format
        if resolve_downloads:
            item["download_urls"] = await resolve_download_links(
                session, item["download_urls"]
            )

    return data


def extract_table_data(html_content: str | bytes) -> list[dict[str, str]]:
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the table and extract rows
    table = soup.find("table", {"class": "catalog"})
    if not table:
        return []

    extracted_data = []
    rows = table.find_all("tr")[1:]

    for row in rows:
        authors = []
        cells = row.find_all("td")
        authors = extract_authors(cells[0])
        title = extract_title(cells[2])
        download_links = extract_download_page_links(cells[5])
        extracted_data.append(
            {"authors": authors, "title": title, "download_urls": download_links}
        )
    return extracted_data


async def resolve_download_links(
    session: httpx.AsyncClient, download_links: list[str]
) -> list[str]:
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
    soup = BeautifulSoup(html_content, "html.parser")
    link = soup.find("a", href=True, text="GET")
    if link:
        if "http" not in link["href"]:
            return f'https://libgen.li/{link["href"]}'
        return link["href"]


def extract_authors(td: BeautifulSoup) -> list[str]:
    authors = []
    authors_list = td.find_all("a")
    for author in authors_list:
        name = author.text.strip()
        authors.append(name)
    return authors


def extract_title(td: BeautifulSoup) -> str:
    title = td.find("a").text.strip()
    return title


def extract_download_page_links(td: BeautifulSoup) -> list[str]:
    links = []
    for link in td.find_all("a"):
        links.append(link["href"])
    return links


async def produce_search_results_for_title(
    session: httpx.AsyncClient, title: Title, send_stream: MemoryObjectSendStream
):
    # substitute uppercase letters before that letter followed by a space
    processed_title = camel_to_string(title.title)
    results = await search(session, q=f'{processed_title} {title.author if title.author else ""}')
    logger.debug(f"Produced {results} for {title.title_id}")
    await send_stream.send({"title_id": title.title_id, 'hits': results})
    await send_stream.aclose()


async def save_search_results(
    file_stream: FileWriteStream, results_stream: MemoryObjectReceiveStream
):
    async with results_stream:
        async for result in results_stream:
            logger.info(f"Saving {result}")
            await file_stream.send(orjson.dumps(result) + b"\n")


async def search_and_store_titles_from_libgen(
    session: httpx.AsyncClient, titles: list[Title]
):
    csv_path = settings.tvtropes.csv_dir / "libgen.jsonl"
    send_stream, receive_stream = anyio.create_memory_object_stream[dict]()
    async with await FileWriteStream.from_path(csv_path, append=True) as fstream:
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(save_search_results, fstream, receive_stream)
                async with send_stream:
                    for title in titles:
                        logger.debug(f"Adding {title.title_id} to the task group")
                        tg.start_soon(
                            produce_search_results_for_title,
                            session,
                            title,
                            send_stream.clone(),
                        )
                        
        except Exception as e:
            logger.error(f"Task group error: {e}")
            # Log all sub-exceptions if it's an ExceptionGroup
            if hasattr(e, 'exceptions'):
                for sub_exc in e.exceptions:
                    logger.error(f"Sub-exception: {sub_exc}")



async def get_tvtropes_titles_from_libgen(scraped_path=None):
    exclude_ids = set()
    if scraped_path is None:
        scraped_path = settings.tvtropes.csv_dir / "libgen.jsonl"
    if not scraped_path.exists():
        scraped_path.touch()
    scraped_titles = [
        title
        async for title in async_load_jsonl(settings.tvtropes.csv_dir / "libgen.jsonl")
    ]
    for title in scraped_titles:
        exclude_ids.add(title["title_id"])
    
    goodreadsTropesCRUD = TropeExamplesCRUD.load_from_csv(settings.tvtropes, 'lit_goodreads_match')
    titles = goodreadsTropesCRUD.get_titles(
        limit=10000000, exclude_ids=list(exclude_ids)
    )
    bacth_size = 10
    for batch in tqdm(
        [titles[i : i + bacth_size] for i in range(0, len(titles), bacth_size)]
    ):
        if len(batch) == 0:
            break
        if environ.get("PROXY"):
            async with httpx.AsyncClient(
                proxy=environ.get("PROXY"),
                limits=httpx.Limits(
                    max_keepalive_connections=10, max_connections=10, keepalive_expiry=5.0
                ),
            ) as session:
                logger.debug(f"Starting to scrape {batch}")
                await search_and_store_titles_from_libgen(session, batch)
                logger.debug(f"Finished scraping batched {batch}")
        else:
            async with httpx.AsyncClient(limits=httpx.Limits(
                    max_keepalive_connections=10, max_connections=10, keepalive_expiry=5.0
                )) as session:
                await search_and_store_titles_from_libgen(session, batch)


def download_books_scraped(scraped_list_path, limit: 1000, offset: 0, title_ids: list[str] = None):
    with open(scraped_list_path, "r") as f:
        scraped_books = [orjson.loads(line) for line in f]

    logger.info(f"Scraped books: {len(scraped_books)}")
    if title_ids:
        logger.info(f"Filtering scraped books for title_ids: {title_ids}")
        scraped_books = [book for book in scraped_books if book["title_id"] in title_ids and book["hits"]]

    downloaded_books = settings.books.dir.glob("*.epub")
    downloaded_books = [book.stem for book in downloaded_books]

    scraped_books = TypeAdapter(list[LibgenSearchResult]).validate_python(scraped_books)
    scraped_books = [book for book in scraped_books if len(book.hits) > 0 and book.title_id not in downloaded_books]

    if len(scraped_books) == 0:
        logger.info("No hits on libgen. Skipping download.")
        return

    for book in scraped_books[offset: offset + limit]:
        for hit in book.hits:
            saved = False
            for link in hit.download_urls:
                try:
                    response = httpx.get(str(link))
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    continue
                else:
                    direct_download_link = extract_download_link(response.content)
                    if direct_download_link:
                        try: 
                            response = httpx.get(direct_download_link)
                            
                            with open(
                                settings.books.dir / f"{book.title_id}.epub", "wb"
                            ) as f:
                                f.write(response.content)
                            saved = True
                        except httpx.HTTPError:
                            continue
                        else:
                            break
                  
            if saved:
                break
                    
         
    
            
async def search_and_download_titles(title_ids: list[str]):
    logger.info(f"Searching and downloading titles: {title_ids}")
    
    # Load goodreads data
    goodreadsTropesCRUD = TropeExamplesCRUD.load_from_csv(settings.tvtropes, 'lit_goodreads_match')
    titles_to_search = [t for t in goodreadsTropesCRUD.get_titles(limit=10000000) if t.title_id in title_ids]
    
    if len(titles_to_search) == 0:
        logger.warning(f"No titles matched in goodreads: {title_ids}")
        return

    # Create books directory
    settings.books.dir.mkdir(parents=True, exist_ok=True)
    
    TIMEOUT = httpx.Timeout(connect=5, read=5, write=5, pool=5)  # Timeout settings
    
    # Process each title
    for title in titles_to_search:
        try:
            logger.info(f"Processing {title.title_id}: {title.title}")
            
            # Skip if already downloaded
            if (settings.books.dir / f"{title.title_id}.epub").exists():
                logger.info(f"Book already downloaded: {title.title_id}")
                continue
                
            # Search on libgen
            async with httpx.AsyncClient(
                proxy=environ.get("PROXY") if environ.get("PROXY") else None,
                timeout=TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10, keepalive_expiry=5.0)
            ) as session:
                processed_title = camel_to_string(title.title)
                search_query = f'{processed_title} {title.author if title.author else ""}'
                results = await search(session, q=search_query)
                
                if not results:
                    logger.warning(f"No results found for {title.title_id}")
                    continue
                
                # Try each search result
                for hit in results:
                    saved = False
                    for link in hit["download_urls"]:
                        try:
                            # Get download page
                            response = await session.get(str(link))
                            response.raise_for_status()
                            
                            # Extract direct download link
                            direct_link = extract_download_link(response.content)
                            if not direct_link:
                                continue
                                
                            # Download book
                            response = await session.get(direct_link, timeout=TIMEOUT)
                            response.raise_for_status()
                            
                            # Save book
                            with open(settings.books.dir / f"{title.title_id}.epub", "wb") as f:
                                f.write(response.content)
                            saved = True
                            logger.info(f"Successfully downloaded: {title.title_id}")
                            break
                            
                        except httpx.TimeoutException as e:
                            logger.error(f"Timeout downloading {title.title_id}: {e}")
                            continue
                        except httpx.HTTPError as e:
                            logger.error(f"HTTP error for {title.title_id}: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error downloading {title.title_id}: {e}")
                            continue
                            
                    if saved:
                        break
                        
                if not saved:
                    logger.warning(f"Failed to download any version of {title.title_id}")
                    
        except Exception as e:
            logger.error(f"Error processing title {title.title_id}: {e}")
            continue

if __name__ == "__main__":
    # parse program arguments and run
    parser = argparse.ArgumentParser(description="Download books from Libgen")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download books",
    )

    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Scrape books",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Number of books to download",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Offset to start downloading from",
    )
    parser.add_argument(
        "--scraped_list_path",
        type=str,
        default=settings.tvtropes.csv_dir / "libgen.jsonl",
        help="Path to scraped list of books",
    )
    parser.add_argument(
        "--title_ids",
        type=str,
        default=None,
        help="Title ids to download",
    )

    args = parser.parse_args()
    if args.scrape:
        anyio.run(get_tvtropes_titles_from_libgen)
    elif args.download:
        download_books_scraped(args.scraped_list_path, args.limit, args.offset, args.title_ids.split(',') if args.title_ids else [])
    elif args.title_ids:
        anyio.run(search_and_download_titles, args.title_ids.split(','))
            
