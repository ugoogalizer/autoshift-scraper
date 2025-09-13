import requests
from bs4 import BeautifulSoup
import json, base64
from datetime import datetime, timezone
from os import path, makedirs
from pathlib import Path

from github import Github

from common import _L, DEBUG, DIRNAME, INFO

SHIFTCODESJSONPATH = 'data/shiftcodes.json'

webpages= [{ 
        "game": "Borderlands 4", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-4-shift-codes/",
        "platform_ordered_tables": [
                "universal"
            ]
    },{ 
        "game": "Borderlands: Game of the Year Edition", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-golden-keys/",
        "platform_ordered_tables": [
                "universal",
                "universal",
                "universal"
            ]
    },{ 
        "game": "Borderlands 2", 
        "sourceURL": "https://mentalmars.com/game-news/borderlands-2-golden-keys/",
        "platform_ordered_tables": [
                "universal",
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
                "discard",
                "discard"
            ]
    },{ 
        "game": "Tiny Tina's Wonderlands", 
        "sourceURL": "https://mentalmars.com/game-news/tiny-tinas-wonderlands-shift-codes/",
        "platform_ordered_tables": [
                "universal",
                "universal",
                "universal"
            ]
    }
    
    ]

def remap_dict_keys(dict_keys):
    # Map a variety of possible table heading variations to a small set of
    # canonical keys. This is intentionally fuzzy: many pages prefix the
    # heading with the game name (e.g. 'Borderlands 4 SHiFT Code') or use
    # slightly different wording like 'Expire Date'. Match case-insensitively
    # using substring checks so we don't miss these variants.
    mapped = {}
    for key, value in dict_keys.items():
        if key is None:
            continue
        k = key.strip().lower()
        if 'shift code' in k or 'shift' in k and 'code' in k:
            new_key = 'code'
        elif 'expire' in k:
            new_key = 'expires'
        elif 'reward' in k:
            new_key = 'reward'
        else:
            # preserve the original heading if it doesn't match any known
            # canonical field — downstream code will either handle it or
            # ignore it.
            new_key = key
        mapped[new_key] = value
    return mapped


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

        # Mark expired as expired
        if "expired" in clean_code: 
            clean_code.update({"expired" : True})
        else:
            clean_code.update({"expired" : False})
            

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
        # Prevent IndexError if there are more figures than expected
        if table_count >= len(webpage.get("platform_ordered_tables")):
            _L.warn(f"More tables found ({len(figures)}) than expected ({len(webpage.get('platform_ordered_tables'))}) for {webpage.get('game')}. Skipping extra tables.")
            break

        _L.info (" Parsing for table #" + str(table_count) + " - " + webpage.get("platform_ordered_tables")[table_count])

        #Don't parse any tables marked to discard
        if webpage.get("platform_ordered_tables")[table_count] == "discard":
            table_count+=1
            continue

        table_html = figure.find(lambda tag: tag.name=='table') 

        table_header = []
        code_table = []

        # Convert the HTML table into a Python Dict: 
        # Tip from: https://stackoverflow.com/questions/11901846/beautifulsoup-a-dictionary-from-an-html-table
        table_header = [header.text for header in table_html.find_all('th')]
        table_header.append("expired") # expired codes have a strikethrough ('s') tag and are found last
        code_table = [{table_header[i]: cell.text for i, cell in enumerate(row.find_all({'td','s'}))}
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
            "raw_table_html": str(table_html),
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

# Check to see if the new code existed in previous codes, and if so return the previous code's archive date.
def getPreviousCodeArchived(new_code,new_game,previous_codes):
    # Stupidly inefficient, but enough to keep previous dates
    if previous_codes:
        for previous_code in previous_codes[0].get("codes"):
            #  print("COMPARING: " + new_code.get("code") + " with " + previous_code.get("code"))
            if (new_code.get("code") == previous_code.get("code")) and (new_game == previous_code.get("game")) :
                _L.debug(" Code already existed, reverting archived datestamp")
                return previous_code.get("archived")
    return None

# Restructure the normalised dictionary to the denormalised structure autoshift expects
def generateAutoshiftJSON(website_code_tables, previous_codes, include_expired): 
    autoshiftcodes = []
    newcodecount = 0
    for code_tables in website_code_tables:
        for code_table in code_tables:
            for code in code_table.get("codes"):

                # Skip the code if its expired and we're not to include expired
                if not include_expired and code.get("expired"):
                    continue

                # Extract out the previous archived date if the key existed previously
                archived = getPreviousCodeArchived(code,code_table.get("game"),previous_codes) 
                if archived == None: 
                    # New code
                    archived = code_table.get("archived")
                    newcodecount+=1
                    # If any critical fields are missing, capture context for debugging and continue
                    if code.get("code") is None or code.get("reward") is None:
                        _L.error("Parsed code row missing fields for game=%s platform=%s: %s", code_table.get("game"), code_table.get("platform"), code)
                        # write debugging info to a file for inspection
                        try:
                            debug_record = {
                                "game": code_table.get("game"),
                                "platform": code_table.get("platform"),
                                "sourceURL": code_table.get("sourceURL"),
                                "archived": str(code_table.get("archived")),
                                "row": code
                            }
                            makedirs(path.join(DIRNAME, "data"), exist_ok=True)
                            fn = path.join(DIRNAME, "data", "debug_problem_rows.json")
                            # append JSON objects one per line so it's easy to inspect
                            with open(fn, "a") as df:
                                df.write(json.dumps(debug_record, default=str) + "\n")
                        except Exception as e:
                            _L.error("Failed to write debug file: %s", e)
                    # Use logger formatting (avoids concatenation when values may be None)
                    _L.info(" Found new code: %s %s for %s on %s", code.get("code"), code.get("reward"), code_table.get("game"), code_table.get("platform"))

                if code_table.get("platform") == "pc":
                    autoshiftcodes.append({
                        "code": code.get("code"),
                        "type": "shift",
                        "game": code_table.get("game"),
                        "platform": "steam",
                        "reward": code.get("reward"),
                        "archived": archived,
                        "expires": code.get("expires"),
                        "expired": code.get("expired"),
                        "link": code_table.get("sourceURL")
                    })
                    autoshiftcodes.append({
                        "code": code.get("code"),
                        "type": "shift",
                        "game": code_table.get("game"),
                        "platform": "epic",
                        "reward": code.get("reward"),
                        "archived": archived,
                        "expires": code.get("expires"),
                        "expired": code.get("expired"),
                        "link": code_table.get("sourceURL")
                    })
                else:
                    autoshiftcodes.append({
                        "code": code.get("code"),
                        "type": "shift",
                        "game": code_table.get("game"),
                        "platform": code_table.get("platform"),
                        "reward": code.get("reward"),
                        "archived": archived,
                        "expires": code.get("expires"),
                        "expired": code.get("expired"),
                        "link": code_table.get("sourceURL")
                    })
  
    # Add the metadata section: 
    generatedDateAndTime = datetime.now(timezone.utc)
    metadata = {
            "version": "0.1",
            "description": "GitHub Alternate Source for Shift Codes",
            "attribution": "Data provided by https://mentalmars.com",
            "permalink": "https://raw.githubusercontent.com/zarmstrong/autoshift-codes/main/shiftcodes.json",
            "generated": {
                "human": generatedDateAndTime
            },
            "newcodecount": newcodecount
        }
    
    autoshift = [{
        "meta" : metadata,
        "codes" : autoshiftcodes
    }]
    
    return autoshift   
    #return json.dumps(autoshiftcodes,indent=2, default=str)

def setup_argparser():
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    # TODO add github repo and key here to publish to...
    parser.add_argument("--schedule",
                        type=float, const=2, nargs="?",
                        help="Keep checking for keys and redeeming every hour")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_true",
                        help="Verbose mode")
    parser.add_argument("-u", "--user",
                        default=None,
                        help=("GitHub Username that hosts the repo to push into"))
    parser.add_argument("-r", "--repo",
                        default=None,
                        help=("GitHub Repository to push the shiftcodes into (i.e. autoshift-codes)"))
    parser.add_argument("-t", "--token",
                        default=None,
                        help=("GitHub Authentication token to use "))
    return parser


def main(args):

    # Setup json output folder
    makedirs(path.join(DIRNAME, "data"), exist_ok=True)
    Path('data/shiftcodes.json').touch()

    #print(json.dumps(webpages,indent=2, default=str))
    codes_inc_expired = []
    codes_excl_expired = []
    code_tables = []

    #Scrape the source webpage into a normalised Dictionary
    for webpage in webpages:
       code_tables.append(scrape_codes(webpage))
        
        #print(codes)

    _L.info("Scraping Complete. Now writing out shiftcodes.json file")

    # Read in the previous codes so we can retain timestamps and know how many are new
    with open(SHIFTCODESJSONPATH, "rb") as f:
        try:
            previous_codes = json.loads(f.read())
        except:
            previous_codes = None
            pass

    # Convert the normalised Dictionary into the denormalised autoshift structure
    codes_inc_expired = generateAutoshiftJSON(code_tables, previous_codes, True)
    codes_excl_expired = generateAutoshiftJSON(code_tables, previous_codes, False)

    _L.info("Found " + str(codes_inc_expired[0].get("meta").get("newcodecount")) + " new codes.")

    # Write out the file even if no new codes so we can track last scrape time
    with open(SHIFTCODESJSONPATH, 'w') as write_file:
        json.dump(codes_inc_expired, write_file, indent=2, default=str)

    # Commit the new file to GitHub publically if the args are set:
    if (args.user and args.repo and args.token):
        #Only commit if there are new codes
        if codes_inc_expired[0].get("meta").get("newcodecount") > 0:
            _L.info("Connecting to GitHub repo: " + args.user + "/" + args.repo)
            # Connect to GitHub
            file_path = SHIFTCODESJSONPATH
            g = Github(args.token)
            repo = g.get_repo(args.user + "/" + args.repo)

            # Read in the latest file
            _L.info("Read in shiftcodes file")
            with open(file_path, "rb") as f:
                file_to_commit = f.read()

            # Push to GitHub:
            _L.info("Push and Commit")
            contents = repo.get_contents('shiftcodes.json', ref="main")  # Retrieve old file to get its SHA and path
            commit_return = repo.update_file(contents.path, "added new codes" , file_to_commit, contents.sha, branch="main", )  # Add, commit and push branch
            _L.info("GitHub result: " + str(commit_return))
        else:
            _L.info("Not committing to GitHub as there are no new codes.")

if __name__ == '__main__':
    import os

    # build argument parser
    parser = setup_argparser()
    args = parser.parse_args()

    # Setup the logger
    _L.setLevel(INFO)
    if args.verbose:
        _L.setLevel(DEBUG)
        _L.debug("Debug mode on")

    # execute the main function at least once (and only once if scheduler is not set)
    main(args)

    if args.schedule and args.schedule < 2:
        _L.warn(f"Running this tool every {args.schedule} hours would result in "
                "too many requests.\n"
                "Scheduling changed to run every 2 hours!")

    # scheduling will start after first trigger (so in an hour..)
    if args.schedule:
        hours = int(args.schedule)
        minutes = int((args.schedule-hours)*60+1e-5)
        _L.info(f"Scheduling to run every {hours:02}:{minutes:02} hours")
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        scheduler.add_job(main, "interval", args=(args,), hours=args.schedule)
        print(f"Press Ctrl+{'Break' if os.name == 'nt' else 'C'} to exit")

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass

    _L.info("Goodbye.")