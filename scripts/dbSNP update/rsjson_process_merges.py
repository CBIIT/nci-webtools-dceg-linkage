# LAST UPDATED 07/16/2021 FOR dbSNP b155

import json
import sys
from pymongo import MongoClient
from bson import json_util, ObjectId

def queryMongoRSID(db, rsid):
    query_results = db.dbsnp.find_one({"id": rsid})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def writeJSON(merge_record):
    with open('merged_filtered.json', 'a') as outfile:
        json.dump(merge_record, outfile)
        outfile.write('\n')

def writeLog(msg, data):
    with open('merged_filtered.log.txt', 'a') as outfile:
        json.dump({"msg": msg, "data": data }, outfile)
        outfile.write('\n')

def main():
    filename = sys.argv[1]
    client = MongoClient()
    db = client["LDLink"]
    with open(filename, 'r') as f_in:
        for line in f_in:
            record = json.loads(line)
            file_id = record['id']
            file_merges = record['merged_into']

            query_results = queryMongoRSID(db, file_id)
            # if merged rsid is found, toss record
            # else if merged rsid is not found, keep record and write to new file
            if query_results is not None:
                msg = "Record found for RSID: " + file_id + "[SKIPPED]"
                writeLog(msg, [])
            else: 
                for merge_rsid in file_merges:
                    query_merge = queryMongoRSID(db, merge_rsid)
                    if query_merge is not None:
                        merge_record = {
                            "id": file_id,
                            "chromosome": query_merge['chromosome'],
                            "position_grch37": query_merge['position_grch37'],
                            "position_grch38": query_merge['position_grch38'],
                            "function": query_merge['function'],
                            "type": query_merge['type'],
                            "ref_id": merge_rsid
                        }
                        msg = "Record not found for RSID: " + file_id + "[ADDED]"
                        writeLog(msg, merge_record)
                        writeJSON(merge_record)
                        break

if __name__ == "__main__":
    main()