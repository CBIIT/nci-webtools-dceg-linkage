#!/usr/bin/env python3
from datetime import datetime
import requests
import os
import sys
import json
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
import time
import yaml


start_time = time.time()  # measure script's run time
filename = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d') + ".tsv"
errFilename = "ldtrait_error_snps_" + datetime.today().strftime('%Y-%m-%d') + ".json"

# Load variables from config file
with open('/analysistools/public_html/apps/LDlink/app/config.yml', 'r') as c:
# with open('config.yml', 'r') as c:
    config = yaml.load(c)
ldtrait_src = config['data']['ldtrait_src']
tmp_dir = config['data']['tmp_dir']

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

    # client = MongoClient('mongodb://localhost/LDLink')
    # client = MongoClient('mongodb://' + username + ':' + password + '@localhost/LDLink', port)
    # Connect to Mongo snp database
    if instance == "web":
        contents = open("/analysistools/public_html/apps/LDlink/app/SNP_Query_loginInfo.ini").read().split('\n')
        # contents = open("./SNP_Query_loginInfo_test.ini").read().split('\n')
        username = 'ncianalysis_api'
        password = contents[1].split('=')[1]
        port = int(contents[2].split('=')[1])
        client = MongoClient('mongodb://' + username + ':' + password + '@localhost/LDLink', port)
    else:
        client = MongoClient('localhost')
    db = client["LDLink"]
    dbsnp = db.dbsnp151

    # if gwas_catalog collection already exists, delete 
    if "gwas_catalog" in db.list_collection_names():
        print("Collection 'gwas_catalog' already exists. Dropping...")
        gwas_catalog = db.gwas_catalog
        gwas_catalog.drop()
    else: 
        gwas_catalog = db.gwas_catalog

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
        problematic_gwas_variants = 0
        errSNPs = []
        for line in lines:
            values = line.strip().split('\t')
            values.append("NA")
            values.append("NA")
            document = dict(list(zip(headers, values)))
            # check if orginal gwas row has populated rs number column
            # check field: "SNP_ID_CURRENT"
            # To-do: check field "SNPS" (with possible merged RSIDs and genomic coords)
            if len(values[23]) > 0:
                # find chr, pos in dbsnp using rsid
                record = dbsnp.find_one({"id": values[23]})
                # if found in dbsnp, add to chr, pos to record
                if record is not None and len(record["chromosome"]) > 0 and len(record["position"]) > 0: 
                    document["chromosome_grch37"] = str(record["chromosome"])
                    document["position_grch37"] = int(record["position"])
                    gwas_catalog.insert_one(document)
                else:
                    document["err_msg"] = "Genomic coordinates not found in dbSNP."
                    errSNPs.append(document)
                    no_dbsnp_match += 1
            else:
                document["err_msg"] = "SNP missing valid RSID."
                errSNPs.append(document)
                problematic_gwas_variants += 1
        with open(tmp_dir + errFilename, 'a') as errFile:
            json.dump(errSNPs, errFile)

    print("Problematic GWAS variants:", problematic_gwas_variants)
    print("Genomic position not found in dbSNP:", no_dbsnp_match)
    print("===== Total # variants w/ no GRCh37 genomic positions:", problematic_gwas_variants + no_dbsnp_match)
    print("GWAS catalog inserted into MongoDB.")

    print("Indexing GWAS catalog Mongo collection...")
    gwas_catalog.create_index([("chromosome_grch37", ASCENDING), ("position_grch37", ASCENDING)])
    print("Indexing completed.")
    print(("Completion time:\t--- %s minutes ---" % str(((time.time() - start_time) / 60.0))))

if __name__ == "__main__":
    main()