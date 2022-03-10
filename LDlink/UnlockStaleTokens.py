#!/usr/bin/env python3
import datetime
import dateutil.parser
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from LDcommon import connectMongoDBReadOnly

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# script to free token locks older than 15 minutes at some scheduled time
# triggered from CRON job
def main():
    db = connectMongoDBReadOnly()
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