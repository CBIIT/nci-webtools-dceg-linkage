#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
import requests
import os
import sys
import json
import zipfile
import boto3
from pymongo import ASCENDING
from timeit import default_timer as timer
from LDutilites import get_config
from LDcommon import connectMongoDBReadOnly

start_time = timer() # measure script's run time
filename = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d') + ".tsv"
filename_download = "gwas_catalog_" + datetime.today().strftime('%Y-%m-%d')  + ".zip"
errFilename = "ldtrait_error_snps.json"

# Load variables from config file
#path = LDutilites.config_path
param_list = get_config()
tmp_dir = param_list['tmp_dir']
ldtrait_src = param_list['ldtrait_src']
data_dir = param_list['data_dir']
api_users_backup_dir = os.path.join(data_dir, "backups", "api_users")
api_users_backup_retention_days = 7
# Opt-in: when set, backups go to S3 (SSE-KMS) instead of the shared EFS data dir --
# e.g. API_USERS_BACKUP_S3_BUCKET=ldlink-data-nonprod, API_USERS_BACKUP_S3_PREFIX=ldlink/backups/api_users
api_users_backup_s3_bucket = os.environ.get("API_USERS_BACKUP_S3_BUCKET") or None
api_users_backup_s3_prefix = os.environ.get("API_USERS_BACKUP_S3_PREFIX", "ldlink/backups/api_users").strip("/")


if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

# export api_users collection to a dated JSON file, as a backup -- to S3 (SSE-KMS) if
# API_USERS_BACKUP_S3_BUCKET is configured, otherwise to the EFS-backed data dir
def backupApiUsers():
    db = connectMongoDBReadOnly()
    users = list(db.api_users.find())
    backup_filename = "api_users_" + datetime.today().strftime('%Y-%m-%d') + ".json"
    # default=str handles ObjectId/datetime fields, which json.dump can't serialize directly
    backup_body = json.dumps(users, indent=2, default=str)

    if api_users_backup_s3_bucket:
        key = f"{api_users_backup_s3_prefix}/{backup_filename}"
        boto3.client("s3").put_object(
            Bucket=api_users_backup_s3_bucket,
            Key=key,
            Body=backup_body.encode("utf-8"),
            ServerSideEncryption="aws:kms",
        )
        print(f"Backed up {len(users)} api_users records to s3://{api_users_backup_s3_bucket}/{key}")
        deleteExpiredApiUsersBackupsS3()
        return

    os.makedirs(api_users_backup_dir, exist_ok=True)
    backup_path = os.path.join(api_users_backup_dir, backup_filename)
    fd = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(backup_body)

    print(f"Backed up {len(users)} api_users records to {backup_path}")
    deleteExpiredApiUsersBackups()

# delete api_users backup files older than the retention window
def deleteExpiredApiUsersBackups():
    cutoff = datetime.today() - timedelta(days=api_users_backup_retention_days)
    for entry in os.listdir(api_users_backup_dir):
        if not entry.startswith("api_users_") or not entry.endswith(".json"):
            continue
        entry_path = os.path.join(api_users_backup_dir, entry)
        if datetime.fromtimestamp(os.path.getmtime(entry_path)) < cutoff:
            os.remove(entry_path)
            print(f"Deleted expired api_users backup: {entry_path}")

# delete api_users backup objects older than the retention window from S3
def deleteExpiredApiUsersBackupsS3():
    cutoff = datetime.now(timezone.utc) - timedelta(days=api_users_backup_retention_days)
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=api_users_backup_s3_bucket, Prefix=api_users_backup_s3_prefix + "/"):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                s3.delete_object(Bucket=api_users_backup_s3_bucket, Key=obj["Key"])
                print(f"Deleted expired api_users backup: s3://{api_users_backup_s3_bucket}/{obj['Key']}")

# download daily update of GWAS Catalog
def downloadGWASCatalog():
    tsv_path = tmp_dir + filename
    zip_path = tmp_dir + filename_download

    if (os.path.isfile(tsv_path)):
        print("Latest GWAS catalog already downloaded, deleting existing...")
        os.remove(tsv_path)

    if (os.path.isfile(zip_path)):
        os.remove(zip_path)

    r = requests.get(ldtrait_src, allow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError(f"GWAS Catalog source unavailable (HTTP {r.status_code}); aborting update.")

    with open(zip_path, 'wb') as f:
        f.write(r.content)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            tsv_members = [member for member in zip_file.namelist() if member.lower().endswith('.tsv')]
            if len(tsv_members) == 0:
                raise RuntimeError("GWAS archive does not contain a TSV file; aborting update.")
            tsv_member = tsv_members[0]
            print("Extracting TSV from GWAS archive:", tsv_member)
            with zip_file.open(tsv_member) as zipped_tsv, open(tsv_path, 'wb') as extracted_tsv:
                extracted_tsv.write(zipped_tsv.read())
    except zipfile.BadZipFile:
        raise RuntimeError("GWAS source is not a valid ZIP archive; aborting update.")
    finally:
        if (os.path.isfile(zip_path)):
            os.remove(zip_path)

    return filename

def main():
    try:
        print("Backing up api_users collection...")
        backupApiUsers()
    except Exception as backup_error:
        # Non-fatal: a failed backup shouldn't block the daily GWAS catalog update below.
        print(f"Failed to back up api_users collection: {backup_error}")

    print("Downloading GWAS catalog...")
    filename = downloadGWASCatalog()
    print(filename + " downloaded.")

    db = connectMongoDBReadOnly()
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