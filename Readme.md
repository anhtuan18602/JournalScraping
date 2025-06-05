# Journal Search, Download, Parse

## Requirements
This was tested with Python 3.9 on Mac OS X. Apart from the required python packages you will also have to install additional dependencies for the ```textract``` package to work on your system. If you do not set it up, data cannot be parsed from Nature fulltext articles. Please refer to the ```textract``` [docs](https://textract.readthedocs.io/).

## Publishers
- Elsevier
- Springer
- Wiley
- Oxford
- Cambridge
- Nature
- Taylor & Francis

## Usage
Generally, there are four steps:
1. Define a journals you want to get data from.
```python
journal = {
    'publisher': 'elsevier',
    'shortname': 'jbef',
    'identifiers': ['2214-6350']  
    # identifiers can be ISSN or other identifiers depending on the publisher
}
```

2. Use a search provider to gather article search results from a given range of years.
```python
SearchProvider = ElsevierSearch(journal['publisher'], 
                                journal['shortname'], 
                                journal['identifiers'], 
                                year_range=(2020, 2021))
SearchProvider.search()
search_results = SearchProvider.results
print(search_results)
```

3. Use the downloader to get the article preview.
```python
download_targets = []
for article in search_results:
    download_target = make_download_target(article)
    download_targets.append(download_target)

dl = ArticleDownloader(download_targets)
dl.download()
```

4. Parse the downloaded files for metadata.
```python
file_path = 'files/elsevier/jbef/previews/<DOI>.html'
Parser = ElsevierParser(file_path)
parse_result = Parser.parse()
print(parse_result)
```

## Note
Using this software might violate terms and conditions for the use of publisher's websites. Use at your own risk (or better don't). 