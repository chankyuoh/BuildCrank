import requests
import json
import logging
import unicodedata
import inspect
from bs4 import BeautifulSoup

#TODO: add builds sorted by roles
#TODO: Fix Aatrox Jungle build bug
#TODO: Things learned: Logging, WebScraping, Scaling, automation, making things work for long-run
#TODO: Making code easier to read by SLAP
#TODO: Fix Jungle weapon enchantment
#TODO: Add starter and full build options
#TODO: Add Frequent or Highest win option


logging.basicConfig(level=logging.INFO, format= '%(levelname)s %(lineno)d \n%(message)s')
logger = logging.getLogger(__name__)
# ignore requests library's logging information
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def parseUrlTag(tag):
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


def parseLeaguePediaURL(url):
    """Given a URL link of the leaguepedia wiki's item description, parses out the item name"""
    begin = url.find("/wiki/")
    begin = begin + len("/wiki/")
    return url[begin:]

def parseJungleItem(jungleItem):
    """Parses out the the item ID number by looking for the string 'data-id='"""
    if "data-id" in jungleItem:
        beginInd = jungleItem.index("data-id")
        ID = jungleItem[beginInd+9:beginInd+13]
        if ID == "1400":
            return "Stalker's Warrior"
        elif ID == "1401":
            return "Stalker's Cinderhulk"
        elif ID == "1402":
            return "Stalker's Runic Echoes"
        elif ID == "1408":
            return "Tracker's Warrior"
        elif ID == "1409":
            return "Tracker's Cinderhulk"
        elif ID == "1410":
            return "Tracker's Runic Echoes"
        elif ID == "1412":
            return "Skirmisher's Warrior"
        elif ID == "1413":
            return "Skirmisher's Cinderhulk"
        elif ID == "1414":
            return "Skirmisher's Runic Echoes"
        elif ID == "1416":
            return "Skirmisher's Bloodrazor"
        elif ID == "1418":
            return "Tracker's Bloodrazor"
        elif ID == "1419":
            return "Skirmisher's Bloodrazor"
        else:
            return ""
    else:
        return ""

def parseFullBuild(build):
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
        #print item
        jungleItem = item.find_all("img", attrs={'class': 'possible-build tsm-tooltip'})
        if jungleItem == []:
            jungleItem = item.find_all("img", attrs={'class': 'tsm-tooltip possible-build'})
        #print jungleItem
        jungleItem = str(jungleItem)
        jungleItem = parseJungleItem(jungleItem)
        if jungleItem != "":
            itemList.append(jungleItem)
        else:
            item = str(item)
            itemList.append(parseLeaguePediaURL(parseUrlTag(item)))
        i += 3
        # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
    if len(itemList) >= 1:
        itemList = itemList[0:len(itemList) - 1]  # remove last item which is a blank item from parsing
    #print itemList
    return itemList


def parseStarterBuild(build):
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
        itemList.append(parseLeaguePediaURL(parseUrlTag(item)))
        i += 2
        # the items list contains a pattern of [URL,PictureLink,random HTML tag], we only want URL, so skip by 3's
    if len(itemList) >= 2:
        itemList = itemList[0:len(itemList) - 2]
    return itemList


def makeRoleBuildDict(url,role):
    """ url: champion.gg url link to the champion's page
        role: the specified role of the champ's build you want
        Parses champion's specific role page and returns a dictionary of d[BuildType] = build details"""
    # 0 = Most Frequent Build
    # 1 = Highest Winrate Build
    # 2 = Most Frequent Starter
    # 3 = Highest Winrate Starter
    r = requests.get(url+"/"+role)
    soup = BeautifulSoup(r.content, "html.parser")
    roleBuildDict = {}
    buildTypes = soup.find_all("div", class_="build-wrapper")
    # buildTypes becomes a list of the HTML parts that encloses the build order
    for i in range(len(buildTypes)):
        if i == 0:
            roleBuildDict["FreqFullBuild"] = parseFullBuild(buildTypes[0])
            logger.debug(str("FreqFullBuild: " + str(parseFullBuild(buildTypes[0]))))
        elif i == 1:
            roleBuildDict["WinFullBuild"] = parseFullBuild(buildTypes[i])
            logger.debug(str("WinFullBuild: " + str(parseFullBuild(buildTypes[i]))))
        if i == 2:
            roleBuildDict["FreqStarterBuild"] = parseStarterBuild(buildTypes[i])
            logger.debug(str("FreqStarterBuild: " + str(parseStarterBuild(buildTypes[i]))))
        elif i == 3:
            roleBuildDict["WinStarterBuild"] = parseStarterBuild(buildTypes[i])
            logger.debug(str("WinStarterBuild: " + str(parseStarterBuild(buildTypes[i]))))
    return roleBuildDict


def createChampRoleList(soup):
    """
    soup: beautifulsoup object, used to parse HTML web page. soup object should be
    the champion.gg page of the champion you are interested in.

    Finds the roles that the specified champion plays (mid, top, jg, etc.)
    and returns a list of the roles"""
    roleList = []
    webLinks = soup.find_all("a")  # pull html code that has web link in it b/c roles are listed as links to the role page
    for link in webLinks:
        roleName = link.find_all("h3")  # the roles (Middle,Top, etc.) are written in h3 html tag
        if roleName != []:
            roleName = roleName[0]  # convert roleName from single element list to string
            roleName = roleName.text.strip()
            roleList.append(roleName)
    return roleList

def makeChampData(name):
    """
    name: string format name of the champion
    Creates the champion's build data in a dictionary of format d[role][buildType]"""
    url = "http://champion.gg/champion/" + name
    r = requests.get(url)
    # "http://champion.gg/champion/Leblanc"
    soup = BeautifulSoup(r.content, "html.parser")
    roleList = createChampRoleList(soup)
    roleData = {}  # roleData format: roleData[Role][BuildType]
    for role in roleList:
        roleData[role] = makeRoleBuildDict(url,role)
    #print soup.prettify()
    return roleData

def makeJsonData(champBuildDict):
    """Writes a JSON file that has all the information of a champion's builds
       in a file named 'champData.json' """
    #  write new champion build data to .json file
    with open('champData.json', 'w') as fp:
        json.dump(champBuildDict, fp, sort_keys=True, indent=4)


def createChampBuildsJsonFile():
    """
    creates a dictionary of champion builds ( d[ChampionName][Role][BuildType]
    and saves the dictionary to a json file called 'champData.json' """
    with open("champNames.json", 'r') as fp:
        champNames = json.load(fp)
    champBuildDict = {}
    for champName in champNames:
        champBuild = makeChampData(champName)
        champBuildDict[champName] = champBuild
        makeJsonData(champBuildDict)





def printEveryBuildFromJson():
    """parses the Json to print out the build order for all champion and roles"""
    with open("champData.json", 'r') as fp:
        data = json.load(fp)
        for champ in data:
            for role in data[champ]:
                res = "Build Suggestion: for " + champ + " " + role +  "\n"
                itemCount = 1
                freqFull = data[champ][role]["FreqFullBuild"]
                for i in range(len(freqFull)):
                    res += str(itemCount) + ") "
                    res += freqFull[i] + "\n"
                    itemCount += 1
                print res

def printSpecificBuildFromJson(champName):
    """parses the Json to print out the build order for the specified champion's roles"""
    with open("champData.json", 'r') as fp:
        data = json.load(fp)
        for role in data[champName]:
            res = "Build Suggestion: for " + champName + " " + role + "\n"
            itemCount = 1

            freqFull = data[champName][role]["FreqFullBuild"]
            for i in range(len(freqFull)):
                res += str(itemCount) + ") "
                res += freqFull[i] + "\n"
                itemCount += 1
            print res



createChampBuildsJsonFile()
#printEveryBuildFromJson()
#makeChampData("Fiora")

#printSpecificBuildFromJson("akali")

#r = requests.get("http://champion.gg/champion/hecarim")
#soup = BeautifulSoup(r.content, "html.parser")
#print soup.prettify()

#makeChampData("hecarim")




