#!/usr/bin/env python
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = 'ncianalysis_api'
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])


# script to unlock all tokens at EOD or some scheduled time
# triggered from CRON job
def main():
    # db.foo.updateMany({}, {$set: {lastLookedAt: Date.now() / 1000}})
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_mongo_addr = config['api']['api_mongo_addr']
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    users.update_many({}, { "$set": {"locked": 0}})

if __name__ == "__main__":
    main()