FROM python:3.10-slim

COPY . /autoshift-scraper/
RUN pip install -r ./autoshift-scraper/requirements.txt && \
    touch ./autoshift-scraper/shiftcodes.json
CMD python ./autoshift-scraper/autoshift-scraper.py --user ${GITHUB_USER} --repo ${GITHUB_REPO} --token ${GITHUB_TOKEN} ${PARSER_ARGS}