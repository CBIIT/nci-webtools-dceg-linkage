#!/usr/bin/env python3
import datetime
import dateutil.parser
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# script to free token locks older than 15 minutes at some scheduled time
# triggered from CRON job
def main():
    with open('/analysistools/public_html/apps/LDlink/app/config.yml', 'r') as yml_file:
        config = yaml.load(yml_file, Loader=yaml.FullLoader)
    api_mongo_addr = config['api']['api_mongo_addr']
    mongo_username = config['database']['mongo_user_api']
    mongo_password = config['database']['mongo_password']
    mongo_port = config['database']['mongo_port']

    client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + api_mongo_addr + '/LDLink', mongo_port)
    db = client["LDLink"]
    users = db.api_users
    # current datetime
    present = getDatetime()
    unlockTokens = []
    # look at each token
    for user in users.find():
        if "locked" in user:
            locked = user["locked"]
            if locked != 0 and locked != -1:
                if isinstance(locked, datetime.datetime):
                    diff = present - locked
                else:
                    diff = present - dateutil.parser.parse(locked, ignoretz=True)
                diffMinutes = (diff.seconds % 3600) // 60.0
                # if token is locked for over 15 mins, unlock
                if diffMinutes > 15.0:
                    unlockTokens.append(user["token"])
    for token in unlockTokens:
        users.find_one_and_update({"token": token}, { "$set": {"locked": 0}})

if __name__ == "__main__":
    main()