# dbsnp-mongodb
Scripts to parse NCBI's dbsnp records and outputs files that can be imported to a MongoDB collection. 

Last updated JULY 2021 for dbSNP b155 import. Built off Lon Phan's `rsjson_test.py` (lonphan@ncbi.nlm.nih.gov)

## Download dbSNP (latest build) raw data files from NCBI

Download all data from ftp `ftp://ftp.ncbi.nih.gov/snp/latest_release/JSON/`.

Run `md5sum -c CHECKSUMS` to verify data integrity. Re-download any files that fail the check.

## Step 1: Parse raw dbsnp chromosome files 1 - 22, X, Y, and "merged".

Includes script `rsjson_parse_data_mongo.py` to parse dbsnp .json.bz2 files and creates .json files that can be imported into a MongoDB collection. Also finds merged variants from `refsnp-merged.json.bz2` and parses that file for extra merged variants. Further processing is required after chr1-22,X and Y .json files are imported to MongoDB to include these 'extra' merged variants.

- Inputs: `/path/to/refsnp-<chr1-22,chrX,chrY,merged>.json.bz2`(required) `/path/to/output_directory`(required) `/path/to/tmp_directory`(optional)
- Output for `refsnp-<chr1-22,chrX,chrY>.json.bz2`: `chr_#_filtered.json`(parsed data ready to be imported into mongo collection) and `chr_#_filtered.ERROR.json`(dbsnp records that ran into any issues during parsing)
- Output for `refsnp-merged.json.bz2`: `merged_filtered.json`(parsed merged variants data that is used as the input for `rsjson_process_merges.py`) and `merged_filtered.ERROR.json`(dbsnp merged records that ran into any issues during parsing)

Each row of output file contains a variant JSON object with keys: RS id, chromosome, position, type (snv, delins, etc), and function (annotation). Record will be duplicated for each of the variant's merged RS ids - meaning, another record will be created with all the same fields except the RS id key (which will be the merged variant's RS id). This file can be imported into MongoDB via mongoimport.

### Recommended: Running script in parallel with HPC cluster (i.e. NIH's BIOWULF)

Clone this repo into your data directory on the Biowulf cluster /data/your_username. 

`cd nci-webtools-dceg-linkage/scripts/dbSNP update/hpc`

`sh run-swarm-parse-dbsnp-json.sh <INPUT_DIR> <OUTPUT_DIR>`

This script will use Biowulf to parse all NCBI dbsnp .json.bz2 files in `<INPUT_DIR>`. Once completed, parsed .json files will appear in `<OUTPUT_DIR>` and proceed to Step #2 to import them into MongoDB.

Note: this process can take up to 22 hours to complete (largest chromosome data file)

## Step 2: Import parsed chromosome .json files to MongoDB and index collection.

Use mongoimport to import all `chr_#|X|Y_filtered.json` files into the Mongo dbsnp build:

`mongoimport --db LDLink --collection dbsnp --file chr_#_filtered.json`

Do NOT import `merged_filtered.json` into the MongoDB dbsnp collection or any `*.ERROR.json` files.

Use this script to import ALL files in a folder into a MongoDB collection:

Be sure to move `merged_filtered.json` and all `*.ERROR.json` files outside the folder before running it.

`for filename in *; do mongoimport --db dbsnp --collection LDLink --file $filename; done`

Create indexes on the collection to significantly speed up queries. Execute command:

`nohup mongo --eval "db.dbsnp.createIndexes([{id: 1}, {chromosome: 1, position_grch37: 1}, {chromosome: 1, position_grch38: 1}])" LDLink &`

This process may take several hours to complete. Consider using `nohup` and `&` to run task continuously in background.

## Step 3: Process merged variants file `merged_filtered.json`.

Includes script `rsjson_process_merges.py` which looks up each merged RSID found in `merged_filtered.json` in MongoDB dbsnp to prevent duplicate insertions. If the record does not already exists, it will query the reference RS id's merged RS id and create a record with the data. The newly created merged RSID records will be in a new file called `merged_filtered_complete.json`.

- `rsjson_process_merges.py` outputs .json file `merged_filtered_complete.json`

`python3 rsjson_process_merges.py merged_filtered.json`

Each row of output file `merged_filtered_complete.json` contains a variant JSON object with keys: RS id, chromosome, position_grch37, position_grch38, type (snv, delins, etc), and function (annotation). This file can be imported into MongoDB via mongoimport.

`nohup mongoimport --db LDLink --collection dbsnp --file merged_filtered_complete.json &`

This process may take several hours to complete. Consider using `nohup` and `&` to run task continuously in background. Also consider dropped all indexes before runnning `mongoimport` and then rebuilding all indexes again after import is complete.

## Step 4: Dump dbsnp MongoDB collection and restore elsewhere.

To dump:
`nohup mongodump --verbose --db LDLink --collection dbsnp --gzip --out ./dump_dbsnp &`

To restore data:
`nohup mongorestore --verbose --numInsertionWorkersPerCollection 12 --noIndexRestore --db LDLink ./dump_dbsnp/LDLink/ --gzip &`

To restore indexes:
`nohup mongo --eval "db.dbsnp.createIndexes([{id: 1}, {chromosome: 1, position_grch37: 1}, {chromosome: 1, position_grch38: 1}])" LDLink &`

This process may take several hours. Consider using `nohup` and `&` to run task continuously in background.
