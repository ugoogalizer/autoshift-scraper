

# Overview
Script aimed at scraping SHiFT Codes from websites, initially focused at those hosted on https://mentalmars.com, such as: 
 - https://mentalmars.com/game-news/borderlands-3-golden-keys/

Instead of publishing this as part of [Fabbi's autoshift](https://github.com/Fabbi/autoshift), this is aimed at publishing a machine readable file that can be hit by autoshift.  This reduces the load on mentalmars as it's likely not ok to have swarms of autoshifts scraping their website.

This has been setup with the intent that other webpages could be scraped. The  Python Dictionary `webpages` can be used to customise the webpage, the tables and their contents. This may need adjusting as mentalmars' website updates over time also

TODO List: 
- [x] Scrape mentalmars
- [x] output into a autoshift compatible json file format
- [ ] change to find `table` tags in `figure` tags to reduce noise in webpage
- [ ] publish somewhere for consumption (github repo?) retaining sort order to make diffs easier
- [ ] dockerise and schedule



# Use

``` bash
python3 ./autoshift-scraper.py
```

## Setting up development environment




## Original setup

``` bash
# setup venv
python3 -m venv .venv
source ./.venv/bin/activate

# install packages
pip install requests bs4 html5lib

pip freeze > requirements.txt
```

