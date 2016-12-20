import os
import sys
import json
import string
import requests
from flask import Flask, request
app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    set_get_started_button()
    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    if "text" not in messaging_event["message"]:  # don't let users send me stickers/images
                        send_message(sender_id,"I only accept text-based communications :(")
                        return "ok", 200
                    else:
                        message_text = messaging_event["message"]["text"]  # the message's text

                    sendAppropriateMessage(message_text,sender_id)


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    message_text = messaging_event["postback"]["payload"]  # the message's text
                    sender_id = messaging_event["sender"]["id"]
                    aboutMessage = "BuildCrank is built using Flask, Heroku, and Python. \n\n"
                    aboutMessage += "All data has been web scraped from champion.gg using the BS4 python module\n\n"
                    aboutMessage += "Find the code for this bot on my Github! https://github.com/chankyuoh/fb-lol-bot"
                    feedbackMsg = "Send me any feedback or bug reports by PM'ing /u/RevTremendo on reddit! "
                    text = "Try any of these things: \n\n"
                    text += "1: varus\n"
                    text += "2: varus mid\n"
                    text += "3: mid varus\n"
                    text += "4: frequent varus\n"
                    text += "5: frequent varus mid\n"
                    text += "6: highest winrate varus mid\n"
                    text += "7: winrate varus mid\n"
                    text += "8: most frequent build for varus mid\n"
                    text += "9: highest winrate build for varus adc\n"
                    if message_text == "example_clicked":
                        send_message(sender_id,text)
                    elif message_text == "about_clicked":
                        send_message(sender_id,aboutMessage)
                    elif message_text == "feedback_clicked":
                        send_message(sender_id,feedbackMsg)
                    elif message_text == "get_started_clicked":
                        send_help_post_message(sender_id)
                    else:
                        sendAppropriateMessage(message_text,sender_id)

    return "ok", 200



def sendAppropriateMessage(message_text,sender_id):
    message_text = formatMessage(message_text)
    if message_text.lower().strip() == "help":
        send_help_post_message(sender_id)
        return "ok", 200

    if isChampionNameSpecified(message_text) and isRoleSpecified(message_text) and isBuildTypeSpecified(message_text):
        championName = getChampionName(message_text)
        role = getRole(championName,message_text)
        buildType = getBuildType(message_text)
        if isValidRole(championName,role):
            sendPrettyBuild(championName,role,buildType,sender_id)
            return "ok", 200
        else:
            send_message(sender_id,
                         "Sorry " + championName + "'s " + prettifyRole(role) + " build is not available. Try a more common role for this champion")
            return "ok", 200
        buildType = getBuildType(message_text)
        sendPrettyBuild(championName,role,buildType,sender_id)
    elif isChampionNameSpecified(message_text) and isRoleSpecified(message_text) and not isBuildTypeSpecified(message_text):
        championName = getChampionName(message_text)
        role = getRole(championName, message_text)
        if isValidRole(championName,role):
            send_build_type_post_message(sender_id, championName, role)
            return "ok", 200
        else:
            send_message(sender_id,
                         "Sorry " + prettifyChampionName(championName) + "'s " + prettifyRole(role) + " build is not available. Try a more common role for this champion")
            return "ok", 200
    elif isChampionNameSpecified(message_text) and not isRoleSpecified(message_text) and isBuildTypeSpecified(message_text):
        championName = getChampionName(message_text)
        buildType = getBuildType(message_text)
        roles = getRoleList(championName)
        send_role_post_message(sender_id,roles,championName,buildType)
    elif isChampionNameSpecified(message_text) and not isRoleSpecified(message_text) and not isBuildTypeSpecified(message_text):
        championName = getChampionName(message_text)
        buildType = ""
        roles = getRoleList(championName)
        send_role_post_message(sender_id,roles,championName,buildType)
    else:
        send_message(sender_id, "Sorry I don't recognize a champion name in your message. Type help if you're stuck!")
        return "ok", 200


def formatMessage(message_text):
    message_text = removeApostropheS(message_text)
    message_text = "".join(c for c in message_text if c not in ('!', '.', ':', '?', ",", "'"))
    return message_text


def removeApostropheS(message_text):
    for i in range(len(message_text)-1):
        twoMsg = message_text[i] + message_text[i+1]
        if twoMsg == "'s":
            newMsg = message_text[0:i] + message_text[i+2:]
            return newMsg
    return message_text



def getRoleList(champName):
    with open('champData.json', 'r') as fp:
        data = json.load(fp)
    roleList = data[champName].keys()
    return roleList

def isChampionNameSpecified(message_text):
    with open('champNames.json', 'r') as fp:
        champNames = json.load(fp)
    championName = formatChampionName(message_text)
    if championName in champNames:
        return True
    else:
        return False
def getChampionName(message_text):
    with open('champNames.json', 'r') as fp:
        champNames = json.load(fp)
    championName = formatChampionName(message_text)
    if championName in champNames:
        return championName
def isValidRole(championName,role):
    roleList = getRoleList(championName)
    if role in roleList:
        return True
    else:
        return False

def formatChampionName(message_text):
    msgList = message_text.split(" ")
    if len(msgList) == 1:
        championName = updateChampNameFormat(message_text)
    else:
        championName = getSpecifiedChampName(message_text)  # message contain both champ name and role, parse out name
        championName = updateChampNameFormat(championName)
    return championName

def isBuildTypeSpecified(message_text):
    buildTypes = ['most','freq','frequent', 'frequently','common','commonly', 'win%', '%','high' 'highest','win', 'winning', 'winrate', 'rate']
    msgList = message_text.split(" ")
    for msg in msgList:
        msg = msg.lower().strip()
        if msg in buildTypes:
            return True

    return False

def getBuildType(message_text):
    frequentBuildTypeKeyWords = ['most','freq','frequent','frequently','common','commonly']
    winBuildTypeKeyWords = ['high','highest','win','rate','winning','winrate', 'win%', '%']
    msgList = message_text.split(" ")
    for msg in msgList:
        msg = msg.lower().strip()
        if msg in frequentBuildTypeKeyWords:
            return "frequent"
        if msg in winBuildTypeKeyWords:
            return "win"
    return "frequent"  # default to frequent if can't find
def isRoleSpecified(message_text):
    roles = ['sup', 'supp', 'support', "ad","bot", 'adc', 'mid', "middle", 'jg', 'jungle', 'top']
    msgList = message_text.split(" ")
    for msg in msgList:
        msg = msg.lower()
        if msg in roles:
            return True
    return False

def getRole(championName,message_text):
    roles = ['sup','supp', 'support', "bot", 'adc', 'mid', "middle", 'jg', 'jungle', 'top']
    msgList = message_text.split(" ")
    for msg in msgList:
        msg = msg.lower()
        if msg in roles:
            if msg == "sup" or msg == "supp" or msg == "support":
                return "Support"
            if msg == "bot" or msg == "adc":
                return "ADC"
            if msg == "mid" or msg == "middle":
                return "Middle"
            if msg == "jg" or msg == "jungle":
                return "Jungle"
            if msg == "top":
                return "Top"
    roleList = getRoleList(championName)
    return roleList[0]  # this leads to random role selection


def prettifyRole(role):
    if role == "ADC":
        return "Adc"
    elif role == "Middle":
        return "Mid"
    else:
        return role

def sendPrettyBuild(championName,role,buildType,sender_id):
    with open('champData.json', 'r') as fp:
        data = json.load(fp)

    if buildType == "frequent":
        res = makeFrequentBuild(championName,role,data)
        send_message(sender_id,res)
        return "ok", 200
    elif buildType == "win":
        res = makeWinBuild(championName,role,data)
        send_message(sender_id,res)
        return "ok", 200
    else:
        send_message(sender_id,"I HAVE NO IDEA WHAT IM DOING")

def prettifyChampionName(championName):
    if championName == "aurelionsol":
        return "Aurelion Sol"
    if championName == "chogath":
        return "Cho'Gath"
    if championName == "drmundo":
        return "Dr. Mundo"
    if championName == "jarvaniv":
        return "Jarvan IV"
    if championName == "khazix":
        return "Kha'Zix"
    if championName == "kogmaw":
        return "Kog'Maw"
    if championName == "leblanc":
        return "LeBlanc"
    if championName == "leesin":
        return "Lee Sin"
    if championName == "masteryi":
        return "Master Yi"
    if championName == "missfortune":
        return "Miss Fortune"
    if championName == "reksai":
        return "Rek'Sai"
    if championName == "tahmkench":
        return "Tahm Kench"
    if championName == "twistedfate":
        return "Twisted Fate"
    if championName == "velkoz":
        return "Vel'Koz"
    if championName == "xinzhao":
        return "Xin Zhao"
    return championName[0].upper() + championName[1:]


def makeWinBuild(championName,role,data):
    prettyChampName = championName[0].upper() + championName[1:]
    prettyRoleName = prettifyRole(role)
    res = ""
    res += "Highest Win Rate Build For " + prettyChampName + " " + prettyRoleName + "\n"
    WinFullBuild = data[championName][role]["WinFullBuild"]
    itemCount = 1
    for i in range(len(WinFullBuild)):
        res += str(itemCount) + ") "
        res += WinFullBuild[i] + "\n"
        itemCount += 1
    res += "\n Starting Items: "+ "\n"
    WinStartBuild = data[championName][role]["WinStarterBuild"]
    itemCount = 1
    for i in range(len(WinStartBuild)):
        res += str(itemCount) + ") "
        res += WinStartBuild[i] + "\n"
        itemCount += 1
    return res

def makeFrequentBuild(championName,role,data):
    prettyChampName = prettifyChampionName(championName)
    prettyRoleName = prettifyRole(role)
    res = ""
    res += "Most Frequent Build For: " + prettyChampName + " " + prettyRoleName + "\n"
    freqFullBuild = data[championName][role]["FreqFullBuild"]
    itemCount = 1
    for i in range(len(freqFullBuild)):
        res += str(itemCount) + ") "
        res += freqFullBuild[i] + "\n"
        itemCount += 1
    res += "\n Starting Items: "+ "\n"
    freqStartBuild = data[championName][role]["FreqStarterBuild"]
    itemCount = 1
    for i in range(len(freqStartBuild)):
        res += str(itemCount) + ") "
        res += freqStartBuild[i] + "\n"
        itemCount += 1
    return res

def getSpecifiedChampName(message_text):
    """gets the specified champion's name by removing the role portion of the message"""
    msgList = message_text.split(" ")
    with open('champNames.json', 'r') as fp:
        champNames = json.load(fp)

    for msg in msgList:
        msg = msg.lower()
        msg = convertAltNametoOriginal(msg)
        if msg in champNames:
            return msg
    for i in range(len(msgList)-1):
        twoWordMsg = msgList[i] + msgList[i+1]
        twoWordMsg = twoWordMsg.lower().strip()
        if twoWordMsg in champNames:
            return twoWordMsg
    return message_text







def updateChampNameFormat(message_text):
    """ Updates the message text to fit the format used in the champData.json file"""
    message_text = message_text.replace(".", "")
    message_text = message_text.replace("'", "")
    message_text = message_text.replace(" ", "")
    message_text = message_text.lower()
    message_text = convertAltNametoOriginal(message_text)
    return message_text


def convertAltNametoOriginal(name):
    if name in ["asol","aurelion","aurlieon","sol"]:
        return "aurelionsol"
    if name in ["blitz"]:
        return "blitzcrank"
    if name in ["cass","cassi","cassiopiea"]:
        return "cassiopeia"
    if name == "cho":
        return "chogath"
    if name == "mundo":
        return "drmundo"
    if name in ["eve","evelyn"]:
        return "evelynn"
    if name == "ez":
        return "ezreal"
    if name in ["fiddle","fiddlestick","fid"]:
        return "fiddlesticks"
    if name == "gp":
        return "gangplank"
    if name == "heimer":
        return "heimerdinger"
    if name == "ilaoi":
        return "illaoi"
    if name in ["j4","jarvan","jarvan4"]:
        return "jarvaniv"
    if name in ["kasadin","kass"]:
        return "kassadin"
    if name == "kat":
        return "katarina"
    if name == "kenen":
        return "kennen"
    if name == "kha":
        return "khazix"
    if name in ["kog","kogmow"]:
        return "kogmaw"
    if name == "lb":
        return "leblanc"
    if name in ["ls","lee"]:
        return "leesin"
    if name == "liss":
        return "lissandra"
    else:
        return name

# send_welcome_message

def send_welcome_message():
    welcomeText = "BuildCrank helps you find item build order for champions in LoL."
    welcomeText += "Type in a champion's name and role to get a suggested build!"
    log("sending welcome message")

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type":"greeting",
        "greeting": {
            "text": welcomeText
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def set_get_started_button():
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "call_to_actions",
        "thread_state": "new_thread",
        "call_to_actions": [
            {
                "payload": "get_started_clicked"
            }
        ]
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_help_post_message(recipient_id):
    text = "Open this menu at any time by typing help!\n\n"
    text += "Type any champion's name to get the champion's build order\n\n"
    text += "Don't like being prompted by buttons to specify what you want? "
    text += "Then give BuildCrank all the info (name,role,buildType) in one message\n\n"
    send_message(recipient_id,text)
    text2 = "Roles consist of: support,adc,mid,jungle,top\n\n"
    text2 += "Build types consist of: frequent(most frequently used build), and winrate (highest winrate build)\n\n"
    text2 += "Feel free to use common nicknames (heimer = heimerdinger, jg = jungle, freq = frequent, win = winrate, etc)\n\n"
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text2,
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "See some examples",
                            "payload": "example_clicked"
                        },
                        {
                            "type": "postback",
                            "title": "About BuildCrank",
                            "payload": "about_clicked"
                        },
                        {
                            "type": "postback",
                            "title": "Feedback/Bug Reports",
                            "payload": "feedback_clicked"
                        }
                    ]
                }
            }
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_build_type_post_message(recipient_id, championName,role):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=championName))
    championName = prettifyChampionName(championName)
    role = prettifyRole(role)

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "What type of build you want?",
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "Most Frequent Build",
                            "payload": "Most Frequent Build For "+ championName + " " + role
                        },
                        {
                            "type": "postback",
                            "title": "High Winrate Build",
                            "payload": "Highest Winrate Build For "+ championName + " " + role
                        }
                    ]
                }
            }
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_role_post_message(recipient_id, roles, championName,buildType):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=championName))
    championName = prettifyChampionName(championName)
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    if len(roles) == 1:
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": "Please specify which role you want",
                        "buttons": [
                            {
                                "type": "postback",
                                "title": championName + " " + prettifyRole(roles[0]),
                                "payload": championName + " " + prettifyRole(roles[0]) +" "+ buildType
                            }
                        ]
                    }
                }
            }
        })
    else:

        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": "Please specify which role you want",
                        "buttons": [
                            {
                                "type": "postback",
                                "title": championName + " " + prettifyRole(roles[0]),
                                "payload": championName + " " + prettifyRole(roles[0]) + " "+ buildType
                            },
                            {
                                "type": "postback",
                                "title": championName + " " + prettifyRole(roles[1]),
                                "payload": championName + " " + prettifyRole(roles[1]) +" "+ buildType
                            }
                        ]
                    }
                }
            }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()



if __name__ == '__main__':
    app.run(debug=True)
