REPLACEMENTS = {
    'ä': 'ae',
    'ö': 'oe',
    'ü': 'ue',
    'ß': 'ss'
}

SPLITTERS = {
    'chars': ['-', "'"],
    'replacements': ['-', '_', '']
}

DEMO_SEARCH_INPUTS = {
    'elsevier': {
        'publisher': 'elsevier',
        'shortname': 'jfe',
        'identifiers': ['0304-405X']
    },
    'springer': {
        'publisher': 'springer',
        'shortname': 'exex',
        'identifiers': ['1386-4157', '1573-6938']
    },
    'wiley': {
        'publisher': 'wiley',
        'shortname': 'jf',
        'identifiers': ['1540-6261']
    },
    'tandf': {
        'publisher': 'tandf',
        'shortname': 'tcpo20',
        'identifiers': ['tcpo20']
    },
    'nature': {
        'publisher': 'nature',
        'shortname': 'nathumbehav',
        'identifiers': ['nathumbehav']
    },
    'oxford': {
        'publisher': 'oxford',
        'shortname': 'rfs',
        'identifiers': ['The Review of Financial Studies']
    },
    'cambridge': {
        'publisher': 'cambridge',
        'shortname': 'jfqa',
        'identifiers': ['FB35548FF614F4556E96D01FA2CB412E']
    }
}

DEMO_SEARCH_RESULTS = {
    'elsevier': [
        {
            'doi': '10.1016/j.jbef.2019.03.007',
            'fulltext_url': 'https://www.sciencedirect.com/science/article/pii/S2214635018302715/pdfft?md5=0c0f91cd66caefa4234050f18e76d6a6&pid=1-s2.0-S2214635018302715-main.pdf',
            'journal': 'Journal of Behavioral and Experimental Finance',
            'journal_shortname': 'jbef',
            'preview_url': 'https://www.sciencedirect.com/science/article/pii/S2214635018302715',
            'publisher': 'elsevier',
            'title': 'An oTree-based flexible architecture for financial market experiments',
            'year': 2020
        }
    ],
    'springer': [
        {
            'publisher': 'springer',
            'journal': 'Experimental Economics',
            'journal_shortname': 'exex',
            'doi': '10.1007/s10683-019-09609-y',
            'title': 'Voting on the threat of exclusion in a public goods experiment',
            'year': 2020,
            'preview_url': 'https://link.springer.com/article/10.1007/s10683-019-09609-y',
            'fulltext_url': 'https://link.springer.com/content/pdf/10.1007/s10683-019-09609-y.pdf'
        }
    ],
    'wiley': [
        {
            'doi': '10.1002/wcc.636',
            'fulltext_url': 'https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/wcc.636?download=true',
            'journal': 'Wiley Interdisciplinary Reviews: Climate Change',
            'journal_shortname': 'wires',
            'preview_url': 'https://onlinelibrary.wiley.com/doi/10.1002/wcc.636',
            'publisher': 'wiley',
            'title': 'A history of the global carbon budget',
            'year': '2020'
        }
    ],
    'tandf': [
        {
            'doi': '10.1080/14693062.2020.1759499',
            'fulltext_url': 'https://www.tandfonline.com/doi/pdf/10.1080/14693062.2020.1759499',
            'journal': 'Climate Policy',
            'journal_shortname': 'tcpo20',
            'preview_url': 'https://www.tandfonline.com/doi/full/10.1080/14693062.2020.1759499',
            'publisher': 'tandf',
            'title': 'Public support for aviation policy measures in Sweden',
            'year': '2020'
        }
    ],
    'nature': [
        {
            'doi': '10.1038/s41562-019-0793-1',
            'fulltext_url': 'https://www.nature.com/articles/s41562-019-0793-1.pdf',
            'journal': 'Nature Human Behaviour',
            'journal_shortname': 'nathumbehav',
            'preview_url': 'https://www.nature.com/articles/s41562-019-0793-1',
            'publisher': 'nature',
            'title': 'How people decide what they want to know',
            'year': '2020'
        }
    ],
    'oxford': [
        {
            'doi': '10.1093/rfs/hhaa004',
            'fulltext_url': None,
            'journal': 'The Review of Financial Studies',
            'journal_shortname': 'rfs',
            'preview_url': 'https://academic.oup.com/rfs/article/33/11/5416/5713526?searchresult=1',
            'publisher': 'oxford',
            'title': 'Monthly Payment Targeting and the Demand for Maturity',
            'year': 2020
        }
    ],
    'cambridge': [
        {
            'doi': '10.1017/S0022109019000681',
            'fulltext_url': None,
            'journal': 'Journal of Financial and Quantitative Analysis',
            'journal_shortname': 'jfqa',
            'preview_url': 'https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/emerging-markets-are-catching-up-economic-or-financial-integration/8AD85E915AE344AA9DA3C2F1D055A114',
            'publisher': 'cambridge',
            'title': 'Emerging Markets Are Catching Up: Economic or Financial Integration?',
            'year': 2020
        }
    ]
}
