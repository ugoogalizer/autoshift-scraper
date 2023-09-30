

# Overview
Script aimed at scraping SHiFT Codes from websites, initially focused at those hosted on https://mentalmars.com, such as: 
 - https://mentalmars.com/game-news/borderlands-3-golden-keys/

Instead of publishing this as part of [Fabbi's autoshift](https://github.com/Fabbi/autoshift), this is aimed at publishing a machine readable file that can be hit by autoshift.  This reduces the load on mentalmars as it's likely not ok to have swarms of autoshifts scraping their website.

This has been setup with the intent that other webpages could be scraped. The  Python Dictionary `webpages` can be used to customise the webpage, the tables and their contents. This may need adjusting as mentalmars' website updates over time also

TODO List: 
- [x] Scrape mentalmars
- [x] output into a autoshift compatible json file format
- [ ] change to find `table` tags in `figure` tags to reduce noise in webpage
- [x] publish to GitHub [here](https://raw.githubusercontent.com/ugoogalizer/autoshift-codes/main/shiftcodes.json)
- [ ] dockerise and schedule



# Use

``` bash
# If only generating locally
python ./autoshift-scraper.py 

# If pushing to GitHub:
python ./autoshift-scraper.py --user GITHUB_USERNAME --repo GITHUB_REPOSITORY_NAME --token GITHUB_AUTHTOKEN

# If scheduling: 
python ./autoshift-scraper.py --schedule 5 # redeem every 5 hours
```

## Setting up development environment



## Configuring GitHub connectivity

Need to create a new fine-grained personal access token, with access to the only the destination repo and Read & Write access to "Contents"

The token should look something like 

```
github_pat_11p9ou8easrhsgp98sepfg97gUS98hu7ASFuASFDNOANSFDASF ... (but much longer)
```

## Original setup

``` bash
# setup venv
python3 -m venv .venv
source ./.venv/bin/activate

# install packages
pip install requests bs4 html5lib PyGithub APScheduler

pip freeze > requirements.txt
```

