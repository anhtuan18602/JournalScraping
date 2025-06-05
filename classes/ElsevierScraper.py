import requests
import time
import json

class ElsevierMetadataScraper:
    def __init__(self, api_key, method, year, journal, delay=3, max_results=1000):
        self.api_key = api_key
        self.delay = delay
        self.max_results = max_results
        self.endpoint = "https://api.elsevier.com/content/search/scopus"
        self.query = (
            f'TITLE-ABS-KEY(experiment OR experiments OR experimental OR laboratory OR "field experiment" OR "field experiments") '
            f'AND PUBYEAR = {year} '
            f'AND SRCTITLE("{journal}")'
        )
        self.headers = {
            'X-ELS-APIKey': self.api_key,
            'Accept': 'application/json'
        }
    def get_abstract(self, scopus_id):
        params = {
                'view': 'FULL',
                'field': 'description'
            }
        url = f'https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}'
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            with open('abstract_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            try:
                abstract = data['abstracts-retrieval-response']['coredata']['dc:description']
                return abstract
            except KeyError:
                return ''
        return ''

    def fetch_metadata(self):
        all_results = []
        start = 0
        count = 25  # max per request

        while start < self.max_results:
            params = {
                'query': self.query,
                'count': count,
                'start': start
            }

            print(f"Requesting results {start + 1} to {start + count}...")

            response = requests.get(self.endpoint, headers=self.headers, params=params)

            if response.status_code != 200:
                print(f"Request failed with status {response.status_code}")
                break

            data = response.json()
            if start == 0:
                with open('elsevier_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            entries = data.get('search-results', {}).get('entry', [])

            if not entries:
                print("No more entries found.")
                break

            for entry in entries:
                page_range = entry.get('prism:pageRange', '')
                start_page, end_page = '', ''
                if page_range and '-' in page_range:
                    start_page, end_page = page_range.split('-')
                affiliations = entry.get('affiliation', [])
                affil_names = [a.get('affilname', '') for a in affiliations]
                affil_str = '; '.join(affil_names) if affil_names else ''
                doi = entry.get('prism:doi')
                scopus_id = entry.get('dc:identifier').split(":")[1]
                all_results.append({
                    'title': entry.get('dc:title'),
                    'abstract': entry.get('dc:description'),
                    #'abstract': self.get_abstract(scopus_id),
                    'doi': doi,
                    'year': entry.get('prism:coverDate', '')[:4],
                    'cover_date': entry.get('prism:coverDate'),
                    'author': entry.get('dc:creator'),
                    'volume': entry.get('prism:volume'),
                    'issue': entry.get('prism:issueIdentifier'),
                    'affiliation': affil_str,
                    'citedbycount': entry.get("citedby-count"),
                    'page_range': page_range,
                    'start_page': start_page,
                    'end_page': end_page
                })
                time.sleep(1)
            start += count
            time.sleep(self.delay)

        print(f"Retrieved {len(all_results)} results.")
        return all_results
