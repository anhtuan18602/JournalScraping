import requests
import time
import json

class ElsevierMetadataScraper:
    def __init__(self, api_key, year, journal, delay=3, max_results=1000):
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
    def get_article(self, doi):

        url = f'https://api.elsevier.com/content/article/doi/{doi}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            with open('article_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return data['full-text-retrieval-response']['coredata'] 
        return {}

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
                affiliations = entry.get('affiliation', [])
                affil_names = [a.get('affilname', '') for a in affiliations]
                affil_str = '; '.join(affil_names) if affil_names else ''
                doi = entry.get('prism:doi')
                scidir = self.get_article(doi)

                all_results.append({
                    'title': entry.get('dc:title'),
                    'abstract': scidir.get('dc:description'),
                    #'abstract': self.get_abstract(scopus_id),
                    'doi': doi,
                    'year': entry.get('prism:coverDate', '')[:4],
                    'cover_date': entry.get('prism:coverDate'),
                    'author.name': entry.get('dc:creator'),
                    'authors': scidir.get('authors'),
                    'volume': entry.get('prism:volume'),
                    'issue': scidir.get('prism:issueIdentifier'),
                    'affiliation': affil_str,
                    'citedbycount': entry.get("citedby-count"),
                    'page_range': scidir.get("prism:pageRange"),
                    'start_page': scidir.get('prism:startingPage'),
                    'end_page': scidir.get('prism:endingPage')
                })
                time.sleep(1)
            start += count
            time.sleep(self.delay)

        print(f"Retrieved {len(all_results)} results.")
        return all_results
