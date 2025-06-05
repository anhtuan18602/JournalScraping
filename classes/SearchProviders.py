from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

from .Utils import get_user_agent, strip_html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import requests
import json
import math
import time

def get_search_provider(publisher, shortname, identifiers, year_range=(2018, 2021)):
    sp_map = {
        'elsevier': ElsevierSearch,
        'springer': SpringerSearch,
        'wiley': WileySearch,
        'tandf': TAndFSearch,
        'nature': NatureSearch,
        'oxford': OxfordSearch,
        'cambridge': CambridgeSearch
    }
    Provider = sp_map.get(publisher, lambda sn, ids, year_range: "Search provider does not exist")
    return Provider(shortname, identifiers, year_range=year_range)


class SearchProvider:
    def __init__(self, journal_shortname, journal_identifiers, year_range=(), article_types=None, exclusions=None):
        self.journal_shortname = journal_shortname
        self.journal_identifiers = journal_identifiers
        self.start_year, self.end_year = year_range
        self.article_types = article_types
        self.exclusions = exclusions
        self.results = []
        self.search_conducted = False
        self.base_settings = self._get_base_settings()
        self.queries = self._generate_queries()
        options = uc.ChromeOptions()
        options.headless = False  # Headless is detectable – start with visible mode
        options.add_argument(f"user-agent={get_user_agent()}")
        options.add_argument("--window-size=1280,800")
        options.add_argument("lang=en-US,en;q=0.9")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"
        # Create driver
        print("Binary location:", options.binary_location)
        self.driver = uc.Chrome(options=options)

    def _generate_queries(self):
        raise NotImplemented('You need to implement this method in a sub-class.')

    def _get_base_settings(self):
        raise NotImplemented('You need to implement this method in a sub-class.')

    def _conduct_search(self, query):
        raise NotImplemented('You need to implement this method in a sub-class.')

    def search(self):
        for query in self.queries:
            self._conduct_search(query)
        self.search_conducted = True


class ElsevierSearch(SearchProvider):
    def __init__(self, journal_shortname, journal_identifiers, year_range=(), article_types=('REV', 'FLA'),
                 exclusions=None):
        super().__init__(journal_shortname, journal_identifiers, year_range, article_types, exclusions)

    def _get_base_settings(self):
        return {
            'search_url': 'https://www.sciencedirect.com/search/api?',
            'download_base_url': 'https://www.sciencedirect.com'
        }

    def _generate_queries(self):
        base_query = {
            'show': 100,
            'sortBy': 'date',
            'articleTypes': ','.join(self.article_types),
            'offset': 0,
            'docId': self.journal_identifiers[0]
        }

        queries = []
        for year in reversed(range(self.start_year, self.end_year+1)):
            query = base_query.copy()
            query.update({'date': year})
            queries.append(query)
        return queries

    def _conduct_search(self, query):
        start = query['offset']
        limit = query['show']
        num_results = -1
        while num_results == -1 or num_results > start + limit:
            if num_results != -1:
                start += limit

            print('..requesting results [%s, %s]' % (start+1, start + limit))
            query.update({
                'offset': start,
                'show': limit
            })

            url = self.base_settings['search_url'] + urlencode(query, quote_via=quote_plus)
            print(url)
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                break
            try:
                result = json.loads(r.text)
            except json.decoder.JSONDecodeError:
                print('institutional login required')
                exit('error')

            num_results = int(result['resultsFound'])

            for article in result['searchResults']:
                self.results.append({
                    'publisher': 'elsevier',
                    'journal': article['sourceTitle'],
                    'journal_shortname': self.journal_shortname,
                    'doi': article['doi'],
                    'title': strip_html(article['title']),
                    'year': int(article['publicationDate'][:4]),
                    'preview_url': self.base_settings['download_base_url'] + article['link'],
                    'fulltext_url': self.base_settings['download_base_url'] + article['pdf']['downloadLink'],
                })


class SpringerSearch(SearchProvider):
    def __init__(self, journal_shortname, journal_identifiers, year_range=(), article_types=None,
                 exclusions=('Erratum',)):
        super().__init__(journal_shortname, journal_identifiers, year_range, article_types, exclusions)

    def _get_base_settings(self):
        return {
            'search_url': 'https://link.springer.com/search/page/',
            'download_base_url': 'https://link.springer.com'
        }

    def _generate_queries(self):
        base_query = {
            'date-facet-mode': 'between',
            'facet-start-year': None,
            'facet-end-year': None,
            'showAll': 'true',
            'sortOrder': 'newestFirst',
            'facet-content-type': "Article",
        }

        query_string = "({})".format(" OR ".join(self.journal_identifiers))
        if self.exclusions:
            query_string += " AND NOT({})".format(" ".join(self.exclusions))

        base_query.update({'query': query_string})

        queries = []
        for year in reversed(range(self.start_year, self.end_year + 1)):
            query = base_query.copy()
            query.update({'facet-start-year': year, 'facet-end-year': year})
            queries.append(query)

        return queries

    def _conduct_search(self, query):
        page = 0
        max_page = 1

        while page < max_page:
            page += 1

            url = self.base_settings['search_url'] + str(page) + '?' + urlencode(query, quote_via=quote_plus)
            # print(url)
            print('..requesting page', page)
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                print(r.status_code)
                break

            soup = BeautifulSoup(r.content, 'html.parser')

            # total number of pages
            # print(url)
            if page == 1:
                element = soup.find('span', attrs={'class': 'number-of-pages'})
                if element:
                    max_page = int(element.text)

            # search results
            search_result_list = soup.find('ol', attrs={'id': 'results-list'})
            for result in search_result_list.find_all('li'):
                title = strip_html(result.h2.a.text)
                preview_link = self.base_settings['download_base_url'] + result.h2.a['href']
                doi = result.h2.a['href'].replace('/article/', '')
                enumeration = result.find('p', attrs={'class': 'meta'}).find('span', attrs={'class': 'enumeration'})
                journal = enumeration.a.text
                year = int(enumeration.span.text[1:-1])
                fulltext_link = self.base_settings['download_base_url'] + '/content/pdf/' + doi + '.pdf'

                self.results.append({
                    'publisher': 'springer',
                    'journal': journal,
                    'journal_shortname': self.journal_shortname,
                    'doi': doi,
                    'title': title,
                    'year': year,
                    'preview_url': preview_link,
                    'fulltext_url': fulltext_link,
                })


class WileySearch(SearchProvider):
    def __init__(self, journal_shortname, journal_identifiers, year_range=(), article_types=None,
                 exclusions=('Corrigendum', 'Erratum', 'Issue Information')):
        super().__init__(journal_shortname, journal_identifiers, year_range, article_types, exclusions)

    def _get_base_settings(self):
        return {
            'search_url': 'https://onlinelibrary.wiley.com/action/doSearch?',
            'download_base_url': 'https://onlinelibrary.wiley.com/doi/pdfdirect/',
            'preview_base_url': 'https://onlinelibrary.wiley.com/doi/'
        }

    def _generate_queries(self):
        base_query = {
            'field1': 'AllField',
            'text1': " ".join([jid.replace('-', '') for jid in self.journal_identifiers]),
            'AfterMonth': 1,
            'BeforeMonth': 12,
            'startPage': 0,
            'pageSize': 100,
            'sortBy': 'Earliest'
        }

        queries = []
        for year in reversed(range(self.start_year, self.end_year + 1)):
            query = base_query.copy()
            query.update({'AfterYear': year, 'BeforeYear': year})
            queries.append(query)

        return queries

    def _conduct_search(self, query):
        page = 0
        max_page = 1

        while page < max_page:
            query.update({'startPage': page})
            page += 1

            print('page', page)
            url = self.base_settings['search_url'] + urlencode(query, quote_via=quote_plus)
            print(url)
            """
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                print(f"not working: {r.status_code}")
                break

            soup = BeautifulSoup(r.content, 'html.parser')
            """
            self.driver.get(url)
            time.sleep(5)  # wait for JS to load
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # total number of pages
            # print(url)
            if page == 1:
                ul_list = soup.find('ul', attrs={'class': 'pagination__list'})
                if ul_list:
                    max_page = len(ul_list.find_all('li'))

            # search results
            search_result_list = soup.find_all('li', attrs={'class': 'search__item'})
            for result in search_result_list:
                if hasattr(result.find('span', attrs={'class': 'meta__type'}), 'text'):
                    article_type = result.find('span', attrs={'class': 'meta__type'}).text
                else:
                    article_type = ''
                if article_type in self.exclusions:
                    continue

                access_element = result.find('span', attrs={'class': 'meta__access'})

                title_element = result.find('a', attrs={'class': 'publication_title'})
                title = title_element.text
                doi = title_element['href'].replace('/doi/', '')

                if hasattr(result.find('a', attrs={'class': 'publication_meta_serial'}), 'text'):
                    journal = result.find('a', attrs={'class': 'publication_meta_serial'}).text
                else:
                    journal = ''

                if hasattr(result.find('p', attrs={'class': 'meta__epubDate'}), 'contents'):
                    year_string = result.find('p', attrs={'class': 'meta__epubDate'}).contents[1].strip()
                else:
                    year_string = '0000'
                year = year_string[-4:]

                preview_link = self.base_settings['preview_base_url'] + doi
                fulltext_link = self.base_settings['download_base_url'] + doi + '?download=true'

                self.results.append({
                    'publisher': 'wiley',
                    'journal': journal,
                    'journal_shortname': self.journal_shortname,
                    'doi': doi,
                    'title': title,
                    'year': year,
                    'preview_url': preview_link,
                    'fulltext_url': fulltext_link,
                })


class TAndFSearch(SearchProvider):
    def __init__(self, journal_shortname, journal_identifiers, year_range=(), article_types=None,
                 exclusions=('Correction', 'Editorial')):
        super().__init__(journal_shortname, journal_identifiers, year_range, article_types, exclusions)

    def _get_base_settings(self):
        return {
            'search_url': 'https://www.tandfonline.com/action/doSearch?',
            'preview_base_url': 'https://www.tandfonline.com',
        }

    def _generate_queries(self):
        base_query = {
            'field1': 'AllField',
            'text1': "NOT ({})".format(" OR ".join(self.exclusions)),
            'SeriesKey': self.journal_identifiers[0],
            'sortBy': 'Earliest_asc',
            'pageSize': 100,
            'startPage': 1
        }

        queries = []
        for year in reversed(range(self.start_year, self.end_year + 1)):
            query = base_query.copy()
            query.update({'AfterYear': year, 'BeforeYear': year})
            queries.append(query)

        return queries

    def _conduct_search(self, query):
        page = 0
        max_page = 1

        while page < max_page:
            query.update({'startPage': page})
            page += 1
            print('page', page)
            url = self.base_settings['search_url'] + urlencode(query, quote_via=quote_plus)
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                break

            soup = BeautifulSoup(r.content, 'html.parser')

            # pages
            if page == 1:
                pageination_items = soup.find_all('li', attrs={'class': 'pageLinks'})
                if pageination_items:
                    max_page = len(pageination_items) - 1

            # search results
            search_result_list = soup.find('ol', attrs={'class': 'search-results'})
            for result in search_result_list.find_all('li', attrs={'class': 'search-article-tools'}):

                title_element = result.find('span', attrs={'class': 'hlFld-Title'})
                title = title_element.a.text
                doi = title_element.a['href'].replace('/doi/full/', '')

                journal = result.find('a', attrs={'class': 'searchResultJournal'}).text

                year_string = result.find('span', attrs={'class': 'publication-year'}).contents[1].strip()
                year = year_string[-4:]

                preview_link = self.base_settings['preview_base_url'] + '/doi/full/' + doi
                fulltext_link = self.base_settings['preview_base_url'] + '/doi/pdf/' + doi

                self.results.append({
                    'publisher': 'tandf',
                    'journal': journal,
                    'journal_shortname': self.journal_shortname,
                    'doi': doi,
                    'title': title,
                    'year': year,
                    'preview_url': preview_link,
                    'fulltext_url': fulltext_link,
                })


class NatureSearch(SearchProvider):
    def __init__(self, journal_shortname, journal_identifiers, year_range=(),
                 article_types=('research', 'comments-and-opinion', 'reviews'), exclusions=None):
        super().__init__(journal_shortname, journal_identifiers, year_range, article_types, exclusions)

    def _get_base_settings(self):
        return {
            'search_url': 'https://www.nature.com/search?',
            'preview_base_url': 'https://www.nature.com',
        }

    def _generate_queries(self):
        base_query = {
            'order': 'date_desc',
            'article_type': ",".join(self.article_types),
            'journal': self.journal_identifiers[0],
            'date_range': '',  # 2018 - 2021
            'page': 1
        }

        queries = []
        for year in reversed(range(self.start_year, self.end_year + 1)):
            query = base_query.copy()
            query.update({'date_range': f'{year}-{year}'})
            queries.append(query)

        return queries

    def _conduct_search(self, query):
        page = 0
        max_page = 1

        while page < max_page:
            page += 1
            query.update({'page': page})
            print('page', page)
            url = self.base_settings['search_url'] + urlencode(query, quote_via=quote_plus)
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                break

            soup = BeautifulSoup(r.content, 'html.parser')

            # pages
            if page == 1:
                element = soup.find('div', attrs={'class': 'filter-results'})
                if element:
                    max_page = math.ceil(int(element.p.contents[3].text.strip()) / 50)

            # search results
            search_result_list = soup.find('ol', attrs={'class': 'clean-list'})
            for result in search_result_list.find_all('li', attrs={'itemtype': 'http://schema.org/Article'}):

                title_element = result.find('h2', attrs={'itemprop': 'headline'})
                title = title_element.a.text.strip()

                did = title_element.a['href'].replace('/articles/', '')
                doi = '10.1038/' + did  # nature research always has the same prefix to form a doi

                journal = result.find('a', attrs={'class': 'emphasis text-gray'}).text.strip()

                year = result.find('time', attrs={'itemprop': 'datePublished'})['datetime'][:4]

                preview_link = self.base_settings['preview_base_url'] + '/articles/' + did
                fulltext_link = self.base_settings['preview_base_url'] + '/articles/' + did + '.pdf'

                self.results.append({
                    'publisher': 'nature',
                    'journal': journal,
                    'journal_shortname': self.journal_shortname,
                    'doi': doi,
                    'title': title,
                    'year': year,
                    'preview_url': preview_link,
                    'fulltext_url': fulltext_link,
                })


class OxfordSearch(SearchProvider):
    def __init__(self, journal_shortname, journal_identifiers, year_range=(), article_types=('Research Article',), exclusions=None):
        super().__init__(journal_shortname, journal_identifiers, year_range, article_types, exclusions)

    def _get_base_settings(self):
        return {
            'search_url': 'https://academic.oup.com/journals/search-results?',
            'preview_base_url': 'https://academic.oup.com'
        }

    def _generate_queries(self):
        base_query = {
            'f_JournalDisplayName': self.journal_identifiers[0],
            'f_ContentType': 'Journal Article',
            'f_ArticleTypeDisplayName': "AND".join(self.article_types) ,
            'page': 1,
            'sort': "Date - Newest First"
        }

        queries = []
        for year in reversed(range(self.start_year, self.end_year + 1)):
            query = base_query.copy()
            query.update({'rg_ArticleDate': f'01/01/{year} TO 12/31/{year}'})
            queries.append(query)

        return queries

    def _conduct_search(self, query):
        page = 0
        max_page = 1

        while page < max_page:
            page += 1
            query.update({'page': page})
            print('page', page)
            url = self.base_settings['search_url'] + urlencode(query, quote_via=quote_plus)
            print(url)
            """
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                print(r.status_code)
                break   
            soup = BeautifulSoup(r.content, 'html.parser')
            """
            self.driver.get(url)
            time.sleep(5)  # wait for JS to load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # pages
            if page == 1:
                element = soup.find('div', attrs={'class': 'sr-statistics'})
                if element:
                    parts = element.text.split('of')
                    results_range = parts[0].split('-')
                    try:
                        results_per_page = int(results_range[-1])
                    except:
                        break
                    max_results = int(parts[-1])

                    max_page = math.ceil(max_results / results_per_page)

            # search results
            for result in soup.find_all('div', attrs={'class': 'al-article-box'}):
                title_box = result.find('h4', attrs={'class': 'sri-title'})
                title = title_box.a.text

                preview_link = self.base_settings['preview_base_url'] + title_box.a['href']

                journal = result.find('div', attrs={'class': None}).a.text.strip()

                doi = result.find('div', attrs={'class': 'al-citation-list'}).span.a['href'].replace('https://doi.org/', '')

                year = int(result.find('div', attrs={'al-pub-date'}).contents[-1][-4:].strip())

                self.results.append({
                    'publisher': 'oxford',
                    'journal': journal,
                    'journal_shortname': self.journal_shortname,
                    'doi': doi,
                    'title': title,
                    'year': year,
                    'preview_url': preview_link,
                    'fulltext_url': None,  # there appears to be one on the preview page, but it won't work.
                })


class CambridgeSearch(SearchProvider):
    def _get_base_settings(self):
        return {
            'search_url': 'https://www.cambridge.org/core/what-we-publish/journals/listing?',
            'preview_url': 'https://www.cambridge.org'
        }

    def _generate_queries(self):
        base_query = {
            'aggs[productTypes][filters]': 'JOURNAL_ARTICLE',
            'aggs[productJournal][filters]': self.journal_identifiers[0],
            'sort': 'canonical.date:desc',
            'pageNum': 1
        }

        queries = []
        for year in reversed(range(self.start_year, self.end_year + 1)):
            query = base_query.copy()
            query.update({
                'filters[dateYearRange][from]': year,
                'filters[dateYearRange][to]': year
            })
            queries.append(query)

        return queries

    def _conduct_search(self, query):
        page = 0
        max_page = 1

        while page < max_page:
            page += 1
            query.update({'pageNum': page})
            print('page', page)

            url = self.base_settings['search_url'] + urlencode(query, quote_via=quote_plus)
            print(url)
            r = requests.get(url, headers=get_user_agent())
            if r.status_code != 200:
                break


            # with open('test.htm', 'w') as f:
            #     f.write(r.text)

            soup = BeautifulSoup(r.content, 'html.parser')

            # pages
            if page == 1:
                element = soup.find('ul', attrs={'class': 'pagination'})
                if element:
                    li_items = element.find_all('li')
                    max_page = int(li_items[-1].a['data-page-number'])

            # search results
            for result in soup.find_all('div', attrs={'class': 'product-listing-with-inputs-content'}):
                details = result.find('ul', attrs={'class': 'details'})

                doi_element = result.find('div', attrs={'data-doi': True})
                if doi_element:
                    doi = doi_element['data-doi']
                else:
                    doi = None

                title_box = details.find('li', attrs={'class': 'title'})
                title = title_box.h5.a.text.strip()

                # sort out cover and back matters etc
                if all([e in title.lower() for e in ['issue', 'volume', 'matter']]):
                    continue

                preview_url = self.base_settings['preview_url'] + title_box.h5.a['href']

                source_box = details.find('li', attrs={'class': 'source'})
                journal = source_box.a.text

                published_box = details.find('li', attrs={'class': 'published'})
                year_box = published_box.find('span', attrs={'class': 'date'})
                year = int(year_box.text[-4:])

                link_box = details.find('li', attrs={'class': None})
                access_element = link_box.find('div', attrs={'class': 'access-modal'})

                download_element = link_box.find('a', attrs={'data-pdf-content-id': True})
                if download_element:
                    fulltext_url = self.base_settings['preview_url'] + download_element['href']
                else:
                    fulltext_url = None

                self.results.append({
                    'publisher': 'cambridge',
                    'journal': journal,
                    'journal_shortname': self.journal_shortname,
                    'doi': doi,
                    'title': title,
                    'year': year,
                    'preview_url': preview_url,
                    'fulltext_url': fulltext_url,
                })
