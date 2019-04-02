#!/usr/bin/env python
import datetime
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
contents = open("/analysistools/public_html/apps/LDlink/app/SNP_Query_loginInfo.ini").read().split('\n')
username = 'ncianalysis_api'
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# script to free token locks older than 15 minutes at some scheduled time
# triggered from CRON job
def main():
    with open('/analysistools/public_html/apps/LDlink/app/config.yml', 'r') as f:
        config = yaml.load(f)
    api_mongo_addr = config['api']['api_mongo_addr']
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    # current datetime
    present = getDatetime()
    unlockTokens = []
    # look at each token
    for user in users.find():
        locked = user["locked"]
        if locked != 0:
            diff = present - locked
            diffMinutes = diff.seconds % 3600 / 60.0
            # if token is locked for over 15 mins, unlock
            if diffMinutes > 15.0:
                unlockTokens.append(user["token"])
    for token in unlockTokens:
        users.find_one_and_update({"token": token}, { "$set": {"locked": 0}})

if __name__ == "__main__":
    main()