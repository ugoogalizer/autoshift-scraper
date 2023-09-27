

import requests
from bs4 import BeautifulSoup
import csv

URL = "https://mentalmars.com/game-news/borderlands-2-golden-keys/"
r = requests.get(URL)
# print(r.content)


soup = BeautifulSoup(r.content, 'html.parser') # If this line causes an error, run 'pip install html5lib' or install html5lib
# print(soup.prettify())

figures = soup.find_all("figure")

#print(figures[0].prettify())
i=1
for figure in figures: 
    print("Figure " + str(i))
    table = figure.find(lambda tag: tag.name=='table') 

#     headers = table.findAll(lambda tag: tag.name=='th')
#     rows = table.findAll(lambda tag: tag.name=='tr')
#     headers2=[]
#     for header in headers: 
#         headers2.append(header.get_text())

    
#     print(headers2)
#     print(rows)

    headers = []
    results = []

    # headers_clean = [header.get_text() for header in table.findAll(["tr"])]
    # headers = [header for header in table.findAll(["tr","th"])]
    # results = [{headers_clean[i]: cell.get_text() for i, cell in enumerate(row.findAll("td"))} for row in table.findAll(["tr"])]
    
    headers = [header.text for header in table.find_all('th')]
    results = [{headers[i]: cell.text for i, cell in enumerate(row.find_all('td'))}
            for row in table.find('tbody').find_all('tr')]

    # print("HEADER CLEAN: " + str(i))
    # print(headers_clean)
    print("HEADER: " + str(i))
    print(headers)
    print("RESULT: " + str(i))
    print(results)
    i+=1