#!/usr/bin/env python3
from datetime import datetime
import requests
import os
import sys
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
import time
import yaml


# contents = open("/analysistools/public_html/apps/LDlink/app/SNP_Query_loginInfo.ini").read().split('\n')
# username = 'ncianalysis_api'
# password = contents[1].split('=')[1]
# port = int(contents[2].split('=')[1])

start_time = time.time()  # measure script's run time

# Load variables from config file
with open('config.yml', 'r') as c:
    config = yaml.load(c)
ldtrait_src = config['data']['ldtrait_src']
tmp_dir = config['data']['tmp_dir']

if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

# Load variables from config file
with open('config.yml', 'r') as c:
    config = yaml.load(c)
ldtrait_src = config['data']['ldtrait_src']

# download daily update of GWAS Catalog
def downloadGWASCatalog():
    filename = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d') + ".tsv"
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
        # contents = open("/analysistools/public_html/apps/LDlink/app/SNP_Query_loginInfo.ini").read().split('\n')
        contents = open("./SNP_Query_loginInfo_test.ini").read().split('\n')
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
    filename = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d') + ".tsv"
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
        for line in lines:
            values = line.strip().split('\t')
            if len(values[23]) > 0:
                # find chr, pos in dbsnp using rsid
                record = dbsnp.find_one({"id": values[23]})
                # if found, add to chr, pos to record
                if record is not None and len(record["chromosome"]) > 0 and len(record["position"]) > 0: 
                    values.append(str(record["chromosome"]))
                    values.append(int(record["position"]))
                else:
                    values.append("NA")
                    values.append("NA")
                    no_dbsnp_match += 1
            else:
                values.append("NA")
                values.append("NA")
                problematic_gwas_variants += 1
            document = dict(list(zip(headers, values)))
            # if document["SNPS"][0:2] != "rs" and document["SNPS"][0:3] != "chr" and document["SNPS"][0:3] != "Chr":
            #     print document["SNPS"]
            # print document
            gwas_catalog.insert_one(document)

    print("Problematic GWAS variants:", problematic_gwas_variants)
    print("Genomic position not found in dbSNP:", no_dbsnp_match)
    print("===== Total # variants w/ no GRCh37 genomic positions:", problematic_gwas_variants + no_dbsnp_match)
    print("GWAS catalog inserted into MongoDB.")

    print("Indexing GWAS catalog Mongo collection...")
    gwas_catalog.create_index([("chromosome_grch37", ASCENDING), ("position_grch37", ASCENDING)])
    print("Indexing completed.")

    print(("Completion time:\t--- %s minutes ---" % str(((time.time() - start_time) / 60.0))))


    # with open('/analysistools/public_html/apps/LDlink/app/config.yml', 'r') as f:
    #     config = yaml.load(f)
    # api_mongo_addr = config['api']['api_mongo_addr']
    # # client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    # client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    # db = client["LDLink"]
    # users = db.api_users

if __name__ == "__main__":
    main()