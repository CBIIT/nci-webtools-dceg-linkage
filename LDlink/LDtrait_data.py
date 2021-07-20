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


start_time = timer() # measure script's run time
filename = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d') + ".tsv"
errFilename = "ldtrait_error_snps.json"

# Load variables from config file
with open('/analysistools/public_html/apps/LDlink/app/config.yml', 'r') as c:
# with open('config.yml', 'r') as c:
    config = yaml.load(c)
ldtrait_src = config['data']['ldtrait_src']
tmp_dir = config['data']['tmp_dir']
mongo_username = config['database']['mongo_user_api']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']

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
    if instance == "web":
        client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@localhost/LDLink', mongo_port)
    else:
        client = MongoClient('localhost')
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
        headers.append("chromosome_grch37")
        headers.append("position_grch37")
        # trim headers from list
        lines = lines[1:]
        print("Finding genomics coordinates from dbsnp and inserting to MongoDB collection...")
        no_dbsnp_match = 0
        missing_field = 0
        errSNPs = []
        for line in lines:
            values = line.strip().split('\t')
            values.append("NA")
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
                    if record is not None and len(record["chromosome"]) > 0 and len(record["position"]) > 0: 
                        document["chromosome_grch37"] = str(record["chromosome"])
                        document["position_grch37"] = int(record["position"])
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
    print("===== Total # variants w/ no GRCh37 genomic positions:", missing_field + no_dbsnp_match)
    print("GWAS catalog inserted into MongoDB.")

    print("Indexing GWAS catalog Mongo collection...")
    gwas_catalog_tmp.create_index([("chromosome_grch37", ASCENDING), ("position_grch37", ASCENDING)])
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