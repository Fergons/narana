from bs4 import BeautifulSoup
import httpx 
import asyncio

test_html = """
<table class="catalog">
<thead><tr>
	<td style="width:15%">						<a href="/fiction/?q=A+Caribbean+Mystery+Agatha+Christie&amp;criteria=&amp;language=&amp;format=epub&amp;sort=author:a" title="sort">Author(s) <span class="sort_direction">↕</span></a>
			</td>
	<td>						<a href="/fiction/?q=A+Caribbean+Mystery+Agatha+Christie&amp;criteria=&amp;language=&amp;format=epub&amp;sort=series:a" title="sort">Series <span class="sort_direction">↕</span></a>
			</td>
	<td>						<a href="/fiction/?q=A+Caribbean+Mystery+Agatha+Christie&amp;criteria=&amp;language=&amp;format=epub&amp;sort=title:a" title="sort">Title <span class="sort_direction">↕</span></a>
			</td>
	<td>						<a href="/fiction/?q=A+Caribbean+Mystery+Agatha+Christie&amp;criteria=&amp;language=&amp;format=epub&amp;sort=language:a" title="sort">Language <span class="sort_direction">↕</span></a>
			</td>
	<td style="width:9em">						<a href="/fiction/?q=A+Caribbean+Mystery+Agatha+Christie&amp;criteria=&amp;language=&amp;format=epub&amp;sort=filesize:a" title="sort">File <span class="sort_direction">↕</span></a>
			</td>
	<td style="width:9em">Mirrors</td>
	<td style="width:4em">&nbsp;</td>
</tr></thead>
<tbody>
<tr>
	<td>
				<ul class="catalog_authors">
		<li><a href="/fiction/?q=Agatha%2C%20Christie&amp;criteria=authors" title="search by author">Agatha, Christie</a></li>
		</ul>
			</td>
	<td></td>
	<td>
		<p><a href="/fiction/3EFC40196B26E70529050616463D0823">A Caribbean Mystery</a></p>
			</td>
	<td>English</td>
	<td title="Uploaded at 2012-02-03 18:00:00">EPUB / 186&nbsp;Kb</td>
	<td><ul class="record_mirrors_compact"><li><a href="http://library.lol/fiction/3EFC40196B26E70529050616463D0823" title="Libgen.rs">[1]</a></li><li><a href="https://libgen.li/ads.php?md5=3EFC40196B26E70529050616463D0823" title="Libgen.li">[2]</a></li></ul></td>
	<td class="catalog_edit"><a href="https://library.bz/fiction/edit/3EFC40196B26E70529050616463D0823" title="edit metadata">[edit]</a></td>
</tr>
<tr>
	<td>
				<ul class="catalog_authors">
		<li><a href="/fiction/?q=Agatha%2C%20Christie&amp;criteria=authors" title="search by author">Agatha, Christie</a></li>
		</ul>
			</td>
	<td></td>
	<td>
		<p><a href="/fiction/020247F3E0790956CD4B2B399F5EBB75">A Caribbean Mystery</a></p>
			</td>
	<td>English</td>
	<td title="Uploaded at 2012-02-03 18:00:00">EPUB / 186&nbsp;Kb</td>
	<td><ul class="record_mirrors_compact"><li><a href="http://library.lol/fiction/020247F3E0790956CD4B2B399F5EBB75" title="Libgen.rs">[1]</a></li><li><a href="https://libgen.li/ads.php?md5=020247F3E0790956CD4B2B399F5EBB75" title="Libgen.li">[2]</a></li></ul></td>
	<td class="catalog_edit"><a href="https://library.bz/fiction/edit/020247F3E0790956CD4B2B399F5EBB75" title="edit metadata">[edit]</a></td>
</tr>
<tr>
	<td>
				<ul class="catalog_authors">
		<li><a href="/fiction/?q=Christie%2C%20Agatha&amp;criteria=authors" title="search by author">Christie, Agatha</a></li>
		</ul>
			</td>
	<td></td>
	<td>
		<p><a href="/fiction/4783E5F2F328B8F17BCCD62323EA99F6">A Caribbean Mystery</a></p>
			</td>
	<td>English</td>
	<td title="Uploaded at 2012-02-03 18:00:00">EPUB / 171&nbsp;Kb</td>
	<td><ul class="record_mirrors_compact"><li><a href="http://library.lol/fiction/4783E5F2F328B8F17BCCD62323EA99F6" title="Libgen.rs">[1]</a></li><li><a href="https://libgen.li/ads.php?md5=4783E5F2F328B8F17BCCD62323EA99F6" title="Libgen.li">[2]</a></li></ul></td>
	<td class="catalog_edit"><a href="https://library.bz/fiction/edit/4783E5F2F328B8F17BCCD62323EA99F6" title="edit metadata">[edit]</a></td>
</tr>
</tbody>
</table>
"""
async def search(session: httpx.AsyncClient,*, q: str, criteria: str = '', language: str = 'English', format: str = '', resolve_downloads: bool = False) -> list[dict[str, str]]:
    if q is None:
        raise ValueError("q is required")
    
    url = 'https://libgen.is/fiction/'
    params = {
        'q': q,
        'criteria': criteria,
        'language': language,
        'format': format
    }

    response = await session.get(url, params=params)    
    if response.status_code != 200:
        return []
    
    data = extract_table_data(response.content)
    if not resolve_downloads:
      return data
    

    for item in data:
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
        tasks.append(session.get(link))
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

if __name__ == "__main__":
    html_content = test_html
    print(asyncio.run(search(httpx.AsyncClient(), q="Agatha Christie A Caribbean Mystery", format="epub", resolve_downloads=True)))
    



