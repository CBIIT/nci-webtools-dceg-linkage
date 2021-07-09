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

# CURRENT_DATE=$(date +%F_%H:%M:%S)

# mkdir ./swarm_export_out_$CURRENT_DATE

# Log path
# LOG_PATH="./swarm_export_out_$CURRENT_DATE/"

# Export script path
# EXPORT_SCRIPT="../rsjson_mongo_filter.py"

# Delete existing SWARM file if exists
# if [ -e $SWARM_FILE ] 
# then 
#     echo "Delete existing SWARM file..."
#     rm $SWARM_FILE
# else
#     echo "Creating new SWARM file..."
# fi

# Generate SWARM file
echo "Generating SWARM script..."
for FILE in $INPUT_DIR/*
do
    if [[ "{$FILE}" =~ "^refsnp-chr[\d]*[X|Y]*\.json\.bz2$" ]]
    then
        echo "Found file: $FILE"
        # echo "echo 'Creating MySQL instance...' ; local_mysql create --port $PORT ; echo 'Created MySQL instance.' ; echo 'Configuring MySQL instance...' ; cp mysql-lscratch.config  /lscratch/\$SLURM_JOB_ID/mysql/my.cnf ; sed -i 's/<PORT>/$PORT/g' /lscratch/\$SLURM_JOB_ID/mysql/my.cnf ; sed -i \"s/<SLURM_JOB_ID>/\$SLURM_JOB_ID/g\" /lscratch/\$SLURM_JOB_ID/mysql/my.cnf ; echo 'Configured MySQL instance.' ; echo 'Starting MySQL instance...' ; local_mysql start --port $PORT ; echo 'Started MySQL instance.' ; echo 'Creating MySQL user...' ; mysql -u root -p$PASSWORD --socket=$TMP_DIR/mysql.sock --execute=\"CREATE USER '$USER'@'localhost' IDENTIFIED BY '$PASSWORD'; GRANT ALL PRIVILEGES ON *.* TO '$USER'@'localhost' WITH GRANT OPTION; CREATE USER '$USER'@'%' IDENTIFIED BY '$PASSWORD';GRANT ALL PRIVILEGES ON *.* TO '$USER'@'%' WITH GRANT OPTION; CREATE DATABASE plcogwas CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;\" ; echo 'Created MySQL user.' ; node $EXPORT_SCRIPT --port $PORT --user $USER --password $PASSWORD --file $FILE --phenotype_file $PHENOTYPE_FILE --output $OUTPUT_DIR --logdir $LOG_PATH --tmp $TMP_DIR ; echo 'Stopping MySQL instance...' ; local_mysql stop --port $PORT ; echo 'Stopped MySQL instance.' ;"
        # echo "echo 'Creating MySQL instance...' ; local_mysql create --port $PORT ; echo 'Created MySQL instance.' ; echo 'Configuring MySQL instance...' ; cp mysql-lscratch.config  /lscratch/\$SLURM_JOB_ID/mysql/my.cnf ; sed -i 's/<PORT>/$PORT/g' /lscratch/\$SLURM_JOB_ID/mysql/my.cnf ; sed -i \"s/<SLURM_JOB_ID>/\$SLURM_JOB_ID/g\" /lscratch/\$SLURM_JOB_ID/mysql/my.cnf ; echo 'Configured MySQL instance.' ; echo 'Starting MySQL instance...' ; local_mysql start --port $PORT ; echo 'Started MySQL instance.' ; echo 'Creating MySQL user...' ; mysql -u root -p$PASSWORD --socket=$TMP_DIR/mysql.sock --execute=\"CREATE USER '$USER'@'localhost' IDENTIFIED BY '$PASSWORD'; GRANT ALL PRIVILEGES ON *.* TO '$USER'@'localhost' WITH GRANT OPTION; CREATE USER '$USER'@'%' IDENTIFIED BY '$PASSWORD';GRANT ALL PRIVILEGES ON *.* TO '$USER'@'%' WITH GRANT OPTION; CREATE DATABASE plcogwas CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;\" ; echo 'Created MySQL user.' ; node $EXPORT_SCRIPT --port $PORT --user $USER --password $PASSWORD --file $FILE --phenotype_file $PHENOTYPE_FILE --output $OUTPUT_DIR --logdir $LOG_PATH --tmp $TMP_DIR ; echo 'Stopping MySQL instance...' ; local_mysql stop --port $PORT ; echo 'Stopped MySQL instance.' ;" >> $SWARM_FILE
        echo ""
    fi
done

# [ -d $OUTPUT_DIR ] && echo "$OUTPUT_DIR directory already exists" || mkdir $OUTPUT_DIR

# Run generated SWARM file
# -f <filename> = specify .swarm file
# -t <#> = number of threads for each process subjob
# -g <#> = number of gb for each process subjob
# --verbose <0-6> = choose verbose level, 6 being the most chatty
# --gres=lscratch:<#> = number of gb of tmp space for each process subjob
# swarm -f $SWARM_FILE -t 8 -g 64 --time 48:00:00 --verbose 6 --gres=lscratch:300 --logdir $LOG_PATH --module mysql/8.0,nodejs --merge-output
# swarm -f $SWARM_FILE -t 4 -g 32 --time 48:00:00 --verbose 6 --gres=lscratch:300 --logdir $LOG_PATH --module mysql/5.7.22,nodejs --merge-output