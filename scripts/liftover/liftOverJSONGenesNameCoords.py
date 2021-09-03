# this script is written to use the liftOver program to convert LDassoc's genes_name_coords MongoDB collection with GRCh37 positions to GRCh38
# and create a MongoDB-importable JSON file with both GRCh37 and GRCh38 positions
# http://genome.ucsc.edu/goldenPath/help/hgTracksHelp.html#Liftover
# input: use "mongoexport" to export existing "genes_name_coords" MongoDB collection to .json outfile and use as input for this script
# requirement: you must download liftOver precompiled executable binary and place in PATH before running script
# requirement: you must download and install tabix in local PATH before running script
# requirement: you must download desired liftOver chain file from https://hgdownload.cse.ucsc.edu/goldenpath/hg19/liftOver/

import time
import sys
import json
import datetime
import subprocess

currentDT = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
start_time = time.time()  # measure script's run time

def generateInputBed(inputJSONFile):
    print("Generating input BED file...")
    inputBedFileName = "input." + currentDT + ".bed"
    with open(inputBedFileName, 'a') as bedfile:
        with open(inputJSONFile) as inputfile:
            for line in inputfile:
                jsonObj = json.loads(line)
                if isinstance(jsonObj['position_grch37'], int):
                    writeLine = ["chr" + jsonObj['chromosome'], str(jsonObj['begin']), str(jsonObj['end']), json.dumps(jsonObj, separators=(',', ':')).replace(" ", "__")]
                    bedfile.write("\t".join(writeLine) + '\n')
    print("liftOver input file " + inputBedFileName + " generated...")
    return inputBedFileName

def runLiftOver(inputBedFileName, chainFile):
    print("Running liftOver...")
    outputBedFileName = "output." + currentDT + ".bed"
    outputUnmappedBedFileName = "output.unMapped." + currentDT + ".bed"
    # usage: liftOver oldFile map.chain newFile unMapped
    process = subprocess.Popen(['liftOver', inputBedFileName, chainFile, outputBedFileName, outputUnmappedBedFileName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode('utf-8'), stderr.decode('utf-8'))
    print("liftOver output " + outputBedFileName + " generated...")
    print("liftOver unmapped output " + outputUnmappedBedFileName + " generated...")
    return outputBedFileName, outputUnmappedBedFileName

# CAPTURE START POS

def generateJSONFile(outputBedFileName, outputUnmappedBedFileName, outputJSONFile):
    print("Generating JSON file...")
    with open(outputJSONFile, 'a') as jf:
        with open(outputBedFileName) as bf:
            for line in bf:
                split_line = line.strip().split()
                genes_name_coords_obj = json.loads(split_line[3].replace("__", " "))
                # drop any rows with chr#_*
                if len(split_line[0].split("_")) <= 1:
                    writeJSONMapped = {
                        "chromosome_grch37": genes_name_coords_obj['chromosome'],
                        "begin_grch37": int(genes_name_coords_obj['begin']),
                        "end_grch37": int(genes_name_coords_obj['end']),
                        "chromosome_grch38": split_line[0].lstrip('chr'),
                        "begin_grch38": int(split_line[1]),
                        "end_grch38": int(split_line[2]),
                        "name": genes_name_coords_obj['name']
                    }
                    jf.write(json.dumps(writeJSONMapped) + "\n")
                else:
                    writeJSONMapped = {
                        "chromosome_grch37": genes_name_coords_obj['chromosome'],
                        "begin_grch37": int(genes_name_coords_obj['begin']),
                        "end_grch37": int(genes_name_coords_obj['end']),
                        "chromosome_grch38": split_line[0].lstrip('chr'),
                        "begin_grch38": "NA",
                        "end_grch38": "NA",
                        "name": genes_name_coords_obj['name']
                    }
                    jf.write(json.dumps(writeJSONMapped) + "\n")
        with open(outputUnmappedBedFileName) as bf:
            for line in bf:
                split_line = line.strip().split()
                if "#" not in split_line[0]:
                    genes_name_coords_obj = json.loads(split_line[3].replace("__", " "))
                    writeJSONUnmapped = {
                        "chromosome_grch37": genes_name_coords_obj['chromosome'],
                        "begin_grch37": int(genes_name_coords_obj['begin']),
                        "end_grch37": int(genes_name_coords_obj['end']),
                        "chromosome_grch38": split_line[0].lstrip('chr'),
                        "begin_grch38": "NA",
                        "end_grch38": "NA",
                        "name": genes_name_coords_obj['name']
                    }
                    jf.write(json.dumps(writeJSONUnmapped) + "\n")

def main():
    print("Starting liftOver script for LDassoc 'genes_name_coords' JSON...")
    try:
        inputJSONFile = sys.argv[1]
        chainFile = sys.argv[2]
        outputJSONFile = sys.argv[3]
    except:
        print("USAGE: python3 liftOverJSONGenesNameCoords.py <INPUT_JSON_DATA> <CHAIN_FILE> <OUTPUT_JSON_FILENAME_W_EXTENSION>")
        print("EXAMPLE: python3 liftOverJSONGenesNameCoords.py ./export_genes_name_coords.json ./hg19ToHg38.over.chain.gz new_genes_name_coords.json")
        sys.exit(1)

    inputBedFileName = generateInputBed(inputJSONFile)
    outputBedFileName, outputUnmappedBedFileName = runLiftOver(inputBedFileName, chainFile)
    generateJSONFile(outputBedFileName, outputUnmappedBedFileName, outputJSONFile)

    print("LiftOver completed [" + str(time.time() - start_time) + " seconds elapsed]...")

    
if __name__ == "__main__":
    main()