import httpx
import asyncio
from aiolimiter import AsyncLimiter
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import argparse
import sys
from .dataset import BookCompanion
import logging
import tqdm
from libgen_api_enhanced import LibgenSearch
from rapidfuzz import fuzz
import numpy as np

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


rate_limiter = AsyncLimiter(max_rate=10, time_period=5)

BASE_URL = 'https://www.bookcompanion.com'



async def fetch_url(client, url):
    async with rate_limiter:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            print(f"Failed to fetch {url}: {e}")
            return None

"""
<tr>
    <td style="width: 615px; height: 50px" class="style57">
            <a href="love_does_character_list2.html">Love Does</a></td>
    <td style="width: 70px; height: 50px" class="style128">40</td>
    <td style="width: 300px; height: 50px" class="style56">
            <a href="love_does_links2.html">Bob Goff</a></td>
</tr>
"""
async def extract_books(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = []
    for row in soup.find_all('tr'):
        title = None
        author = None
        character_list_url = None
        links_url = None
        for td in row.find_all('td'):
            if td.get('class') == ['style57']:
                if not td.find('a', href=True):
                    break
                link = td.find('a', href=True)
                title = link.get_text().replace('\t', '').replace('\n', '').replace('(QE)', '').replace('(VE)', '').strip()
                character_list_url = str(httpx.URL(base_url).join(link['href']))
               
            if td.get('class') == ['style56']:
                if td.find('a', href=True):
                    link = td.find('a', href=True)
                    author = link.get_text().replace('\t', '').replace('\n', '')
                    links_url = str(httpx.URL(base_url).join(link['href']))
                else:
                    author = td.get_text().replace('\t', '').replace('\n', '')
                    links_url = None

        if character_list_url is None:
            continue

        data.append({
            'title': title,
            'author': author,
            'links_url': links_url,
            'character_list_url': character_list_url,
            'scraped_character_list': False,
            'goodreads_link': None,
            'text_file_path': None
        })
    return data

def extract_character_list(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'class': 'style55'})
    extracted_data = []

    if table:
        rows = table.find_all('tr')[1:] 
        for row in rows:
            cells = row.find_all('td')
            indices = [1, 2, 3]
            if len(cells) >= 7:
                indices = [2, 4, 6]

            first_name = indices[0].get_text(strip=True)
            last_name = indices[1].get_text(strip=True)
            description = indices[2].get_text(strip=True)
            extracted_data.append({
                'first_name': first_name.strip().replace('\n', ' ').replace('\t', ''),
                'last_name': last_name.strip().replace('\n', ' ').replace('\t', ''),
                'description': description.strip().replace('\n', ' ').replace('\t', '')
            })

    return extracted_data


def extract_goodreads_link(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)

    for link in links:
        if 'goodreads.com/en/book/show' in link['href'] or 'goodreads.com/book/show' in link['href']:
            return {"goodreads_link": link['href'].replace('”', '').replace('"', '').strip()}



async def scrape_book_list():
    book_list_url = "https://www.bookcompanion.com/book_list.html"
    async with httpx.AsyncClient() as client:
        html_content = await fetch_url(client, book_list_url)
        return await extract_books(html_content, BASE_URL)




def search_and_download_epub(title, author):
    tf = LibgenSearch()
    title_filters = {"Extension": "epub"}
    hits = tf.search_default_filtered(title, title_filters, exact_match=True)
    if len(hits) == 0:
        logger.info(f"No results found for {title} by {author}")
        return None
    author_scores = []
    for hit in hits:
        score = fuzz.partial_token_sort_ratio(hit["Author"], author)
        author_scores.append(score/100.0)

    best_choice = hits[np.argmax(author_scores)]
    if np.max(author_scores) < 0.8:
        return None
    logger.info(f"Found epub for {title} by {author} ==> {best_choice['Title']} by {best_choice['Author']}, score: {np.max(author_scores)}")
    download_link = best_choice["Direct_Download_Link"]
    try:
        response = httpx.get(download_link)
    except httpx.HTTPError as e:
        logger.error(f"Failed to download {download_link}.")
        return None
    if response.status_code == 200:
        return response.content
    else:
        return None

    



async def batch_scrape(batch, extract_method):
    async with httpx.AsyncClient() as client:
        tasks = []
        for url in batch:
            tasks.append(fetch_url(client, url))
        html_contents = await asyncio.gather(*tasks)
        return [{"url": batch[i], "data": extract_method(html_content)} for i, html_content in enumerate(html_contents) if html_content is not None ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book_list", action="store_true")
    parser.add_argument("--characters", action="store_true")
    parser.add_argument("--goodreads", action="store_true")
    parser.add_argument("--epub", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    bookcompanion = BookCompanion.load_from_csv()

    if args.book_list:
        book_list = asyncio.run(scrape_book_list())
        bookcompanion.update_book_list(pd.DataFrame(book_list))
        bookcompanion.save_book_list()

    if args.characters:
        urls = bookcompanion.book_list[bookcompanion.book_list['scraped_character_list'] == False]['character_list_url'].values
        batches = [urls[i:i+10] for i in range(0, len(urls), 10)]
        for batch in tqdm.tqdm(batches):
            scraped_data = asyncio.run(batch_scrape(batch, extract_character_list))
            logger.debug(scraped_data)
            characters = pd.DataFrame([{'character_list_url': item['url'], **ch} for item in scraped_data for ch in item['data']])
            actually_scraped_urls = [item['url'] for item in scraped_data if item and item['data'] is not None and len(item['data']) > 0]
            bookcompanion.update_characters(characters)
            bookcompanion.book_list.loc[bookcompanion.book_list['character_list_url'].isin(actually_scraped_urls), 'scraped_character_list'] = True
            bookcompanion.save()

    if args.goodreads:
        urls = bookcompanion.book_list[bookcompanion.book_list['links_url'].notna()][bookcompanion.book_list['goodreads_link'].isna()]['links_url'].values
        batches = [urls[i:i+10] for i in range(0, len(urls), 10)]
        for batch in tqdm.tqdm(batches):
            goodreads_links = asyncio.run(batch_scrape(batch, extract_goodreads_link))
            actually_scraped_urls = [item['url'] for item in scraped_data if item]
            goodreads_links = [item['data']['goodreads_link'] if item['data'] is not None else None for item in goodreads_links]
            bookcompanion.book_list.loc[bookcompanion.book_list['links_url'].isin(actually_scraped_urls), 'goodreads_link'] = goodreads_links
            bookcompanion.save_book_list()

    if args.epub:
        titles = bookcompanion.book_list[bookcompanion.book_list['text_file_path'].isna()]
        for title, author in tqdm.tqdm(zip(titles['title'].values, titles['author'].values)):
            content = search_and_download_epub(title, author)
            if content is None:
                continue
            #replace * " / \ < > : | ? in title for path
            epub_file_path: Path = (BookCompanion.DATASET_PATH / f'{title.replace("*", "").replace("\"", "").replace("/", "").replace("\\", "").replace("<", "").replace(">", "").replace(":", "").replace("|", "").replace("?", "")}.epub')
            with open(epub_file_path, 'wb') as f:
                f.write(content)
            bookcompanion.book_list.loc[bookcompanion.book_list['title'] == title, 'text_file_path'] = epub_file_path.with_suffix('.txt').as_posix()
            bookcompanion.save_book_list()
          

            
