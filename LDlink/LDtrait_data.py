#!/usr/bin/env python3
from datetime import datetime
import requests
import os
import sys
import json
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
import time
from timeit import default_timer as timer
import yaml
from LDutilites import get_config,get_config_admin
import LDutilites

start_time = timer() # measure script's run time
filename = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d') + ".tsv"
errFilename = "ldtrait_error_snps.json"

# Load variables from config file
path = LDutilites.config_abs_path
param_list = get_config(path)
param_list_db = get_config_admin(path)
tmp_dir = param_list['tmp_dir']
aws_info = param_list['aws_info']
ldtrait_src = param_list['ldtrait_src']

api_mongo_addr = param_list_db['api_mongo_addr']
mongo_username_api = param_list_db['mongo_username_api']
mongo_password = param_list_db['mongo_password']
mongo_port = param_list_db['mongo_port']
mongo_db_name = param_list_db['mongo_db_name']

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

# download daily update of GWAS Catalog
def downloadGWASCatalog():
    if (os.path.isfile(tmp_dir + filename)):
        print("Latest GWAS catalog already downloaded, deleting existing...")
        os.remove(tmp_dir + filename)
    r = requests.get(ldtrait_src, allow_redirects=True)
    with open(tmp_dir + filename, 'wb') as f:
        f.write(r.content)
    return filename

def main():
    instance = sys.argv[1]
    print("Downloading GWAS catalog...")
    filename = downloadGWASCatalog()
    print(filename + " downloaded.")

    # Connect to Mongo snp database
    client = MongoClient('mongodb://' + mongo_username_api + ':' + mongo_password + '@' + api_mongo_addr + '/'+ mongo_db_name, mongo_port)
    db = client["LDLink"]
    dbsnp = db.dbsnp

    # delete old error SNPs file if there is one
    if (os.path.isfile(tmp_dir + errFilename)):
        print("Deleting existing error SNPs file...")
        os.remove(tmp_dir + errFilename)

    # if gwas_catalog collection already exists, delete 
    if "gwas_catalog_tmp" in db.list_collection_names():
        print("Collection 'gwas_catalog_tmp' already exists. Dropping...")
        gwas_catalog_tmp = db.gwas_catalog_tmp
        gwas_catalog_tmp.drop()
    else: 
        gwas_catalog_tmp = db.gwas_catalog_tmp

    # read and insert downloaded file
    with open(tmp_dir + filename) as f:
        lines = f.readlines()
        headers = lines[0].strip().split('\t')
        print("\n".join(headers))
        headers.append("chromosome")
        headers.append("position_grch37")
        headers.append("position_grch38")
        # trim headers from list
        lines = lines[1:]
        print("Finding genomics coordinates from dbsnp and inserting to MongoDB collection...")
        no_dbsnp_match = 0
        missing_field = 0
        errSNPs = []
        for line in lines:
            values = line.strip().split('\t')
            # placeholder for chromosome to be retrieved from dbsnp
            values.append("NA")
            # placeholder for position_grch37 to be retrieved from dbsnp
            values.append("NA")
            # placeholder for position_grch38 to be retrieved from dbsnp
            values.append("NA")
            document = dict(list(zip(headers, values)))
            # check if orginal gwas row has populated rs number column
            # check field: "SNP_ID_CURRENT"
            # To-do: check field "SNPS" (with possible merged RSIDs and genomic coords)
            if 'SNP_ID_CURRENT' in document:
                if len(document['SNP_ID_CURRENT']) > 0:
                    # find chr, pos in dbsnp using rsid
                    record = dbsnp.find_one({"id": document['SNP_ID_CURRENT']})
                    # if found in dbsnp, add to chr, pos to record
                    if record is not None and (record["position_grch37"] != "NA" or record["position_grch38"] != "NA"): 
                        document["chromosome"] = record["chromosome"]
                        document["position_grch37"] = int(record["position_grch37"]) if record["position_grch37"] != "NA" else "NA"
                        document["position_grch38"] = int(record["position_grch38"]) if record["position_grch38"] != "NA" else "NA"
                        gwas_catalog_tmp.insert_one(document)
                    else:
                        document["err_msg"] = "Genomic coordinates not found in dbSNP."
                        errSNPs.append(document)
                        no_dbsnp_match += 1
                else:
                    document["err_msg"] = "SNP missing valid RSID."
                    errSNPs.append(document)
                    missing_field += 1
            else:
                document["err_msg"] = "GWAS Catalog entry missing SNP_ID_CURRENT key."
                errSNPs.append(document)
                missing_field += 1
        with open(tmp_dir + errFilename, 'a') as errFile:
            json.dump(errSNPs, errFile)

    print("Problematic GWAS variants:", missing_field)
    print("Genomic position not found in dbSNP:", no_dbsnp_match)
    print("===== Total # variants w/ no GRCh37 and GRCh38 genomic positions:", missing_field + no_dbsnp_match)
    print("GWAS catalog inserted into MongoDB.")

    print("Indexing GWAS catalog Mongo collection...")
    gwas_catalog_tmp.create_index([("chromosome", ASCENDING), ("position_grch37", ASCENDING)])
    gwas_catalog_tmp.create_index([("chromosome", ASCENDING), ("position_grch38", ASCENDING)])
    print("Indexing completed.")
    # if gwas_catalog collection already exists, delete 
    if "gwas_catalog" in db.list_collection_names():
        print("Collection 'gwas_catalog' already exists. Dropping...")
        gwas_catalog = db.gwas_catalog
        gwas_catalog.drop()
    print("Rename gwas_catalog_tmp collection to gwas_catalog")
    gwas_catalog_tmp.rename("gwas_catalog")
    if (os.path.isfile(tmp_dir + filename)):
        print("Deleting raw data file: " + filename)
        os.remove(tmp_dir + filename)
    end_time = timer()
    print(("Completion time:\t--- %s minutes ---" % str(((end_time - start_time) / 60.0))))
if __name__ == "__main__":
    main()