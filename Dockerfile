FROM python:3.10-slim

COPY . /autoshift-scraper/
WORKDIR /autoshift-scraper
RUN pip install -r ./requirements.txt && \
    touch ./shiftcodes.json
CMD python ./autoshift-scraper.py --user ${GITHUB_USER} --repo ${GITHUB_REPO} --token ${GITHUB_TOKEN} ${PARSER_ARGS}