import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone

from common import _L, DEBUG, DIRNAME, INFO
# from typing import (Callable, ContextManager, Dict, Generic, Iterable,
#                     Iterator, Optional, TypeVar)

webpages= [{ 
        "game": "Borderlands: Game of the Year Edition", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-golden-keys/",
        "platform_ordered_tables": [
                "universal",
                "universal"
            ]
    },{ 
        "game": "Borderlands 2", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-2-golden-keys/",
        "platform_ordered_tables": [
                "universal",
                "universal",
                "pc",
                "xbox",
                "Playstation",
                "universal",
                "discard"
            ]
    },{ 
        "game": "Borderlands 3", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-3-golden-keys/",
        "platform_ordered_tables": [
                "universal",
                "discard",
                "universal",
                "universal",
                "universal",
                "discard",
                "discard",
                "discard",
                "discard"
            ]
    },{ 
        "game": "Borderlands The Pre-Sequel", 
        "sourceURL": "https://mentalmars.com/game-news/bltps-golden-keys/",
        "platform_ordered_tables": [
                "universal",
                "universal",
                "pc",
                "Playstation",
                "xbox",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard",
                "discard"
            ]
    },{ 
        "game": "Tiny Tina's Wonderlands", 
        "sourceURL": "https://mentalmars.com/game-news/tiny-tinas-wonderlands-shift-codes/",
        "platform_ordered_tables": [
                "universal",
                "universal"
            ]
    }]

#BL2 = ["universal-expirable", "universal-unexpirable","pc","xbox","Playstation","universal-event"]


def remap_dict_keys(dict_keys):
    # List of table headings to be mapped to standard values
    # Here in case of variation in table headings
    heading_map = {
        'SHiFT Code': 'code',
        'PC SHiFT Code': 'code',
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
    _L.info("Requesting webpage for " + webpage.get("game") + ": " + webpage.get("sourceURL"))
    r = requests.get(webpage.get("sourceURL"))
    #record the time we scraped the URL 
    scrapedDateAndTime = datetime.now(timezone.utc)
    _L.info(" Collected at: " + str(scrapedDateAndTime))
    # print(r.content)

    soup = BeautifulSoup(r.content, 'html.parser') # If this line causes an error, run 'pip install html5lib' or install html5lib
    # print(soup.prettify())

    # Extract all the `figure` tags from the HTML noting the following XPATH was originally expected
    #    /html/body/div[2]/div/div[4]/div[1]/div/div/article/div[5]/figure[2]/table/
    figures = soup.find_all("figure")

    _L.info (" Expecting tables: " + str(len(webpage.get("platform_ordered_tables"))))
    _L.info (" Collected tables: " + str(len(figures)))

    #headers = []
    code_tables = []

    table_count=0
    for figure in figures: 
        _L.info (" Parsing for table #" + str(table_count) + " - " + webpage.get("platform_ordered_tables")[table_count])

        #Don't parse any tables  marked to  discard
        if webpage.get("platform_ordered_tables")[table_count] == "discard":
            table_count+=1
            continue

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


# Restructure the normalised dictionary to the denormalised structure autoshift expects
def generateAutoshiftJSON(website_code_tables): 
    autoshiftcodes = []
    for code_tables in website_code_tables:
        for code_table in code_tables:
            for code in code_table.get("codes"):
                if code_table.get("platform") == "pc":
                    autoshiftcodes.append({
                        "code": code.get("code"),
                        "type": "shift",
                        "game": code_table.get("game"),
                        "platform": "steam",
                        "reward": code.get("reward"),
                        "archived": code_table.get("archived"),
                        "expires": code.get("expires"),
                        "link": code_table.get("sourceURL")
                    })
                    autoshiftcodes.append({
                        "code": code.get("code"),
                        "type": "shift",
                        "game": code_table.get("game"),
                        "platform": "epic",
                        "reward": code.get("reward"),
                        "archived": code_table.get("archived"),
                        "expires": code.get("expires"),
                        "link": code_table.get("sourceURL")
                    })
                else:
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

    # Sort the keys
    # TODO

    # Add the metadata section: 
    generatedDateAndTime = datetime.now(timezone.utc)
    metadata = {
            "version": "0.1",
            "description": "GitHub Alternate Source for Shift Codes",
            "attribution": "Data provided by https://mentalmars.com",
            "permalink": "https://raw.githubusercontent.com/ugoogalizer/autoshift/master/shiftcodes.json",
            "generated": {
                "human": generatedDateAndTime
            }
        }
    
    autoshift = [{
        "meta" : metadata,
        "codes" : autoshiftcodes
    }]
    
    return autoshift   
    #return json.dumps(autoshiftcodes,indent=2, default=str)

def setup_argparser():
    import argparse
    import textwrap

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    # TODO add github repo and key here to publish to...
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
    code_tables = []

    #Scrape the source webpage into a normalised Dictionary
    for webpage in webpages:
        code_tables.append(scrape_codes(webpage))
        
        #print(codes)

    # Convert the normalised Dictionary into the denormalised autoshift structure
    codes = generateAutoshiftJSON(code_tables)

    # Write out the file
    with open('shiftcodes.json', 'w') as write_file:
        json.dump(codes, write_file, indent=2, default=str)

    # Commit and push to github
    # TODO

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