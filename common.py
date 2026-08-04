import discord
import traceback
import os
import pickle
import json

# variables // i cba adding these to env so eh
joinandleavechannelid = 1515297901771755600
messageloggingchannelid = 1515298744474669170
etanid = 614014104667160576
membercountid = 1515299581422993538
serverid = 1515268345312837653
moderatorroleid = 1515289661944107048
starboardchannel = 1515298029094047754
ruiroleid = 1515300776451506290
bottrapchannelid = 1515298163467223112
timeoutcornerroleid = 1515277839602028595
lastcachedmembercount = 0

# what the bot is "playing", will cycle through randomly every minute
prescencecycles = ["Yuri", "Yuri"]

if not os.path.exists("env.json"):
    with open("env.json", "w") as file:
        json.dump({
            "token": "your_discord_bot_token_here",
            "fontpath": "path_to_a_font_file.ttf"
        }, file)
    input("env.json file not found. A sample one has been created, please fill it, then press enter to continue...")

env = json.load(open("env.json", "r"))

datastores = ["customroles", "ships", "profiles", "achievements", "playerachievements"] # json files to create
for item in datastores:
    if os.path.exists(f"{item}.pkl"):
        data = pickle.load(open(f"{item}.pkl", "rb"))
        with open(f"{item}.json", "w") as file:
            json.dump(data, file, indent=4)
            print(f"Converted [{item}.pkl] to [{item}.json]")
    if not os.path.exists(f"{item}.json"):
        with open(f"{item}.json", "w") as file:
            json.dump({}, file)
        print(f"Created new file [{item}.json]")

datastoresbuttheseonesarelists = ["starboard"] # json files to create but these are lists
for item in datastoresbuttheseonesarelists:
    if os.path.exists(f"{item}.pkl"):
        data = pickle.load(open(f"{item}.pkl", "rb"))
        with open(f"{item}.json", "w") as file:
            json.dump(data, file, indent=4)
            print(f"Converted [{item}.pkl] to [{item}.json]")
    if not os.path.exists(f"{item}.json"):
        with open(f"{item}.json", "w") as file:
            json.dump([], file)
        print(f"Created new file [{item}.json]")

del datastores
del datastoresbuttheseonesarelists

# other functions
def formatUsername(user: discord.User): # Fancy formatting for usernames // displayname (@username)
    if user.display_name == None:
        return f"{user.name}"
    else:
        return f"{user.display_name} (@{user.name})"

def getDisplay(user: discord.User): # incase we only want to get display name and the users display is same as username
    if user.display_name == None:
        return user.name
    else:
        return user.display_name

def saveData(store: str, newdata: dict): # Saves data to a specified .json file
    print(f"Saving [{store}]...")
    try:
        backup = loadData(store)
        with open(f"{store}_backup.json", "w") as file:
            json.dump(backup, file)
        with open(f"{store}.json", "w") as file:
            json.dump(newdata, file)
        os.remove(f"{store}_backup.json")
        return True # Return true if it succeeds
    except Exception:
        traceback.print_exc()
        with open(f"{store}.json", "w") as file:
            json.dump(backup, file)
        return False # Otherwise return false

def loadData(store: str): # Gets data from a specified .json file
    try:
        with open(f"{store}.json", "r") as file:
            return json.load(file) # Return file data if it succeeds
    except Exception:
        traceback.print_exc()
        return "" # Otherwise return an empty string

def truncateMessage(message, length):
    if len(message) <= length:
        return message
    else:
        return message[:length-40] + f"... [{len(message)-length+40} more characters]"
