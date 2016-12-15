import requests
import json
import logging
import inspect
from bs4 import BeautifulSoup

r = requests.get("http://leagueoflegends.wikia.com/wiki/List_of_champions")
# "http://champion.gg/champion/Leblanc"

soup = BeautifulSoup(r.content, "html.parser")
#print soup.prettify()
championTable = soup.find("table",attrs={'class':'wikitable sortable'})
# HTML table of champion names and roles
championNames = []
rows = championTable.find_all('tr')
for row in rows:
    cols = row.find_all('td')
    for col in cols:
        col = col.find_all('span',attrs={'class':'character_icon'})  # only find champion names, not their roles
        if col != []:
            col = col[0]  # convert one element list to just a string
            col = col.text
            championNames.append(col)

championNames = [x[1:] for x in championNames]  # remove unicode \xa0
gnarMegaIndex =  championNames.index('Gnar (Mega)')
championNames[gnarMegaIndex] = 'Gnar'
championNames.remove('Gnar (Mini)')
wukongIndex = championNames.index("Wukong")
championNames[wukongIndex] = 'MonkeyKing'
print championNames
print len(championNames)


championNames = [name.replace("'","") for name in championNames]
championNames = [name.replace(" ","") for name in championNames]
championNames = [name.lower() for name in championNames]
championNames = [name.replace(".","") for name in championNames]

champWithAltNames = championNames # championNames2 includes shorter, alternate names
with open('champNames.json', 'w') as fp:
    json.dump(championNames, fp, sort_keys=True, indent=4)