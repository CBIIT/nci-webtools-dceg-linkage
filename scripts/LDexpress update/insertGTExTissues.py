import json
import requests
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
from timeit import default_timer as timer

def get_ldexpress_tissues():
    PAYLOAD = {
            "format" : "json",
            "datasetId": "gtex_v8"
        }
    REQUEST_URL = "https://gtexportal.org/rest/v1/dataset/tissueInfo"
    try:
        r = requests.get(REQUEST_URL, params=PAYLOAD)
        responseObj = json.loads(r.text)
    except:
        errorObj = {
            "error": "Failed to retrieve tissues from GTEx Portal server."
        }
        return json.dumps(json.loads(errorObj))
    return responseObj

def insertRecord(db, record):
    gtex_tissues = db['gtex_tissues']
    gtex_tissues.insert_one(record)

def main():
    print("start script")
    start = timer()
    
    client = MongoClient()
    db = client['LDLink']

    # if mongo collection already exists, drop
    if "gtex_tissues" in db.list_collection_names():
        print("gtex_tissues mongo collection already exists, dropping")
        db['gtex_tissues'].drop()

    tissues = get_ldexpress_tissues()

    inserted = 0
    for tissue in tissues['tissueInfo']:
        print(tissue)
        insertRecord(db, tissue)
        inserted += 1
            
    print("finish script")
    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("# inserted", inserted)

if __name__ == "__main__":
    main()