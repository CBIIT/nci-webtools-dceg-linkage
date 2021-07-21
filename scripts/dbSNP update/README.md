# dbsnp-mongodb
Scripts to filter dbsnp records provided by NCBI and create files that can be imported to a MongoDB collection. NCBI dbsnp records are located here: ftp://ftp.ncbi.nlm.nih.gov/snp/.redesign/

Last updated JULY 2021 for dbSNP b155 import. Built off Lon Phan's `rsjson_test.py` (lonphan@ncbi.nlm.nih.gov)

## Download dbSNP (latest build) raw data files from NCBI

Download all data from ftp `ftp://ftp.ncbi.nih.gov/snp/latest_release/JSON/`.

Run `md5sum -c CHECKSUMS` to verify data integrity. Re-download any files that fail the check.

## Step 1: Parse raw dbsnp chromosome files 1 - 22, X, Y, and "merged".

Includes script `rsjson_parse_data_mongo.py` to parse dbsnp .json.bz2 files and creates .json files that can be imported into a MongoDB collection. Also finds merged variants from `refsnp-merged.json.bz2` and parses that file for extra merged variants. Further processing is required after chr1-22,X and Y .json files are imported to MongoDB to include these 'extra' merged variants.

- Inputs: `/path/to/refsnp-<chr1-22,chrX,chrY,merged>.json.bz2`(required) `/path/to/output_directory`(required) `/path/to/tmp_directory`(optional)
- Output for `refsnp-<chr1-22,chrX,chrY>.json.bz2`: `chr_#_filtered.json`(parsed data ready to be imported into mongo collection) and `chr_#_filtered.ERROR.json`(dbsnp records that ran into any issues during parsing)
- Output for `refsnp-merged.json.bz2`: `merged_filtered.json`(parsed merged variants data that is used as the input for `rsjson_find_merges.py`) and `merged_filtered.ERROR.json`(dbsnp merged records that ran into any issues during parsing)

Each row of output file contains a variant JSON object with keys: RS id, chromosome, position, type (snv, delins, etc), and function (annotation). Record will be duplicated for each of the variant's merged RS ids - meaning, another record will be created with all the same fields except the RS id key (which will be the merged variant's RS id). This file can be imported into MongoDB via mongoimport.

### Recommended: Running script in parallel with HPC cluster (i.e. NIH's BIOWULF)

Clone this repo into your data directory on the Biowulf cluster /data/your_username. 

## Step 2: Import chromosome variants and index collection.

Use mongoimport to import `processed_merges.json` into the Mongo dbsnp build:

`mongoimport --db LDLink --collection dbsnp --file chr_#_filtered.json`

Use this script to import ALL files in a folder into a MongoDB collection:

`for filename in *; do mongoimport --db dbsnp --collection LDLink --file $filename; done`

Create indexes on the collection to significantly speed up queries. Execute command:

`nohup mongo --eval "db.dbsnp.createIndexes([{id: 1}, {chromosome: 1, position_grch37: 1}, {chromosome: 1, position_grch38: 1}])" LDLink &`

This process may take a long time. Consider using `nohup` and `&` to run task continuously in background.

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


