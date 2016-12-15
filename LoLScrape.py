import requests
import json
import logging
import unicodedata
import inspect
from bs4 import BeautifulSoup

#TODO: add builds sorted by roles


logging.basicConfig(level=logging.INFO, format= '%(levelname)s %(lineno)d \n%(message)s')
logger = logging.getLogger(__name__)
# ignore requests library's logging information
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)



class championScrape(object):
    def __init__(self):
        self.url = ""
    def parseUrlTag(self,tag):
        """Given an HTML tag of href link and other HTML stuff, parses out and returns only the URL portion"""
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

    def parseLeaguePediaURL(self, url):
        """Given a URL link of the leaguepedia wiki's item description, parses out the item name"""
        begin = url.find("/wiki/")
        begin = begin + len("/wiki/")
        return url[begin:]

    def parseFullBuild(self,build):
        """
        build: HTML div portion that contains the build order
        Parses the HTML to obtain just the items from the HTML code
        returns a list of the items in order
        Note: This method is used to parse the full build div"""
        items = build.findChildren()  # items per build can be parsed with findChildren()
        # the items list contains a pattern of [URL,PictureLink,random HTML tag]
        itemList = []
        i = 0
        while i < len(items):
            item = items[i]
            item = str(item)
            itemList.append(self.parseLeaguePediaURL(self.parseUrlTag(item)))
            i += 3
            # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
        if len(itemList) >= 1:
            itemList = itemList[0:len(itemList) - 1]  # remove last item which is a blank item from parsing
        return itemList

    def parseStarterBuild(self,build):
        """
        build: HTML div portion that contains the build order
        Parses the HTML to obtain just the items from the HTML code
        returns a list of the items in order
        Note: this method is used to parse the starter item div"""
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
            itemList.append(self.parseLeaguePediaURL(self.parseUrlTag(item)))
            i += 2
            # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
        if len(itemList) >= 2:
            itemList = itemList[0:len(itemList) - 2]
        return itemList

    def getBuilds(self,url):
        """
        url: URL link to the champion's profile page
        uses BS4 to web scrape item build order data from the page"""
        r = requests.get(url)
        # "http://champion.gg/champion/Leblanc"

        soup = BeautifulSoup(r.content, "html.parser")
        buildList = {}
        # print soup.prettify()

        # 0 = Most Frequent Build
        # 1 = Highest Winrate Build
        # 2 = Most Frequent Starter
        # 3 = Highest Winrate Starter
        buildTypes = soup.find_all("div", class_="build-wrapper")
        # buildTypes becomes a list of the HTML parts that encloses the build order
        fullBuilds = buildTypes[0:2]  # full builds (freq, highest win) are the first 2 items
        starterBuilds = buildTypes[2:]  # starter builds (freq, highest win) are last 2 items
        for i in range(len(fullBuilds)):
            if i == 0:
                buildList["FreqFullBuild"] = self.parseFullBuild(fullBuilds[i])
                logger.debug(str("FreqFullBuild: " + str(self.parseFullBuild(fullBuilds[i]))))
            elif i == 1:
                buildList["WinFullBuild"] = self.parseFullBuild(fullBuilds[i])
                logger.debug(str("WinFullBuild: " + str(self.parseFullBuild(fullBuilds[i]))))
        for i in range(len(starterBuilds)):
            if i == 0:
                buildList["FreqStarterBuild"] = self.parseStarterBuild(starterBuilds[i])
                logger.debug(str("FreqStarterBuild: " + str(self.parseFullBuild(fullBuilds[i]))))
            elif i == 1:
                buildList["WinStarterBuild"] = self.parseStarterBuild(starterBuilds[i])
                logger.debug(str("WinStarterBuild: " + str(self.parseFullBuild(fullBuilds[i]))))
        return buildList



def makeChampBuildJson():
    # Open json file that has the list of champion names
    with open("champNames.json", 'r') as fp:
        champNames = json.load(fp)
    champBuildDict = {}
    c = championScrape()
    for champName in champNames:
        champBuilds = c.getBuilds("http://champion.gg/champion/"+champName)
        champBuildDict[champName] = champBuilds
        makeJsonData(champBuildDict)



def makeJsonData(champBuildDict):
    """Writes a JSON file that has all the information of a champion's builds
       in a file named 'champData.json' """
    #  write new champion build data to .json file
    with open('champData.json', 'w') as fp:
        json.dump(champBuildDict, fp, sort_keys=True, indent=4)

def printBuildFromJson(fileName,champName):
    """parses the Json to print out the build order for the champion specified"""
    with open(fileName, 'r') as fp:
        data = json.load(fp)

        res = ""
        res += "Build Suggestion: \n"
        freqFull = data[champName]["FreqFullBuild"]
        itemCount = 1
        for i in range(len(freqFull)):
            res += str(itemCount) + ") "
            res += freqFull[i] + "\n"
            itemCount += 1
        print res
makeChampBuildJson()
with open("champNames.json", 'r') as fp:
    champNames = json.load(fp)

for champ in champNames:
    print champ
    printBuildFromJson('champData.json',champ)









#  read .json file for champion build data






