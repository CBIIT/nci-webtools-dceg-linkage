# dbsnp-mongodb
Scripts to filter dbsnp records provided by NCBI and create files that can be imported to a MongoDB collection. NCBI dbsnp records are located here: ftp://ftp.ncbi.nlm.nih.gov/snp/.redesign/

Built off Lon Phan's `rsjson_test.py` (lonphan@ncbi.nlm.nih.gov)

## Step 1: Parse chromosome files 1 - 22, X and Y.

Includes script `rsjson_mongo_filter.py` to parse dbsnp .json.gz files and creates .json files that can be imported into MongoDB collection(s).

- Outputs .json file(s): `chr_#_filtered.json`

Each row of output file(s) contains a variant JSON object with keys: RS id, chromosome, position, type (snv, delins, etc), and function (annotation). Record will be duplicated for each of the variant's merged RS ids - meaning, another record will be created with all the same fields except the RS id key (which will be the merged variant's RS id). This file can be imported into MongoDB via mongoimport.

### Running script

Clone this repo into your data directory on the Biowulf cluster /data/your_username. 

Create folder named `json_refsnp` in the repo's directory and place all compressed json `json.gz` files in folder.

Run `./rsjson_run.sh` to queue 24 jobs to process the 24 compressed chromosome .json.gz files.

## Step 2: Import chromosome variants and index collection.

Use mongoimport to import `processed_merges.json` into the Mongo dbsnp build:

`mongoimport --db <db_name> --collection <collection_name> --file chr_#_filtered.json`

Use this script to import ALL files in a folder into a MongoDB collection:

`for filename in *; do mongoimport --db <db_name> --collection <collection_name> --file $filename; done`

Create indexes on the collection to significantly speed up queries. Log into the the Mongo shell and execute these commands:

`use <db_name>`
`db.<collection_name>.createIndex({id: 1})`
`db.<collection_name>.createIndex({chromosome: 1, position: 1})`

This process may take a long time. Make sure to keep your machine awake to prevent loss of progress.

## Step 3: Parse merged variants file.

Includes scripts `rsjson_find_merges.py` and `rsjson_process_merges.py` to find and parse merged variants set aside in refsnp-merged.json.gz file. `rsjson_find_merges.py` parses the refsnp-merged.json.gz file for required fields and outputs a .json file. `rsjson_process_merges.py` processed the file outputted from `rsjson_find_merges.py` by looking up each merged RS id in MongoDB dbsnp to prevent duplicate insertions and if the record does not already exists, it will query the reference RS id's merged RS id and create a record with the data. The newly created merged RS id records will be in a new file called processed_merges.json .

- `rsjson_find_merges.py` outputs .json file: `refsnp-merged_merges.json`
- `rsjson_process_merges.py` outputs .json file `processed_merges.json`

Each row of output file `processed_merges.json` contains a variant JSON object with keys: RS id, chromosome, position, type (snv, delins, etc), and function (annotation). This file can be imported into MongoDB via mongoimport.

### Running scripts

Run `./rsjson_run_merges.sh` to queue job to parse the refsnp-merged.json.gz file. Make sure refsnp-merged.json.gz is located in the `json_refsnp` directory.

Run `python rsjson_process_merges.py refsnp-merged_merges.json` to process the parsed RS ids and create records to be imported the MongoDB dbsnp build.

## Step 4: Import merged variants and index collection.

Again, use mongoimport to import `processed_merges.json` into the Mongo dbsnp build:

`mongoimport --db <db_name> --collection <collection_name> --file processed_merges.json`


