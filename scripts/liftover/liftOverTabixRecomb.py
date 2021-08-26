# this script is written to use the liftOver program to convert LDlink MongoDB collections with GRCh37 positions to GRCh38
# http://genome.ucsc.edu/goldenPath/help/hgTracksHelp.html#Liftover
# requirement: you must download liftOver precompiled executable binary and place in PATH before running script
# requirement: you must download and install tabix in local PATH before running script
# requirement: you must download desired liftOver chain file from https://hgdownload.cse.ucsc.edu/goldenpath/hg19/liftOver/

import time
from pymongo import MongoClient
from bson import json_util, ObjectId
import sys
import gzip
import datetime
import subprocess

currentDT = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
start_time = time.time()  # measure script's run time

def generateInputBed(inputTabixFile):
    with gzip.open(inputTabixFile) as gf:
        lines = gf.read().splitlines() 
    # print("lines", lines)
    inputBedFileName = "input." + currentDT + ".bed"
    headers = lines[0].decode('utf-8').split()
    # print("headers", headers)
    with open(inputBedFileName, 'a') as bf:
        # skip header
        for line in lines[1:]:
            fields = line.decode('utf-8').split()
            writeLine = ["chr" + fields[0], fields[1], str(int(fields[1]) + 1), fields[2]]
            # print(writeLine)
            bf.write("\t".join(writeLine) + '\n')
    print("liftOver input file " + inputBedFileName + " generated...")
    return inputBedFileName, headers

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

def generateTabixFile(headers, outputBedFileName, outputTabixFile):
    print("Generating Tabix file...")
    with open(outputBedFileName) as bf:
        lines = bf.read().splitlines() 
    splitLines = list(map(lambda x: x.split("\t"), lines[1:]))
    # print(splitLines)
    print("Sorting lines...")
    splitLines.sort(key = lambda x: (int(x[0].lstrip('chr').split("_")[0]) if x[0].lstrip('chr').split("_")[0] not in ['X', 'Y'] else x[0].lstrip('chr').split("_")[0], int(x[1])))
    with open(outputTabixFile + ".txt", 'a') as tf:
        tf.write("\t".join(headers) + '\n')
        for line in splitLines:
            # drop any rows with chr#_*
            if len(line[0].split("_")) <= 1:
                writeLine = [line[0].lstrip('chr'), line[1], line[3]]
                # print(writeLine)
                tf.write("\t".join(writeLine) + '\n')
    # bgzip file for tabix
    process = subprocess.Popen(['bgzip', outputTabixFile + ".txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode('utf-8'), stderr.decode('utf-8'))
    print("Generated Tabix data file " + outputTabixFile + "...")
    generateTabixIndex(outputTabixFile)

def generateTabixIndex(outputTabixFile):
    # tabix genetic_map_autosomes_combined_b38.txt.gz -b 2 -e 2 -f -S 1 -0
    print("Generating Tabix index file...")
    process = subprocess.Popen(['tabix', outputTabixFile + ".txt.gz", '-b 2', '-e 2', '-0', '-S 1', '-f'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode('utf-8'), stderr.decode('utf-8'))
    print("Finished generating Tabix index file...")

def main():
    print("Starting liftOver script...")
    try:
        inputTabixFile = sys.argv[1]
        chainFile = sys.argv[2]
        outputTabixFile = sys.argv[3]
    except:
        print("USAGE: python3 liftOverTabix.py <INPUT_TABIX_FILE> <CHAIN_FILE> <OUTPUT_TABIX_FILE_NAME>")
        print("EXAMPLE: python3 liftOverTabix.py ./genetic_map_autosomes_combined_b37.txt.gz ./hg19ToHg38.over.chain.gz genetic_map_autosomes_combined_b38")
        sys.exit(1)

    inputBedFileName, headers = generateInputBed(inputTabixFile)
    outputBedFileName, outputUnmappedBedFileName = runLiftOver(inputBedFileName, chainFile)
    generateTabixFile(headers, outputBedFileName, outputTabixFile)

    print("LiftOver completed [" + str(time.time() - start_time) + " seconds elapsed]...")

    
if __name__ == "__main__":
    main()