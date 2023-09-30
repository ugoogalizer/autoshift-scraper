FROM python:3.10-slim

COPY . /autoshift-scraper/
RUN pip install -r ./autoshift-scraper/requirements.txt && \
    touch ./autoshift-scraper/shiftcodes.json
CMD python ./autoshift/auto.py --user ${SHIFT_USER} --pass ${SHIFT_PASS} --games ${SHIFT_GAMES} --platforms ${SHIFT_PLATFORMS} ${SHIFT_ARGS}