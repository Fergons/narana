from bs4 import BeautifulSoup
import httpx
import asyncio
from app.models.tvtropes import LibgenSearchResult, Title
from app.crud.tvtropes import TropeExamplesCRUD
from app.utils import retry_fetch
import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio.streams.file import FileWriteStream
import re
from utils.string import camel_to_string

import orjson
from app.config import tvtropes_config, books_config
import logging

from app.utils import load_jsonl, async_load_jsonl
from tqdm import tqdm

from pydantic import TypeAdapter

from dotenv import dotenv_values

import argparse


basic_config = logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    csv_path = tvtropes_config.csv_dir / "libgen.jsonl"
    send_stream, receive_stream = anyio.create_memory_object_stream[dict]()
    async with await FileWriteStream.from_path(csv_path, append=True) as fstream:
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(save_search_results, fstream, receive_stream)
                async with send_stream:
                    for title in titles:
                        tg.start_soon(
                            produce_search_results_for_title,
                            session,
                            title,
                            send_stream.clone(),
                        )
        except* httpx.HTTPError as e:
            logger.error(e)

        except* httpx.TimeoutException as e:
            logger.error(e)

        except* httpx.RequestError as e:
            logger.error(e)


async def get_tvtropes_titles_from_libgen():
    exclude_ids = set()
    scraped_path = tvtropes_config.csv_dir / "libgen.jsonl"
    if not scraped_path.exists():
        scraped_path.touch()
    scraped_titles = [
        title
        async for title in async_load_jsonl(tvtropes_config.csv_dir / "libgen.jsonl")
    ]
    for title in scraped_titles:
        exclude_ids.add(title["title_id"])
    
    goodreadsTropesCRUD = TropeExamplesCRUD.load_from_csv('lit_goodreads_match')
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
                await search_and_store_titles_from_libgen(session, batch)
        else:
            async with httpx.AsyncClient(limits=httpx.Limits(
                    max_keepalive_connections=10, max_connections=10, keepalive_expiry=5.0
                )) as session:
                await search_and_store_titles_from_libgen(session, batch)


def download_books_scraped(scraped_list_path, limit: 1000, offset: 0):
    with open(scraped_list_path, "r") as f:
        scraped_books = [orjson.loads(line) for line in f]

    downloaded_books = books_config.dir.glob("*.epub")
    downloaded_books = [book.stem for book in downloaded_books]

    scraped_books = TypeAdapter(list[LibgenSearchResult]).validate_python(scraped_books)
    scraped_books = [book for book in scraped_books if len(book.hits) > 0 and book.title_id not in downloaded_books]


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
                                books_config.dir / f"{book.title_id}.epub", "wb"
                            ) as f:
                                f.write(response.content)
                            saved = True
                        except httpx.HTTPError:
                            continue
                        else:
                            break
                  
            if saved:
                break
                    
         
    
            
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
        default=tvtropes_config.csv_dir / "libgen.jsonl",
        help="Path to scraped list of books",
    )

    args = parser.parse_args()
    if args.scrape:
        anyio.run(get_tvtropes_titles_from_libgen)
    if args.download:
        download_books_scraped(args.scraped_list_path, args.limit, args.offset)

            

