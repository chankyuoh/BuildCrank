import requests
from bs4 import BeautifulSoup


# github commit check
def parseUrlTag(tag):
    """Given an HTML tag, parses out and returns only the URL portion"""
    isWithinQuote = False
    count = 0
    url = ""
    for char in tag:
        if count == 2:
            break
        if char == '"':
            isWithinQuote = not isWithinQuote
            count += 1
        elif isWithinQuote:
            url += char
    return url

def parseUrl(url):
    """Given a URL link of the leaguepedia wiki's item description, parses out the item name"""
    begin =  url.find("/wiki/")
    begin = begin + len("/wiki/")
    return url[begin:]


def parseFullBuild(build):
    items = build.findChildren()  # items per build can be parsed with findChildren()
    # the items list contains a pattern of [URL,PictureLink,random HTML tag]
    itemList = []
    i = 0
    while i < len(items):
        item = items[i]
        item = str(item)
        # print "item's leaguepedia link tag"
        # print item
        # print "PARSED URL TAG"
        # print parseUrlTag(itemInfo)
        #print "PARSE URL"
        #print parseUrl(parseUrlTag(item))
        itemList.append(parseUrl(parseUrlTag(item)))
        i += 3
        # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
    return itemList



r = requests.get("http://champion.gg/champion/Akali")

soup = BeautifulSoup(r.content)

#print soup.prettify()

print "BUILDS GOES DOWN HERE"
# 0 = Most Frequent Build
# 1 = Highest Winrate Build
# 2 = Most Frequent Starter
# 3 = Highest Winrate Starter
buildTypes = soup.find_all("div", class_="build-wrapper")
freqBuild = ""
fullBuilds = buildTypes[0:2]
starterBuilds = buildTypes[2:]
for build in fullBuilds:
    print parseFullBuild(build)
#print buildList[0]





