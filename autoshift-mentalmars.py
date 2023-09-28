import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone

from common import _L, DEBUG, DIRNAME, INFO
# from typing import (Callable, ContextManager, Dict, Generic, Iterable,
#                     Iterator, Optional, TypeVar)

webpages= [{ 
        "game": "Borderlands 2", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-2-golden-keys/",
        "platform_ordered_tables": [
                "universal",
                "universal",
                "pc",
                "xbox",
                "psn",
                "universal",
                "discard"
            ]
    }]

#BL2 = ["universal-expirable", "universal-unexpirable","pc","xbox","psn","universal-event"]


def remap_dict_keys(dict_keys):
    # List of table headings to be mapped to standard values
    # Here in case of variation in table headings
    heading_map = {
        'SHiFT Code': 'code',
        'Expires': 'expires', 
        'Reward': 'reward'
    }

    return dict((heading_map[key], dict_keys[key]) if key in heading_map else (key, value) for key, value in dict_keys.items())


# convert headings to standard headings
def cleanse_codes(codes):
    clean_codes = []
    for code in codes:

        # standardise the table headings
        clean_code = remap_dict_keys(code)

        # Clean up text from expiry date
        if "expires" in clean_code:
            clean_code.update({"expires" : clean_code.get("expires").replace('Expires: ', '')})
        else:
            clean_code.update({"expires" : "Unknown"})

        # convert expiries to dates
        # TODO 

        clean_codes.append(clean_code)

    return clean_codes

def scrape_codes(webpage):
    r = requests.get(webpage.get("sourceURL"))
    #record the time we scraped the URL 
    scrapedDateAndTime = datetime.now(timezone.utc)
    print(scrapedDateAndTime)
    # print(r.content)

    soup = BeautifulSoup(r.content, 'html.parser') # If this line causes an error, run 'pip install html5lib' or install html5lib
    # print(soup.prettify())

    figures = soup.find_all("figure")

    #headers = []
    code_tables = []

    table_count=0
    for figure in figures: 
        table_html = figure.find(lambda tag: tag.name=='table') 

        table_header = []
        code_table = []

        # Convert the HTML table into a Python Dict: 
        # Tip from: https://stackoverflow.com/questions/11901846/beautifulsoup-a-dictionary-from-an-html-table
        table_header = [header.text for header in table_html.find_all('th')]
        code_table = [{table_header[i]: cell.text for i, cell in enumerate(row.find_all('td'))}
                for row in table_html.find('tbody').find_all('tr')]

        # If we find more tables on the webpage than we were expecting, error
        if table_count+1 > len(webpage.get("platform_ordered_tables")):
            _L.error("ERROR: There are more tables on the webpage than configured")
            # TODO _L.error("ERROR: Unexpected table has headings of: " + header)
            # Skip to the next table iteration
            continue

        # Only keep any tables not marked to  discard
        if webpage.get("platform_ordered_tables")[table_count] != "discard":
            # Clean the results up 
            code_table = cleanse_codes(code_table)
            code_tables.append({
                "game" : webpage.get("game"), 
                "platform" : webpage.get("platform_ordered_tables")[table_count], 
                "sourceURL" : webpage.get("sourceURL"),
                "archived" : scrapedDateAndTime,
                "codes" : code_table
            })

        #print("Table Number: " + str(table_count))
        # print("HEADER CLEAN: " + str(table_count))
        # print(headers_clean)
        #print("HEADER: " + str(i) + " : " + header)
        #print("RESULT: " + str(i)+ " : " + table)

        table_count+=1
    _L.debug(json.dumps(code_tables,indent=2, default=str))
    return code_tables


def generateAutoshiftJSON(code_tables): 
    autoshiftcodes = []
    for code_table in code_tables:
        for code in code_table.get("codes"):
            autoshiftcodes.append({
                "code": code.get("code"),
                "type": "shift",
                "game": code_table.get("game"),
                "platform": code_table.get("platform"),
                "reward": code.get("reward"),
                "archived": code_table.get("archived"),
                "expires": code.get("expires"),
                "link": code_table.get("sourceURL")
            })
    return json.dumps(autoshiftcodes,indent=2, default=str)

def setup_argparser():
    import argparse
    import textwrap

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-u", "--user",
                        default=None,
                        help=("User login you want to use "
                              "(optional. You will be prompted to enter your "
                              " credentials if you didn't specify them here)"))
    parser.add_argument("-p", "--pass",
                        help=("Password for your login. "
                              "(optional. You will be prompted to enter your "
                              " credentials if you didn't specify them here)"))
    parser.add_argument("--golden",
                        action="store_true",
                        help="Only redeem golden keys")
    parser.add_argument("--non-golden", dest="non_golden",
                        action="store_true",
                        help="Only redeem non-golden keys")
    # parser.add_argument("--games",
    #                     type=str, required=True,
    #                     choices=games, nargs="+",
    #                     help=("Games you want to query SHiFT keys for"))
    # parser.add_argument("--platforms",
    #                     type=str, required=True,
    #                     choices=platforms, nargs="+",
    #                     help=("Platforms you want to query SHiFT keys for"))
    parser.add_argument("--limit",
                        type=int, default=200,
                        help=textwrap.dedent("""\
                        Max number of golden Keys you want to redeem.
                        (default 200)
                        NOTE: You can only have 255 keys at any given time!""")) # noqa
    parser.add_argument("--schedule",
                        type=float, const=2, nargs="?",
                        help="Keep checking for keys and redeeming every hour")
    parser.add_argument("-v", dest="verbose",
                        action="store_true",
                        help="Verbose mode")

    return parser


def main(args):
    #print(json.dumps(webpages,indent=2, default=str))
    codes = []
    for webpage in webpages:
        #print(json.dumps(webpage,indent=2, default=str))
        code_tables = scrape_codes(webpage)
        codes = generateAutoshiftJSON(code_tables)
        #print(codes)
    
    with open('shiftcodes.json', 'w', newline='') as fp:
        json.dump(codes, fp, indent=2, ensure_ascii=False)
        #json_string = json.dumps(codes,indent=2, default=str)
        #fp.write(json_string)

if __name__ == '__main__':

    # build argument parser
    parser = setup_argparser()
    args = parser.parse_args()

    #args.pw = getattr(args, "pass")

    # Setup the logger
    _L.setLevel(INFO)
    if args.verbose:
        _L.setLevel(DEBUG)
        _L.debug("Debug mode on")

    # execute the main function
    main(args)