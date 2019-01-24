# dbsnp-mongodb
Script to filter dbsnp records provided by NCBI and create files that can be imported to a MongoDB collection.

Built off Lon Phan's `rsjson_test.py` (lonphan@ncbi.nlm.nih.gov)

Includes script `rsjson_mongo_filter.py` to parse dbsnp .json.gz files and creates .json files that can be imported into MongoDB collection(s).

- Outputs .json file(s): `chr_#_filtered.json`
  
Each row of output file contains a variant JSON object with keys: RS id, chromosome, position, type (snv, delins, etc), and function (annotation). Record will be duplicated for each of the variant's merged RS ids - meaning, another record will be created with all the same fields except the RS id key (which will be the merged variant's RS id).

## Running script

Clone this repo into your data directory on the Biowulf cluster /data/your_username. 

Create folder named `json_refsnp` in the repo's directory and place all compressed json `json.gz` files in folder.

Run `./rsjson_run.sh` to queue 24 jobs to process the 24 compressed chromosome .json.gz files.