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

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    message_text = formatMessage(message_text)
                    isPostBackClicked = False
                    if message_text.lower().strip() == "help":
                        sendHelpMessage(sender_id)
                        return "ok", 200

                    championName = getChampName(message_text)
                    if isValidChampionName(championName):
                        if isRoleSpecified(message_text):
                            role = getRole(championName, message_text)
                        else:
                            print "Please Choose a role"
                            send_post_message(sender_id,"hilo world")
                            return "ok", 200
                    else:
                        send_message(sender_id, "Sorry I don't recognize the champion name " + championName)
                        return "ok", 200

                    if isValidRole(championName, role):
                        sendPrettyBuild(championName, role, sender_id)
                    else:
                        send_message(sender_id,
                                     "Sorry " + championName + "'s " + role + " build is not available")
                        return "ok", 200


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    roleList = getRoleList(championName)

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

def getKeyWordList():
    keywords = []
    with open('champNames.json', 'r') as fp:
        champNames = json.load(fp)
    keywords += champNames
    roles = ['sup','supp', 'support', "bot", 'adc', 'mid', "middle", 'jg', 'jungle', 'top']
    buildTypes = ['frequent', 'frequently','popular','win','winning','winrate','full','core','start','starting','starter']
    keywords += roles
    keywords += buildTypes
    return keywords

def sendHelpMessage(sender_id):
    send_message(sender_id, "type in a champion's name to get a build order of a random common role of the champion.\n"
                            "type in a champion's name + role name to get build order for specified role \n"
                            "Ex1) annie \n"
                            "Ex2) annie mid")
def getRoleList(champName):
    with open('champData.json', 'r') as fp:
        data = json.load(fp)
    roleList = data[champName].keys()
    return roleList

def isValidChampionName(championName):
    with open('champNames.json', 'r') as fp:
        champNames = json.load(fp)
    if championName in champNames:
        return True
    else:
        return False
def isValidRole(championName,role):
    roleList = getRoleList(championName)
    if role in roleList:
        return True
    else:
        return False

def getChampName(message_text):
    msgList = message_text.split(" ")
    if len(msgList) == 1:
        championName = updateChampNameFormat(message_text)
    else:
        championName = getSpecifiedChampName(message_text)  # message contain both champ name and role, parse out name
        championName = updateChampNameFormat(championName)
    return championName

def isRoleSpecified(message_text):
    roles = ['sup', 'supp', 'support', "bot", 'adc', 'mid', "middle", 'jg', 'jungle', 'top']
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

def sendPrettyBuild(championName,role,sender_id):
    with open('champData.json', 'r') as fp:
        data = json.load(fp)
    prettyChampName = championName[0].upper() + championName[1:]
    prettyRoleName = prettifyRole(role)
    res = ""
    res += "Most Frequent Build For: " + prettyChampName + " " + prettyRoleName + "\n"
    freqFullBuild = data[championName][role]["FreqFullBuild"]
    itemCount = 1
    for i in range(len(freqFullBuild)):
        res += str(itemCount) + ") "
        res += freqFullBuild[i] + "\n"
        itemCount += 1
    send_message(sender_id, res)




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

def make_role_buttons(championName,roles):
    res = ""
    for i in range(len(roles)):
        if i == len(roles)-1:
            res += "{\n\t" + '"type": "postback",\n\t"title": "' + championName + ' ' + roles[i] + '",\n\t"payload": "' + championName+ " " + roles[i] + '"\n}\n'
        else:
            res += "{\n\t" + '"type": "postback",\n\t"title": "' + championName + ' ' + roles[i] + '",\n\t"payload": "' + championName+ " " + roles[i] + '"\n},\n'

def send_post_message(recipient_id, roles,championName):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=championName))

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
                    "text": "Choose a role for the build you want",
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "Akali Top",
                            "payload": "Akali Top"
                        },
                        {
                            "type": "postback",
                            "title": "Start Chatting",
                            "payload": "USER_DEFINED_PAYLOAD"
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
