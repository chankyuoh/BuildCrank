import os
import sys
import json
import string
import requests
from flask import Flask, request

def send_message(sender_id,msg):
    print msg


def sendHelpMessage(sender_id):
    send_message(sender_id, "type in a champion's name to get a build order. \n"
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
def isValidInput(message_text):
    msgList = message_text.split(" ")
    if len(msgList) == 1 or len(msgList) == 2:
        return True
    else:
        return False

def getChampName(message_text):
    msgList = message_text.split(" ")
    if len(msgList) == 2:
        championName = getSpecifiedChampName(message_text)  # message contain both champ name and role, parse out name

    championName = updateChampNameFormat(championName)
    return championName

def getRole(championName,message_text):
    msgList = message_text.split(" ")
    if len(msgList) == 1:
        roleList = getRoleList(championName)
        return roleList[0]  # first element = highest played role
    elif len(msgList) == 2:
        return getSpecifiedRole(message_text)





def sendPrettyBuild(championName,role,sender_id,original_message):
    with open('champData.json', 'r') as fp:
        data = json.load(fp)
    res = ""
    res += "Suggested build for: " + original_message + "\n"
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
    roles = ['supp', 'support', "bot", 'adc', 'mid', "middle", 'jg', 'jungle', 'top']
    for msg in msgList:
        original_msg = msg
        msg = msg.lower()
        if msg in roles:
            msgList.remove(original_msg)
    return "".join(msgList)


def getSpecifiedRole(message_text):
    roles = ['supp', 'support', "bot", 'adc', 'mid', "middle", 'jg', 'jungle', 'top']
    msgList = message_text.split(" ")
    for msg in msgList:
        msg = msg.lower()
        if msg in roles:
            if msg == "supp" or msg == "support":
                return "Support"
            if msg == "bot" or msg == "adc":
                return "ADC"
            if msg == "mid" or msg == "middle":
                return "Middle"
            if msg == "jg" or msg == "jungle":
                return "Jungle"
            if msg == "top":
                return "Top"
    return ""

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

def webhook():

    message_text = "akali top"
    sender_id = 1
    original_message = message_text
    original_champion_name = getSpecifiedChampName(message_text)
    if message_text == "help":
        sendHelpMessage(sender_id)

    if isValidInput(message_text):
        championName = getChampName(message_text)
        role = getRole(championName, message_text)
    else:
        send_message(sender_id, "Sorry I don't understand your input. Please type help")

    if isValidChampionName(championName):
        if isValidRole(championName, role):
            sendPrettyBuild(championName,role, sender_id, original_message)
        else:
            send_message(sender_id, "Sorry the build for " + role + "is not available for " + original_champion_name)
    else:
        send_message(sender_id, "Sorry I don't recognize that champion name")


webhook()
