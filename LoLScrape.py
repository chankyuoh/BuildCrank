import requests
import json
from bs4 import BeautifulSoup

#TODO: add builds sorted by roles

# github commit check

championDict = {}

class championScrape(object):
    def __init__(self):
        self.url = ""
    def parseUrlTag(self,tag):
        """Given an HTML tag of href link and other stuff, parses out and returns only the URL portion"""
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

    def parseUrl(self,url):
        """Given a URL link of the leaguepedia wiki's item description, parses out the item name"""
        begin = url.find("/wiki/")
        begin = begin + len("/wiki/")
        return url[begin:]

    def parseFullBuild(self,build):
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
            # print "PARSE URL"
            # print parseUrl(parseUrlTag(item))
            itemList.append(self.parseUrl(self.parseUrlTag(item)))
            i += 3
            # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
        if len(itemList) >= 1:
            itemList = itemList[0:len(itemList) - 1]  # remove last item which is a blank item from parsing
        return itemList

    def parseStarterBuild(self,build):
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
            # print "PARSE URL"
            # print parseUrl(parseUrlTag(item))
            itemList.append(self.parseUrl(self.parseUrlTag(item)))
            i += 2
            # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
        if len(itemList) >= 2:
            itemList = itemList[0:len(itemList) - 2]
        return itemList

    def getBuilds(self,url):
        r = requests.get(url)
        # "http://champion.gg/champion/Leblanc"

        soup = BeautifulSoup(r.content)
        buildList = {}
        # print soup.prettify()

        # 0 = Most Frequent Build
        # 1 = Highest Winrate Build
        # 2 = Most Frequent Starter
        # 3 = Highest Winrate Starter
        buildTypes = soup.find_all("div", class_="build-wrapper")
        freqBuild = ""
        fullBuilds = buildTypes[0:2]
        print "FULL BUILDS"
        starterBuilds = buildTypes[2:]
        for i in range(len(fullBuilds)):
            print self.parseFullBuild(fullBuilds[i])
            if i == 0:
                buildList["FreqFullBuild"] = self.parseFullBuild(fullBuilds[i])
            elif i == 1:
                buildList["WinFullBuild"] = self.parseFullBuild(fullBuilds[i])
        print "STARTER BUILDS"
        for i in range(len(starterBuilds)):
            print self.parseStarterBuild(starterBuilds[i])
            if i == 0:
                buildList["FreqStarterBuild"] = self.parseStarterBuild(starterBuilds[i])
            elif i == 1:
                buildList["WinStarterBuild"] = self.parseStarterBuild(starterBuilds[i])
        return buildList

c = championScrape()
champBuilds = c.getBuilds("http://champion.gg/champion/Akali")
print champBuilds
championDict['Akali'] = champBuilds


with open('champData.json', 'w') as fp:
    json.dump(championDict, fp, sort_keys=True, indent=4)

with open('champData.json', 'r') as fp:
    data = json.load(fp)
    print "JSON DATA"
    print str(data)





