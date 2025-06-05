from classes.Parsers import get_parser
from classes.Constants import DEMO_SEARCH_RESULTS
from classes.Utils import make_download_target
from pprint import pprint

if __name__ == '__main__':
    publisher = 'cambridge'

    search_result = DEMO_SEARCH_RESULTS[publisher][0]
    file_path = make_download_target(search_result, fulltext=False)['target']

    Parser = get_parser(publisher, file_path)
    result = Parser.parse()

    pprint(result.paper)
    pprint(result.authors)
