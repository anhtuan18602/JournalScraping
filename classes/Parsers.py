from bs4 import BeautifulSoup

from .Utils import match_emails
from datetime import datetime
import json
import textract
import re
import os


def get_parser(publisher, filepath):
    parser_map = {
        'elsevier': ElsevierParser,
        'springer': SpringerParser,
        'wiley': WileyParser,
        'tandf': TAndFParser,
        'nature': NatureParser,
        'oxford': OxfordParser,
        'cambridge': CambridgeParser
    }
    Parser = parser_map.get(publisher, lambda fp: "Parser does not exist exists")
    return Parser(filepath)


class FileParser:
    def __init__(self, fp):
        self.file_path = fp
        self.authors = []
        self.paper = []
        self.doi = None
        self.parsed = False
        self.file_content = self._read_contents()

    @property
    def institutions(self):
        return list(set([aff for author in self.authors for aff in author['affiliations']]))

    def _read_contents(self, file_encoding='utf-8'):
        with open(self.file_path, 'r', encoding=file_encoding) as f:
            return f.read()

    def parse(self):
        raise NotImplemented('You need to sub-class FileParser and implement the parse method.')


class ElsevierParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')
        self.doi = soup.find('meta', attrs={'name': 'dc.identifier'})['content']

        res = soup.find('script', attrs={'type': 'application/json', 'data-iso-key': '_0'})
        if not res:
            raise Exception('Cannot find json data structure in file. Wrong parser?')

        json_content = json.loads(res.string)
        meta_elements = json_content['authors']['content'][0]['$$']

        identified_authors = []
        identified_institutions = []
        for element in meta_elements:
            if element['#name'] == 'author':
                first_name, last_name = '', ''
                emails = []
                ref_ids = []
                for prop in element['$$']:
                    if prop['#name'] == 'given-name':
                        first_name = prop['_']
                    if prop['#name'] == 'surname':
                        dash = prop.get('_', False)
                        if dash:
                            last_name = dash
                        else:
                            if prop.get('$$', False):
                                last_name = prop['$$'][0].get('_', '')

                    if prop['#name'] == 'cross-ref':
                        if prop['$']['refid']:
                            ref_ids.append(prop['$']['refid'])
                    if prop['#name'] == 'e-address':
                        if prop['$']['type'] == 'email':
                            dash = prop.get('_', False)
                            if dash:
                                emails.append(dash)
                            else:
                                href = prop['$'].get('href', False)
                                if href:
                                    emails.append(href.replace('mailto:', ''))
                identified_authors.append({
                    'name': " ".join([first_name, last_name]),
                    'emails': emails,
                    'refids': ref_ids
                })

            if element['#name'] in ['affiliation']:
                eid = element['$']['id']
                name = ''
                for prop in element['$$']:
                    if prop['#name'] == 'textfn':
                        dash = prop.get('_', False)
                        if dash:
                            name = dash
                            continue
                        long = prop.get('__text__', False)
                        if long:
                            name = long
                            continue
                identified_institutions.append({
                    'refid': eid,
                    'name': name
                })

        for a in identified_authors:
            a['affiliations'] = []
            for i in identified_institutions:
                if i['refid'] in a['refids']:
                    a['affiliations'].append(i['name'])
            del (a['refids'])

        if not any([a['affiliations'] for a in identified_authors]):
            for a in identified_authors:
                a['affiliations'] = [aff['name'] for aff in identified_institutions]

        self.authors = identified_authors

        # print(json_content['abstracts'])
        print(' ')
        print(json_content)
        if 'abstracts' in json_content:
            if 'content' in json_content['abstracts']:
                if len(json_content['abstracts']['content']) == 2:
                    if '_' in json_content['abstracts']['content'][0]['$$'][0]:
                        if json_content['abstracts']['content'][0]['$$'][0]['_'] == 'Highlights' or json_content['abstracts']['content'][0]['$$'][0]['_'] == 'Highlight':
                            if '$$' in json_content['abstracts']['content'][1]:
                                if 0 <= 1 < len(json_content['abstracts']['content'][1]['$$']):
                                    if '$$' in json_content['abstracts']['content'][1]['$$'][1]:
                                        if '_' in json_content['abstracts']['content'][1]['$$'][1]['$$'][0]:
                                            abstract = json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['_']
                                        elif '$$' in json_content['abstracts']['content'][1]['$$'][1]['$$'][0]:
                                            if 2 < len(json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$']) and '_' in json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][2]:
                                                abstract = json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][0]['_'] + json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][2]['_']
                                            else:
                                                abstract = json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][0]['_']
                                        else:
                                            abstract = ''
                                    else:
                                        abstract = ''
                                else:
                                    abstract = ''
                            else:
                                abstract = ''
                        else:
                            if '$$' in json_content['abstracts']['content'][0]:
                                if 0 <= 1 < len(json_content['abstracts']['content'][0]['$$']):
                                    if '$$' in json_content['abstracts']['content'][0]['$$'][1]:
                                        if '_' in json_content['abstracts']['content'][0]['$$'][1]['$$'][0]:
                                            abstract = json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['_']
                                        elif '$$' in json_content['abstracts']['content'][0]['$$'][1]['$$'][0]:
                                            if 2 < len(json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$']) and '_' in json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][2]:
                                                abstract = json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][0]['_'] + json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][2]['_']
                                            else:
                                                abstract = json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][0]['_']
                                        else:
                                            abstract = ''
                                    else:
                                        abstract = ''
                                else:
                                    abstract = ''
                            else:
                                abstract = ''
                    else:
                        if json_content['abstracts']['content'][0]['$$'][0]['$$'][0]['_'] == 'Highlights':
                            if '$$' in json_content['abstracts']['content'][1]:
                                if 0 <= 1 < len(json_content['abstracts']['content'][1]['$$']):
                                    if '$$' in json_content['abstracts']['content'][1]['$$'][1]:
                                        if '_' in json_content['abstracts']['content'][1]['$$'][1]['$$'][0]:
                                            abstract = json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['_']
                                        elif '$$' in json_content['abstracts']['content'][1]['$$'][1]['$$'][0]:
                                            if 2 < len(json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$']) and '_' in json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][2]:
                                                abstract = json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][0]['_'] + json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][2]['_']
                                            else:
                                                abstract = json_content['abstracts']['content'][1]['$$'][1]['$$'][0]['$$'][0]['_']
                                        else:
                                            abstract = ''
                                    else:
                                        abstract = ''
                                else:
                                    abstract = ''
                            else:
                                abstract = ''
                else:
                    if '$$' in json_content['abstracts']['content'][0]:
                        if 0 <= 1 < len(json_content['abstracts']['content'][0]['$$']):
                            if '$$' in json_content['abstracts']['content'][0]['$$'][1]:
                                if '_' in json_content['abstracts']['content'][0]['$$'][1]['$$'][0]:
                                    abstract = json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['_']
                                elif '$$' in json_content['abstracts']['content'][0]['$$'][1]['$$'][0]:
                                    if 2 < len(json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$']) and '_' in json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][2]:
                                        abstract = json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][0]['_'] + json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][2]['_']
                                    else:
                                        abstract = json_content['abstracts']['content'][0]['$$'][1]['$$'][0]['$$'][0]['_']
                                else:
                                    abstract = ''
                            else:
                                abstract = ''
                        else:
                            abstract = ''
                    else:
                        abstract = ''
            else:
                abstract = ''
        else:
            abstract = ''

        meta_elements = soup.find_all('meta')
        relevant_paper = ['citation_title', 'citation_issue', 'citation_volume', 'citation_firstpage', 'citation_lastpage', 'citation_publication_date']
        filtered_elements_paper = [m for m in meta_elements if m.get('name', '') in relevant_paper]

        currentpaper = None
        currentpaper = {
            'title':  [],
            'abstract': [],
            'volume': [],
            'issue': [],
            'start': [],
            'end': [],
            'date': [],
            'author': [],
            'year': []
        }
        for e in filtered_elements_paper:
            if e['name'] == 'citation_volume':
                if currentpaper:
                    self.paper.append(currentpaper)
                currentpaper = {
                    'title':  [],
                    'abstract': [],
                    'volume': e['content'],
                    'issue': [],
                    'start': [],
                    'end': [],
                    'date': [],
                    'author': self.authors[0],
                    'year': []
                }
            if e['name'] == 'citation_title':
                currentpaper['title'] = e['content']
            if e['name'] == 'citation_issue':
                currentpaper['issue'] = e['content']
            if e['name'] == 'citation_firstpage':
                currentpaper['start'] = e['content']
            if e['name'] == 'citation_lastpage':
                currentpaper['end'] = e['content']
            if e['name'] == 'citation_publication_date':
                currentpaper['date'] = e['content']
                currentpaper['year'] = e['content']
            currentpaper['abstract'] = abstract
        #        print(type(currentpaper))
        self.paper = currentpaper



        self.parsed = True
        return self


class SpringerParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')

        content_type_element = soup.find('meta', attrs={'name': 'dc.type'})
        if content_type_element:
            content_type = content_type_element['content']
            if any([s.lower() in content_type.lower() for s in ['Announcement']]):
                return self

        doi_element = soup.find('meta', attrs={'name': 'DOI'})
        if doi_element:
            self.doi = doi_element['content']
        else:
            bib_doi = soup.find('li', attrs={'class': 'c-bibliographic-information__list-item--doi'})
            if bib_doi:
                doi_span = bib_doi.find('span', attrs={'class': 'c-bibliographic-information__value'})
                if doi_span:
                    self.doi = doi_span.a['href'].replace('https://doi.org/', '')

        meta_elements = soup.find_all('meta')
        relevant = ['citation_author', 'citation_author_email', 'citation_author_institution']
        filtered_elements = [m for m in meta_elements if m.get('name', '') in relevant]

        relevant_paper = ['dc.title', 'dc.description', 'prism.volume', 'prism.number', 'prism.startingPage', 'prism.endingPage', 'prism.publicationDate']
        filtered_elements_paper = [m for m in meta_elements if m.get('name', '') in relevant_paper]

        current = None
        for e in filtered_elements:
            if e['name'] == 'citation_author':
                if current:
                    self.authors.append(current)
                current = {
                    'name': e['content'],
                    'emails': [],
                    'affiliations': []
                }
            if e['name'] == 'citation_author_email':
                current['emails'].append(e['content'])
            if e['name'] == 'citation_author_institution':
                current['affiliations'].append(e['content'])
        self.authors.append(current)

        currentpaper = None
        for e in filtered_elements_paper:
            if e['name'] == 'dc.title':
                if currentpaper:
                    self.paper.append(currentpaper)
                currentpaper = {
                    'title': e['content'],
                    'abstract': None,
                    'volume': None,
                    'issue': None,
                    'start': None,
                    'end': None,
                    'date': None
                }
            if e['name'] == 'dc.description':
                currentpaper['abstract'] = e['content']
            if e['name'] == 'prism.volume':
                currentpaper['volume'] = e['content']
            if e['name'] == 'prism.number':
                currentpaper['issue'] = e['content']
            if e['name'] == 'prism.startingPage':
                currentpaper['start'] = e['content']
            if e['name'] == 'prism.endingPage':
                currentpaper['end'] = e['content']
            if e['name'] == 'prism.publicationDate':
                currentpaper['date'] = e['content']
#        print(type(currentpaper))
        self.paper = currentpaper

        self.parsed = True
        return self


class WileyParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')
        if any([t in self.file_content for t in ['ERRATUM', 'RETRACTION', 'CORRIGENDUM', 'Errata', 'FELLOW OF THE YEAR', 'AWARDS AND PRIZES', 'EDITORIAL']]):
            return self

        title_content = soup.find('meta', attrs={'property': 'og:title'})['content']
        if any([st.lower() in title_content.lower() for st in [
            'Cover Image', 'Issue Information', 'CORRIGENDUM', "Report of the", "BRATTLE GROUP PRIZES",
            'AMERICAN FINANCE ASSOCIATION', 'Participant Schedule', 'DIMENSIONAL FUND ADVISORS PRIZES',
            'Minutes of the', 'Call for Papers', 'AUTHOR INDEX', 'List of Reviewers', 'Accepted Articles',
            'Content:', 'Back Matter', 'Front Matter', 'Volume Information', 'ANNOUNCEMENT',
            'ASSOCIATION MEETINGS', "From the ExSec's Notebook", 'Participants in the AFA Program',
            'ANNUAL MEETING'
        ]]):
            return self

        if any([title_content == 'ANNOUNCEMENTS', title_content == 'MISCELLANEA']):
            return self

        self.doi = soup.find('meta', attrs={'name': 'dc.identifier'})['content']

        if soup.find('div', attrs={'class': 'loa-authors'}) is not None:
            if len(soup.find('div', attrs={'class': 'loa-authors'}).find_all('div', attrs={'class': 'accordion-tabbed__tab-mobile'})) != 0:
                author_tabs = soup.find('div', attrs={'class': 'loa-authors'}).find_all('div', attrs={
                    'class': 'accordion-tabbed__tab-mobile'})
            else:
                author_tabs = soup.find('div', attrs={'class': 'loa-authors'}).find_all('span', attrs={
                    'class': 'accordion-tabbed__tab-mobile'})
            for tab in author_tabs:
                name = tab.a.span.text

                emails = []
                if len(tab.div.find_all('ul', attrs={'class': 'sm-account'})) != 0:
                    for account_link in tab.div.find_all('ul', attrs={'class': 'sm-account'}):
                        if account_link.li.a is not None:
                            if 'mailto:' in account_link.li.a['href']:
                                emails.append(account_link.li.a.span.text)

                affiliations = []
                for aff_para in tab.div.find_all('p'):
                    if not aff_para.get('class', False):
                        if not aff_para.find('b'):
                            affiliations.append(aff_para.text)
                        elif aff_para.b.text == "Correspondence":
                            break

                self.authors.append({
                    'name': name,
                    'emails': emails,
                    'affiliations': affiliations
                })
        else:
            self.authors = []



        abstract_group = soup.find('div', class_ = 'abstract-group')
        if hasattr(abstract_group, 'p'):
            abstract = abstract_group.p.text
        else:
            if soup.find('div', attrs={'class':'article-section__content'}):
                abstract = soup.find('div', attrs={'class':'article-section__content'}).p.text
            else:
                abstract = None

        meta_elements = soup.find_all('meta')
        relevant_paper = ['citation_title', 'citation_volume', 'citation_issue', 'citation_firstpage', 'citation_lastpage', 'citation_publication_date']
        filtered_elements_paper = [m for m in meta_elements if m.get('name', '') in relevant_paper]

        currentpaper = None
        currentpaper = {
            'title':  [],
            'abstract': abstract,
            'doi': self.doi,
            'volume': [],
            'issue': [],
            'start': [],
            'end': [],
            'date': [],
            'author': [],
            'year': []
        }
        for e in filtered_elements_paper:
            if e['name'] == 'citation_title':
                currentpaper['title'] = e['content']
            if e['name'] == 'Description':
                currentpaper['abstract'] = e['content']
            if e['name'] == 'citation_volume':
                currentpaper['volume'] = e['content']
            if e['name'] == 'citation_issue':
                currentpaper['issue'] = e['content']
            if e['name'] == 'citation_firstpage':
                currentpaper['start'] = e['content']
            if e['name'] == 'citation_lastpage':
                currentpaper['end'] = e['content']
            if e['name'] == 'citation_publication_date':
                currentpaper['date'] = e['content']
                currentpaper['year'] = e['content']
            if 0 < len(self.authors):
                currentpaper['author'] = self.authors[0]
        #        print(type(currentpaper))
        self.paper = currentpaper

        self.parsed = True
        return self


class TAndFParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')
        self.doi = soup.find('meta', attrs={'name': 'dc.Identifier', 'scheme': 'doi'})["content"]

        author_spans = soup.find_all('span', attrs={'class': 'contribDegrees'})
        for element in author_spans:
            name = element.a.contents[0].strip()

            a_element = element.a.find('span', attrs={'class': 'overlay'})
            affiliations = [aff.strip() for aff in a_element.contents[0].split(';')]

            emails = []
            e_element = element.a.find('span', attrs={'class': 'corr-email'})
            if e_element:
                emails.append(e_element.span.text.strip())

            self.authors.append({
                'name': name,
                'emails': emails,
                'affiliations': affiliations
            })
        self.parsed = True
        return self


class NatureParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')
        self.doi = soup.find('meta', attrs={'name': 'DOI'})['content']

        meta_elements = soup.find_all('meta')
        relevant = ['citation_author', 'citation_author_institution']
        filtered_elements = [m for m in meta_elements if m.get('name', '') in relevant]

        authors = []
        current = None
        for e in filtered_elements:
            if e['name'] == 'citation_author':
                if current:
                    authors.append(current)
                current = {
                    'name': e['content'],
                    'emails': [],
                    'affiliations': []
                }
            if e['name'] == 'citation_author_institution':
                current['affiliations'].append(e['content'])
        authors.append(current)

        # here, we need to find e-mail addresses from full-texts and match them accordingly
        self.authors = match_emails(self._emails_from_fulltext(), authors)

        self.parsed = True
        return self

    def _emails_from_fulltext(self):
        path, preview_filename = os.path.split(self.file_path)
        path = path.replace('/previews', '')
        fulltext_filename = preview_filename[:-4] + 'pdf'
        full_path = os.path.join(path, 'fulltexts', fulltext_filename)
        if os.path.isfile(full_path):
            text = textract.process(full_path).decode('utf-8')
            matches = re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)
            return list({address for address in matches})
        else:
            return []


class OxfordParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')
        json_element = soup.find('script', attrs={'type': 'application/ld+json'})
        if not json_element:
            print("no data in", self.file_path)

            title_element = soup.find('title')
            if title_element:
                if title_element.text == "Validate User":
                    print('..suspected captcha page')

            return

        json_data = json.loads(json_element.text)

        self.doi = json_data['url'].replace('https://dx.doi.org/', '')

        authors = []
        if 'author' in json_data:
            for author in json_data['author']:
                split_name = [e.strip() for e in author['name'].split(',')]
                aname = " ".join(reversed(split_name))
                affils = []
                if author.get('affiliation', False):
                    affils.append(author['affiliation'])
                authors.append({
                    'name': aname,
                    'affiliations': affils,
                    'emails': []
                })

        for correspondence_element in soup.find_all('div', attrs={'class': 'info-author-correspondence'}):
            for author in authors:
                name_elements = [el for el in author['name'].split(' ') if len(el) > 2]
                if all(e in correspondence_element.text for e in name_elements):
                    if correspondence_element.a is not None:
                        author['emails'].append(correspondence_element.a['href'].replace('mailto:', ''))

        self.authors = authors


        abstract_section = soup.find('section', class_ = 'abstract')
        if abstract_section is not None:
            abstract = abstract_section.text
        else:
            abstract = ''

#        meta_citation_volume = soup.find('meta', {'name': 'citation_volume'})
#        meta_citation_issue = soup.find('meta', {'name': 'citation_volume'})

        meta_elements = soup.find_all('meta')
        relevant_paper = ['citation_issue', 'citation_volume', 'citation_publication_date']
        filtered_elements_paper = [m for m in meta_elements if m.get('name', '') in relevant_paper]

        currentpaper = None
        for e in filtered_elements_paper:
            if e['name'] == 'citation_volume':
                if currentpaper:
                    self.paper.append(currentpaper)
                if 0 < len(authors):
                    currentpaper = {
                        'title':  json_data['name'],
                        'abstract': abstract,
                        'doi': self.doi,
                        'volume': e['content'],
                        'issue': [],
                        'start': json_data['pageStart'],
                        'end': json_data['pageEnd'],
                        'date': json_data['datePublished'],
                        'author': authors[0],
                    }
                else:
                    currentpaper = {
                        'title':  json_data['name'],
                        'abstract': abstract,
                        'volume': e['content'],
                        'issue': [],
                        'start': json_data['pageStart'],
                        'end': json_data['pageEnd'],
                        'date': json_data['datePublished'],
                        'author': authors,
                    }
            if e['name'] == 'citation_issue':
                currentpaper['issue'] = e['content']
            if e['name'] == 'citation_publication_date':
                currentpaper['year'] = e['content']
        #        print(type(currentpaper))
        self.paper = currentpaper


#        currentpaper = {
#            'title': json_data['name'],
#            'abstract': abstract,
#            'volume': meta_citation_volume['content'],
#            'issue': meta_citation_issue['content'],
#            'start': json_data['pageStart'],
#            'end': json_data['pageEnd'],
#            'date': json_data['datePublished']
#        }
#        self.paper = currentpaper

        self.parsed = True
        return self


class CambridgeParser(FileParser):
    def parse(self):
        soup = BeautifulSoup(self.file_content, 'html.parser')

        title = soup.find('meta', attrs={'property': 'og:title'})['content']
        #print(title)
        if any([st.lower() in title.lower() for st in ['ERRATUM', 'CORRIGENDUM']]):
            return self

        contributor_details = soup.find('div', attrs={'class': 'contributors-details'})
        if contributor_details is not None:
            contribs = contributor_details.find('div', attrs={'class': ['row', 'authors']})
    #        author_details = contributor_details.find('div', attrs={'class': 'authors-details', 'id': 'authors-details'})
            if contributor_details.find('dl', attrs={'class': 'authors-details', 'id': 'authors-details'}) is not None:
                #print("whattt")
                author_details = contributor_details.find('dl', attrs={'class': 'authors-details', 'id': 'authors-details'})

                temp_authors = []
                for contrib_box in contribs.find_all('div', attrs={'class': 'contributor'}):
                    temp_authors.append({'name': contrib_box.a.text.strip(), 'emails': [], 'affiliations': []})

                authors = []
                author_boxes = author_details.find_all('div', attrs={'class': 'row author'})
                #print(author_boxes)
                for abox_details in author_boxes:
                    #print(author_box)
                    #abox_details = author_box.find('div', attrs={'class': 'row author'})
                    #print("authorbox")
                    #print(abox_details)
                    if abox_details:
                        a_name = abox_details['data-test-author'].strip()
                        a_name_elements = {e for e in a_name.split(' ')}

        #                a_content = author_box.find('div', attrs={'class', 'content'}).div.span.text.strip()
                        a_content = abox_details.find('dd', attrs={'class', 'content'}).div.span.text.strip()
                        a_content_elements = {e.strip() for e in a_content.split(',')}

                        non_name_elements = a_content_elements.difference(a_name_elements)

                        combination = " ".join(non_name_elements)
                        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', combination)
                        emails = []
                        if email_match:
                            email = email_match.group()

                            if email:
                                combination = combination.replace(email, '')
                            emails.append(email)
                        affiliation = combination.strip()

                        authors.append({
                            'name': a_name,
                            'affiliations': [affiliation],
                            'emails': emails
                        })

                emails = set()
                if not authors:
                    corresponding = author_details.find('div', attrs={'row'})
                    if corresponding:
                        for element in corresponding.find_all('div', attrs={'class': 'corresp'}):
                            emails.add(element.a['href'].replace('mailto:', ''))

                    authors = match_emails(emails, temp_authors)

            else:
                authors = [{'name': name.span.text} for name in contribs.find_all('div', attrs = {'class': 'contributor-type__contributor'})]
        else:
            authors = [{'name': ''}]
        
        self.doi = soup.find('meta', attrs={'name': 'citation_doi'})['content']
        self.authors = authors

        meta_elements = soup.find_all('meta')
        """
        if self.doi == "10.1017/S0022109024000371":
            with open('testmeta.json', 'w', encoding='utf-8') as f:
                cleaned = [str(tag) for tag in meta_elements] 
                json.dump(cleaned, f, indent=4)
        """
        relevant_paper = ['citation_title', 'citation_issue', 'citation_volume', 'citation_firstpage', 'citation_lastpage', 'citation_publication_date', 'citation_abstract']
        filtered_elements_paper = [m for m in meta_elements if m.get('name', '') in relevant_paper]

        date = soup.find('div',attrs={'class':'row published-date'}).find('strong').text.strip()
        date = datetime.strptime(date, "%d %B %Y")
        date = date.strftime("%Y/%m/%d")
        currentpaper = None
        currentpaper = {
            'title':  [],
            'abstract': [],
            'doi': self.doi,
            'volume': [],
            'issue': [],
            'start': [],
            'end': [],
            'date': date,
            'author': self.authors[0],
            'year': date[:4]
        }
        for e in filtered_elements_paper:
            if e['name'] == 'citation_title':
                currentpaper['title'] = e['content']
            if e['name'] == 'citation_volume':
                currentpaper['volume'] = e['content']
            if e['name'] == 'citation_issue':
                currentpaper['issue'] = e['content']
            if e['name'] == 'citation_firstpage':
                currentpaper['start'] = e['content']
            if e['name'] == 'citation_lastpage':
                currentpaper['end'] = e['content']
            if e['name'] == 'citation_publication_date':
                currentpaper['date'] = e['content']
                currentpaper['year'] = e['content']
            if e['name'] == 'citation_abstract':
                currentpaper['abstract'] = e['content']
        #        print(type(currentpaper))
        self.paper = currentpaper


        return self
