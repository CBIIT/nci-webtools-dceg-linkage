#!/bin/bash

# SWARM file
SWARM_FILE="parse-dbsnp-json.swarm"

# ARGUMENT 1: Input data directory path
# INPUT_DIR="/path/to/input_dir"
if [ -z "$1" ]
    then
        echo "ERROR: No input data path supplied..."
        echo "USAGE: sh run-swarm-parse-dbsnp-json.sh <INPUT_DIR> <OUTPUT_DIR>"
        echo "EXAMPLE: sh run-swarm-parse-dbsnp-json.sh /path/to/input_dir /path/to/output_dir"
        exit 1
fi
INPUT_DIR=$1

# ARGUMENT 2: Output parsed json directory path
# OUTPUT_DIR="/path/to/output_dir"
if [ -z "$2" ]
    then
        echo "ERROR: No output results path supplied..."
        echo "USAGE: sh run-swarm-parse-dbsnp-json.sh <INPUT_DIR> <OUTPUT_DIR>"
        echo "EXAMPLE: sh run-swarm-parse-dbsnp-json.sh /path/to/input_dir /path/to/output_dir"
        exit 1
fi
OUTPUT_DIR=$2

CURRENT_DATE=$(date +%F_%H:%M:%S)

mkdir ./swarm_parse_dbsnp_out_$CURRENT_DATE

# Log path
LOG_PATH="./swarm_parse_dbsnp_out_$CURRENT_DATE/"

# Parse script path
PARSE_SCRIPT="../rsjson_parse_data_mongo.py"

# Tmp lscratch path
TMP_PATH="/lscratch/\$SLURM_JOB_ID"

# Delete existing SWARM file if exists
if [ -e $SWARM_FILE ] 
then 
    echo "Delete existing SWARM file..."
    rm $SWARM_FILE
else
    echo "Creating new SWARM file..."
fi

# Generate SWARM file
echo "Generating SWARM script..."
for FILE in $INPUT_DIR/*
do
    # echo $FILE
    FILE_BASENAME=$(basename $FILE)
    # echo $FILE_BASENAME
    if [[ $FILE_BASENAME =~ ^refsnp-chr[1-9|X|Y]+\.json\.bz2$ ]]
    then
        echo "Found file: $FILE"
        echo "python3 ${PARSE_SCRIPT} ${FILE} ${OUTPUT_DIR} ${TMP_PATH}"
        echo "python3 ${PARSE_SCRIPT} ${FILE} ${OUTPUT_DIR} ${TMP_PATH}" >> $SWARM_FILE
        echo ""
    fi
done

[ -d $OUTPUT_DIR ] && echo "$OUTPUT_DIR directory already exists" || mkdir $OUTPUT_DIR

# Run generated SWARM file
# -f <filename> = specify .swarm file
# -t <#> = number of threads for each process subjob
# -g <#> = number of gb for each process subjob
# --verbose <0-6> = choose verbose level, 6 being the most chatty
# --gres=lscratch:<#> = number of gb of tmp space for each process subjob
# swarm -f $SWARM_FILE -t 8 -g 64 --time 48:00:00 --verbose 6 --gres=lscratch:300 --logdir $LOG_PATH --module mysql/8.0,nodejs --merge-output
swarm -f $SWARM_FILE -t 2 -g 16 --time 48:00:00 --verbose 6 --gres=lscratch:200 --logdir $LOG_PATH --merge-output