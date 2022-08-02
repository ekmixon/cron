import os
import requests

from bs4 import BeautifulSoup

INDEX_URL = 'https://www.w3.org/TR/'
WG = 'W3C'
TAG_BLOCKLIST = ['i18n', 'Accessibility']


class W3C:
    def __init__(self, cache_dir):
        self.cache_path = os.path.join(cache_dir, 'w3c')
        self.cache = self._load_cache()

    def _load_cache(self):
        seen = {}
        if not os.path.exists(self.cache_path):
            return seen
        with open(self.cache_path) as cache:
            for line in cache:
                rfc_id = line.strip()
                seen[rfc_id] = True
        return seen

    def fetch_abstract(self, url):
        """Attempts to fetch the abstract by parsing the standard HTML body.

        This isn't ideal, but it's about the best we can hope for.
        """
        response = requests.get(url)
        if not response.ok:
            return ''
        soup = BeautifulSoup(response.text, 'html5lib')
        return '\n'.join(
            p.text for p in soup.find('section', {'id': 'abstract'}).findAll('p')
        )

    def fetch(self):
        response = requests.get(INDEX_URL)
        if not response.ok:
            raise Exception(f'Failed to fetch IETF results: {response.text}')

        with open(self.cache_path, 'w') as cache_file:
            soup = BeautifulSoup(response.text, 'html5lib')
            for elem in     soup.find('ul', {
                    'id': 'container'
            }).findAll('li', recursive=False):
                title_elem = elem.find('h2').find('a')
                rfc_url = title_elem['href']
                title = title_elem.text
                cache_file.write(rfc_url + '\n')
                if rfc_url in self.cache:
                    continue
                if tags := elem.find('ul', 'taglist'):
                    skip = False
                    for tag in tags.findAll('li'):
                        tag = tag.text.strip()
                        if tag in TAG_BLOCKLIST:
                            print(f'Skipping {title} because {tag} is in the blocklist')
                            skip = True
                            break
                    if skip:
                        continue
                abstract = ''
                try:
                    abstract = self.fetch_abstract(rfc_url).strip()
                except Exception as e:
                    print(e)
                authors = ''
                if author_elem := elem.find('ul', 'editorlist'):
                    authors = ', '.join(author.text.strip()
                                        for author in author_elem.findAll('li'))
                yield {
                    'wg': WG,
                    'id': rfc_url,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'url': rfc_url
                }
