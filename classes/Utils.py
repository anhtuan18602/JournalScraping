import os

from re import sub
from html import unescape
from unidecode import unidecode
from fake_useragent import UserAgent

from .Constants import REPLACEMENTS, SPLITTERS
import random

"""
with open("user-agents.txt", "r", encoding="utf-8") as f:
    USER_AGENTS = [line.strip() for line in f if line.strip()]
"""

ua = UserAgent()

#print(ua.chrome)
def get_user_agent(as_header=True):
    
    """
    ua_string = random.choice(USER_AGENTS)
    
    return  ua_header if as_header else ua_string
    """
    ua_header = {
                    'User-Agent': ua.chrome,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
                    "Cookie": "MAID=nR+/w58JnbUsAuPViqHF7g==; userRandomGroup=50; osano_consentmanager_uuid=dcb8aa55-fe02-476b-8a1c-f07ffa32d718; osano_consentmanager=iTobB2d7w_pQy7yxdAY16k5GjShvCvlAKn4TmVxyRK3FFbxnSbWRATZHrp1CrVOVM5Jes0ZDQjUgZFri4_uob7aXwOdF4FzYY1nRdsB1hq5Nn6xYRDFmli85S7gGJr-uezgVZDSFlh_iyHYlaXhC5b7AOVOFaxwu55KzNeSR9X84YA8L_xaPGOWA0pZ41vA2WLphjKqmtP_GowBuyvSkhCGNSxfwfHcINis_zqi83wj75O1tBqeQRr60Ap65QNgLdQW4HdS-uEbFPz08q12z0LShph2tLBeDxGk8Ztw12jib62GVDggUaxUdqWKMziV4; MACHINE_LAST_SEEN=2025-06-03T05%3A20%3A42.086-07%3A00; JSESSIONID=F7BE3DF59320D61B9E8761A6BF032964; __cf_bm=8iWh7ldH0CWuCxiulZTiqh1BH59OIyVydMsW0dH8AKM-1748953242-1.0.1.1-Gf3kzf5iU0KW84q59TVXqz.7_O.p3DurMEj8ftRHDB0xTxV8eUJ4c0RB4tbmEhKYwWVBD1AqAWcp5rmgyrhSN_GwDIaFCTjZI1k7r0xwVrrqtcRuUw75z72Bo63.3Ggz; cf_clearance=t0_se0AYtC9pKBZc1iVZRl2ocw1QITfQCda_RVDb1ok-1748953244-1.2.1.1-oWtAdhKA9CNr2fj8iozc8Pg7eU7m_vF6B0Ib.JNN_HJWrljwN0b8ihaOmP6_5vgtKGMfdCqCWoHiv.bOb9jUHZGfhhtykKfJDqAGPwzxHn6.IM9DvhTdQ61Q6_lDXPektqfg1Q_7Sl0EbE_29KlwN9NXoH_0JIP2BlzXZOuU53L.cny28TsMEefwcuvKhR9qJrV7.ErrhiR480RPWAJEP0EWhZW2L2CTiL9WpyZRkR2txzeGnITz9VfSRsk1bqbR65qOIfhTt1XGODOBwL9x47R23cA3FwNWTVcv4RLownVRUf70CcN92DVNKeZ5XIQcMvmV_qqlAR6zCf9UBWRh217GZY938eLm70DTYzfW0kE",
                    "Upgrade-Insecure-Requests": "1",
                }
    return ua_header if as_header else ua.chrome
def strip_html(string):
    # requires sub from re, unidecode from unidecode and unescape from html
    # first encodes html special characters
    # then unidecodes these special characters
    # then strips html tags
    return sub(r'<[^<]+?>', '', unidecode(unescape(string)))


def make_download_target(article, fulltext=False, base_dir='files'):
    ft_map = {
        True: {
            'url': 'fulltext_url',
            'path': 'fulltexts',
            'ext': '.pdf'
        },
        False: {
            'url': 'preview_url',
            'path': 'previews',
            'ext': '.html'
        }
    }
    return {
        'url': article[ft_map[fulltext]['url']],
        'target': os.path.join(base_dir,
                               article['publisher'],
                               article['journal_shortname'],
                               ft_map[fulltext]['path'],
                               article['doi'].replace('/', '--') + ft_map[fulltext]['ext'])
    }

def match_emails(emails_to_match, authors):
    matched = []
    authors_to_match = authors

    used_emails = []
    used_authors = []
    # print('start', authors_to_match, emails_to_match)

    for author in [a for a in authors_to_match if a not in used_authors]:
        base_segments = author['name'].lower().split(" ")
        # print(base_segments)

        # if names contain replaceable characters add segments with replacements
        replace_segments = []
        for s in base_segments:
            replace_segments.append(s)
            for replacement_candidate in REPLACEMENTS.keys():
                if replacement_candidate in s:
                    replace_segments.append(s.replace(replacement_candidate, REPLACEMENTS[replacement_candidate]))
        # print(replace_segments)

        # if names contain a splitting character, we add it with the char and without
        segments = []
        for s in replace_segments:
            if any(spl in s for spl in SPLITTERS['chars']):
                for splitter in SPLITTERS['chars']:
                    if splitter in s:
                        parts = s.split(splitter)
                        additions = [sp_replacement.join(parts) for sp_replacement in SPLITTERS['replacements']]
                        additions += parts
                        segments += additions
            else:
                segments.append(s)

        # apply unidecode to make segments email friendly
        decoded_segments = [unidecode(s) for s in segments]

        # remove duplicates and remove segments shorter than three letters,
        # as they tend to match top level domain endings
        segments = [s for s in set(decoded_segments) if len(s) > 2]

        # sort segments by length, longest first
        segments.sort(key=len)
        segments.reverse()

        # print('check', author)
        for email in [e for e in emails_to_match if e not in used_emails]:
            # print('with', email)
            # we do not use an any() construct here, so we can break as soon as we find a segment
            # this is important, because the segments are now sorted by length, descending
            # that is, we try to find the longest sequence of characters first and abort if we find it.
            for segment in segments:
                if segment in email.lower():
                    # matched.append((author, email))
                    author['emails'].append(email)
                    used_authors.append(author)
                    used_emails.append(email)
                    # print('match found', author, email)
                    break

        # remove any potential duplicates
        author['emails'] = list(set(author['emails']))

    return authors