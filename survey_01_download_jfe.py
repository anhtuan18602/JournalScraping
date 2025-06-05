
from classes.SearchProviders import get_search_provider
from classes.Constants import DEMO_SEARCH_INPUTS
from classes.Downloaders import ArticleDownloader, make_download_target
from classes.Constants import DEMO_SEARCH_RESULTS
from classes.Parsers import get_parser
from pprint import pprint
import csv
import pandas as pd


if __name__ == '__main__':

    years = (2016, 2020)

    journal = 'jbf'

    journal_map = {
        'jf': {'publisher': 'wiley', 'identifier': '1540-6261'}, ## Journal of Finance
        'rfs': {'publisher': 'oxford', 'identifier': 'The Review of Financial Studies'}, ## Review of Financial Studies
        'jfe': {'publisher': 'elsevier', 'identifier': '0304-405X'}, ## Journal of Financial Economics
        'rf': {'publisher': 'oxford', 'identifier': 'Review of Finance'}, ## Review of Finance
        'jfqa': {'publisher': 'cambridge', 'identifier': 'FB35548FF614F4556E96D01FA2CB412E'}, ## Journal of Financial and Quantitative Analysis 
        'jbf': {'publisher': 'elsevier', 'identifier': '0378-4266'}, ## Journal of Banking and Finance 
        'ecmt': {'publisher': 'wiley', 'identifier': '1468-0262'}, 
        ## needs Management Science
    }
    journalinfo = journal_map.get(journal)

    publisher = journalinfo['publisher']
    search_inputs = {
        'publisher': journalinfo['publisher'],
        'shortname': journal,
        'identifiers': [journalinfo['identifier']]
    }
    print(years)
    print(search_inputs)
    SearchProvider = get_search_provider(search_inputs['publisher'], search_inputs['shortname'], search_inputs['identifiers'], year_range=years)

    SearchProvider.search()

    search_results = SearchProvider.results

    download_targets = []
    for article in search_results:
        download_target = make_download_target(article, fulltext=False)
        download_targets.append(download_target)

    dl = ArticleDownloader(download_targets)
    dl.download()


    # Parse

    parse_results = []
    for files in download_targets:
        file_path = files['target']
        Parser = get_parser(publisher, file_path)
        parse_result = Parser.parse()
        if parse_result.paper is not None:
            parse_results.append(parse_result.paper)

    print(parse_results)
    print(type(parse_results))
    print(type(parse_results[0]))
#    print(parse_results[0].keys())


    # write

    papers = pd.DataFrame()
    for i in parse_results:
        df = pd.json_normalize(i)
        papers = papers.append(df)


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
