# this script is written to improve the json schema of the "snp_col" SNPChip MongoDB collection
# old schema = { pos: <pos>, data: [ { "platform": <platform>, "chr": <chr> }, ... ] }
# new schema = { chr: <chr>, pos: <pos>, data: [ { "platform": <platform> }, ... ] }
# this will make it easier to generate GRCh38 positions with liftOver and keep both GRCh37 and GRCh38 positions in the same record

import time
import sys
import json
import datetime
import subprocess

currentDT = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
start_time = time.time()  # measure script's run time

def improveJSON(inputJSONFile, outputJSONFile):
    count = 0
    newRecordCount = 0
    # mismatchChrCount = 0
    # mistmatchChrObjs = []
    with open(outputJSONFile, 'a') as outfile:
        with open(inputJSONFile) as infile:
            for line in infile:
                jsonObj = json.loads(line)
                firstChr = jsonObj['data'][0]['chr']
                dataChrs = list(map(lambda x: x['chr'], jsonObj['data']))

                if (dataChrs.count(dataChrs[0]) != len(dataChrs)):
                    # chr mismatch in data
                    # print("jsonObj", jsonObj)
                    newDataEntries = []
                    keepDataEntries = []
                    for dataEntry in jsonObj['data']:
                        if dataEntry['chr'] != firstChr:
                            newDataEntries.append(dataEntry)
                        else:
                            keepDataEntries.append(dataEntry)
                    newKeepJSON = {
                        "chromosome_grch37": firstChr,
                        "position_grch37": int(jsonObj['pos']),
                        "data": list(map(lambda x: {"platform": x['platform']}, keepDataEntries))
                    }
                    # print("newKeepJSON", newKeepJSON)
                    outfile.write(json.dumps(newKeepJSON) + "\n")
                    for newData in newDataEntries:
                        newNewJSON = {
                            "chromosome_grch37": newData['chr'],
                            "position_grch37": int(jsonObj['pos']),
                            "data": [{"platform": newData['platform']}]
                        }
                        # print("newNewJSON", newNewJSON)
                        outfile.write(json.dumps(newNewJSON) + "\n")
                        newRecordCount += 1
                else:
                    # no chr mismatch in data
                    newJSON = {
                        "chromosome_grch37": firstChr,
                        "position_grch37": int(jsonObj['pos']),
                        "data": list(map(lambda x: {"platform": x['platform']}, jsonObj['data']))
                    }
                    outfile.write(json.dumps(newJSON) + "\n")
                count += 1
                if count % 100000 == 0:
                    print("count", count)
                    print("newRecordCount", newRecordCount)
    print("count", count)
    print("newRecordCount", newRecordCount)

def main():
    print("Starting JSON schema improvement script for snp_col...")
    try:
        inputJSONFile = sys.argv[1]
        outputJSONFile = sys.argv[2]
    except:
        print("USAGE: python3 improveJSON.py <INPUT_SNP_COL_JSON> <OUTPUT_SNP_COL_JSON>")
        print("EXAMPLE: python3 improveJSON.py ./export_snp_col.json ./improved_snp_col.json")
        sys.exit(1)

    improveJSON(inputJSONFile, outputJSONFile)

    print("Script completed [" + str(time.time() - start_time) + " seconds elapsed]...")

    
if __name__ == "__main__":
    main()