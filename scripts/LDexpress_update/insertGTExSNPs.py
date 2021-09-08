# PREREQ: download raw data input from https://storage.googleapis.com/gtex_analysis_v8/reference/GTEx_Analysis_2017-06-05_v8_WholeGenomeSeq_838Indiv_Analysis_Freeze.lookup_table.txt.gz

import sys
import os
import json
import gzip
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
from timeit import default_timer as timer

def insertRecord(db, record):
    gtex_snps = db['gtex_snps']
    gtex_snps.insert_one(record)

def buildRecord(db, header, row):
    # print("header", header)
    # print("row", row)
    record = dict(zip(header, row)) 
    # print("record", record)
    # insert into table
    insertRecord(db, record)

def main():
    print("start script")
    start = timer()
    filename = sys.argv[1]
    print("filename", filename)
    
    client = MongoClient()
    db = client['LDLink']

    # if mongo collection already exists, drop
    if "gtex_snps" in db.list_collection_names():
        print("gtex_snps mongo collection already exists, dropping")
        db['gtex_snps'].drop()

    # if debug problematic out files already exist, delete
    if (os.path.exists("problematic.txt")):
        print("problematic.txt already exists, deleting...")
        os.remove("problematic.txt")
    if (os.path.exists("problematicNA.txt")):
        print("problematicNA.txt already exists, deleting...")
        os.remove("problematicNA.txt")

    print("parsing and inserting...")

    inserted = 0
    problematicNA = 0
    problematic = 0
    count = 0
    with gzip.open(filename, 'rb') as f_in:
        header = next(f_in).decode("utf-8").strip().split('\t') + ["chr_b37", "variant_pos_b37"]
        for line in f_in:
            row = line.decode("utf-8").strip().split('\t')
            # print(row)
            chr_pos_b37 = row[7].split('_')
            if (chr_pos_b37[0] == "NA"):
                problematicNA += 1
                row += ["NA variant_id_b37 column."]
                # write to file
                with open("problematicNA.txt", 'a') as problematicNAFile:
                    problematicNAFile.write(str(row) + '\n')
            else:
                if ("." in chr_pos_b37[0]):
                    chr_b37 = chr_pos_b37[0].split(".")[1]
                else:
                    chr_b37 = chr_pos_b37[0]
                variant_pos_b37 = chr_pos_b37[1]
                # print(chr_pos_b37)
                # check if chromosome is 1-22, X, or Y
                # check if position is numeric
                if (((chr_b37.isnumeric() and int(chr_b37) in range(1, 22 + 1)) or (chr_b37 in ["X", "Y"])) and variant_pos_b37.isnumeric()):
                    # create record and insert into mongo collection
                    if (len(row) is 8):
                        buildRecord(db, header, row + [chr_b37, variant_pos_b37])
                        inserted += 1
                    else:
                        problematic += 1
                        row += ["Missing column."]
                        # write to file
                        with open("problematic.txt", 'a') as problematicFile:
                            problematicFile.write(str(row) + '\n')
                else:
                    # capture problematic rows
                    problematic += 1
                    row += ["Invalid variant_id_b37 column."]
                    # write to file
                    with open("problematic.txt", 'a') as problematicFile:
                        problematicFile.write(str(row) + '\n')
                count += 1
                if (count % 100000 == 0):
                    print(count, "records inserted...")
                # if (count == 1000):
                #     break
            
    # create compound index on chr_b37, variant_pos_b37
    print("creating indexes...")
    db.gtex_snps.create_index([("chr_b37", ASCENDING), ("variant_pos_b37", ASCENDING)])

    print("finish script")
    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("# inserted", inserted)
    print("# problematic", problematic)
    print("# problematic b/c NA", problematicNA)

if __name__ == "__main__":
    main()