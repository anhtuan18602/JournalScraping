from classes.Downloaders import ArticleDownloader, make_download_target
from classes.Constants import DEMO_SEARCH_RESULTS

if __name__ == '__main__':
    publisher = 'cambridge'

    demo_search_results = DEMO_SEARCH_RESULTS[publisher]

    download_targets = []
    for article in demo_search_results:
        download_target = make_download_target(article, fulltext=False)
        download_targets.append(download_target)

    dl = ArticleDownloader(download_targets)
    dl.download()
