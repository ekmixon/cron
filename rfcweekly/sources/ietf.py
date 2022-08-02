from defusedxml.ElementTree import fromstring

import os
import requests

INDEX_URL = 'https://www.rfc-editor.org/in-notes/rfc-index.xml'
RFC_URL = 'https://tools.ietf.org/html/{}'
NS = '{http://www.rfc-editor.org/rfc-index}'
WG = 'IETF'


class IETF:
    def __init__(self, cache_dir):
        self.cache_path = os.path.join(cache_dir, 'ietf')
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

    def fetch(self):
        response = requests.get(INDEX_URL)
        if not response.ok:
            raise Exception(f'Failed to fetch IETF results: {response.text}')
        with open(self.cache_path, 'w') as cache_file:
            tree = fromstring(response.text)
            for rfc in tree.findall(f'{NS}rfc-entry'):
                rfc_id = rfc.find(f'{NS}doc-id').text
                cache_file.write(rfc_id + '\n')
                if rfc_id in self.cache:
                    continue
                abstract = ''
                if abstract_elem := rfc.find(f'{NS}abstract'):
                    abstract = ' '.join(p.text for p in abstract_elem.findall(f'{NS}p'))
                authors = ', '.join(
                    author.find(f'{NS}name').text
                    for author in rfc.findall(f'{NS}author')
                )

                url = RFC_URL.format(rfc_id.lower())
                yield {
                    'wg': WG,
                    'id': rfc_id,
                    'title': rfc.find(f'{NS}title').text,
                    'abstract': abstract,
                    'authors': authors,
                    'url': url,
                }
