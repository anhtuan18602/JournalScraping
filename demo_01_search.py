from classes.SearchProviders import get_search_provider
from classes.Constants import DEMO_SEARCH_INPUTS
from pprint import pprint

if __name__ == '__main__':
    publisher = 'elsevier'
    years = (2010, 2010)

    search_inputs = DEMO_SEARCH_INPUTS[publisher]
    SearchProvider = get_search_provider(search_inputs['publisher'], search_inputs['shortname'], search_inputs['identifiers'], year_range=years)

    SearchProvider.search()

    pprint(SearchProvider.results)
    pprint(len(SearchProvider.results))
