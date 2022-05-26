#!/usr/bin/env python3
import datetime
import dateutil.parser
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from LDutilites import get_config_admin
import LDutilites
# get current date and time
def getDatetime():
    return datetime.datetime.now()

# script to free token locks older than 15 minutes at some scheduled time
# triggered from CRON job
def main():
    path = LDutilites.config_abs_path
    param_list_db = get_config_admin(path)
    api_mongo_addr = param_list_db['api_mongo_addr']
    mongo_username_api = param_list_db['mongo_username_api']
    mongo_password = param_list_db['mongo_password']
    mongo_port = param_list_db['mongo_port']
  
    client = MongoClient('mongodb://' + mongo_username_api + ':' + mongo_password + '@' + api_mongo_addr + '/LDLink', mongo_port)
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