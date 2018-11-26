# dbsnp
For constructing dbSNP build (151). Can be modified for future dbSNP updates.

Built off Lon Phan's `rsjson_test.py` (lonphan@ncbi.nlm.nih.gov)

Includes script `rsjson_dbsnp.py` to parse gzipped JSON files and create SQLite database indexed by (RS)ID.

- Outputs SQLITE database: `dbsnp.rs.151.db`

Includes script `chrjson_dbsnp.py` to parse gzipped JSON files and create SQLITE database indexed by CHROMOSOME. 

- Outputs SQLITE database: `dbsnp.chr.151.db`
  
Each row contains the attributes: id, chromosome, position, and function. Data will be duplicated for each of the rsid's associated merged-rsids. 

## Running script

Create folder named `json_refsnp` in script's directory and place all compressed json `json.gz` files in folder. There should be one file for each chromosome (1-22, X & Y - 24 in total).

Current refsnp data files are pulled from here: ftp://ftp.ncbi.nlm.nih.gov/snp/.redesign/latest_release/JSON

Run `python rsjson_dbSNP.py` to execute the script to build SQLite database indexed by RS number.

Run `python chrjson_dbSNP.py` to execute the script to build SQLite database indexed by chromosome.

** To ensure success, make sure scripts are ran in stable environment. Could take up to 5 days to complete. **

** To prevent corrupted `.json.gz` files (failed CRC-checksum), it is recommented to `curl` or `wget` directly from ftp server when downloading data files **