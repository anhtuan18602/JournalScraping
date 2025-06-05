
from classes.SearchProviders import get_search_provider
from classes.Constants import DEMO_SEARCH_INPUTS
from classes.Downloaders import ArticleDownloader, make_download_target, WileyArticleDownloader
from classes.Constants import DEMO_SEARCH_RESULTS
from classes.Parsers import get_parser
from classes.Keys import ELSEVIER_API_KEY
from classes.ElsevierScraper import ElsevierMetadataScraper
from pprint import pprint
import csv
import pandas as pd


if __name__ == '__main__':

    years = (2024, 2024)
    
    ## Specify Chrome installation path here
    binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"

    journal = 'jbf'


    
    journal_map = {
            'jf': {'publisher': 'wiley', 'identifier': '1540-6261','name':'Journal of Finance'},
            'rfs': {'publisher': 'oxford', 'identifier': 'The Review of Financial Studies','name': 'The Review of Financial Studies'},
            'rf': {'publisher': 'oxford', 'identifier': 'Review of Finance','name': 'Review of Finance'},
            'jfe': {'publisher': 'elsevier', 'identifier': '0304-405X', 'name': 'Journal of Financial Economics'},
            'jfqa': {'publisher': 'cambridge', 'identifier': 'FB35548FF614F4556E96D01FA2CB412E','name':'Journal of Financial and Quantitative Analysis'},
            'jbf': {'publisher': 'elsevier', 'identifier': '0378-4266','name':'Journal of Banking and Finance'},
            'ecmt': {'publisher': 'wiley', 'identifier': '1468-0262','name':'Econometrica'},
        }
    journalinfo = journal_map.get(journal)

    publisher = journalinfo['publisher']

    ## Elsevier uses their own api
    if publisher == "elsevier":
        papers = []
        for year in range(years[0], years[1] + 1):
            scraper = ElsevierMetadataScraper(ELSEVIER_API_KEY, year, journalinfo["name"])
            papers.append(pd.DataFrame(scraper.fetch_metadata()))
        papers = pd.concat(papers)
    else :   
        
        
        search_inputs = {
            'publisher': journalinfo['publisher'],
            'shortname': journal,
            'identifiers': [journalinfo['identifier']]
        }
        print(years)
        print(search_inputs)
        SearchProvider = get_search_provider(search_inputs['publisher'], search_inputs['shortname'], search_inputs['identifiers'], binary_location, year_range=years)

        SearchProvider.search()

        search_results = SearchProvider.results
        print(search_results[0])
        download_targets = []
        for article in search_results:
            download_target = make_download_target(article, fulltext=False)
            download_targets.append(download_target)
        
        
        print(download_targets[0])
        if publisher in ["oxford","wiley"]:
            dl = WileyArticleDownloader(download_targets,output_results=True)
        else:
            dl = ArticleDownloader(download_targets,output_results=True)
        dl.download()


        # Parse

        parse_results = []
        for files in download_targets:
            file_path = files['target']
            Parser = get_parser(publisher, file_path)
            parse_result = Parser.parse()
            if parse_result.paper is not None:
                parse_results.append(parse_result.paper)

        #print(parse_results)
        #print(type(parse_results))
        #print(type(parse_results[0]))
    #    print(parse_results[0].keys())


        # write

        dfs = []
        for i in parse_results:
            df = pd.json_normalize(i)
            dfs.append(df)

        papers = pd.concat(dfs, ignore_index=True)
        SearchProvider.driver.quit()


    keywords = [
            'experiment',
            'experiments',
            'experimental',
            'laboratory',
            'field experiment',
            'field experiments'
    ]
    keywords_not = [
        'natural experiment',
        'quasi-experiment',
        'randomized experiment',
        'counterfactual experimental'
        'quasi-natural experiment',
        'quasi-experimental'
    ]

    
    papers['keywords_title'] = papers['title'].str.contains('|'.join(keywords), regex=True, case=False)
    papers['keywords_abstract'] = papers['abstract'].str.contains('|'.join(keywords), regex=True, case=False)
    papers['keywords_not_title'] = papers['title'].str.contains('|'.join(keywords_not), regex=True, case=False)
    papers['keywords_not_abstract'] = papers['abstract'].str.contains('|'.join(keywords_not), regex=True, case=False)

    print(papers)
    papers.to_excel('papers_' + str(years[0]) + '_' + str(years[1]) + '_' + journal + '.xlsx', index = False, header=True)

    

