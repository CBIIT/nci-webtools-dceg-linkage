# this script is written to use the liftOver program to convert the recombination rate data with GRCh37 positions to GRCh38
# and create a MongoDB-importable JSON file with both GRCh37 and GRCh38 positions
# recombination rate data can be downloaded here https://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3.html
# http://genome.ucsc.edu/goldenPath/help/hgTracksHelp.html#Liftover
# requirement: you must download liftOver precompiled executable binary and place in PATH before running script
# requirement: you must download and install tabix in local PATH before running script
# requirement: you must download desired liftOver chain file from https://hgdownload.cse.ucsc.edu/goldenpath/hg19/liftOver/
# requirement: this script will only look at files in a directory named genetic_map_chr*_combined_b37.txt. combine all genetic_map_chrX* files into one. (cat genetic_map_chrX_nonPAR_combined_b37.txt genetic_map_chrX_PAR1_combined_b37.txt genetic_map_chrX_PAR2_combined_b37.txt | sort > genetic_map_chrX_combined_b37.txt)

import time
import sys
import json
import datetime
import subprocess
import os

currentDT = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
start_time = time.time()  # measure script's run time

def generateInputBed(inputDir):
    inputBedFileName = "input." + currentDT + ".bed"
    with open(inputBedFileName, 'a') as bf:
        for inputFile in os.scandir(inputDir):
            print(inputFile.path)
            chromosome = inputFile.name.split("_")[2].strip('chr')
            with open(inputFile.path) as gf:
                lines = gf.read().splitlines() 
            # print("lines", lines)
            headers = lines[0]
            # .decode('utf-8').split()
            # print("headers", headers)
            # skip header
            for line in lines[1:]:
                fields = line.split()
                if fields[0] != "position":
                    # print(fields)
                    writeLine = ["chr" + chromosome, fields[0], str(int(fields[0]) + 1), "__".join([chromosome, fields[0], fields[1]])]
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

# CAPTURE START POS

def generateJSONFile(outputBedFileName, outputUnmappedBedFileName, outputJSONFile):
    print("Generating JSON file...")
    with open(outputBedFileName) as bf:
        linesMapped = bf.read().splitlines() 
    splitLinesMapped = list(map(lambda x: x.split("\t"), linesMapped))
    with open(outputUnmappedBedFileName) as bf:
        linesUnmapped = bf.read().splitlines() 
    splitLinesUnmapped = list(map(lambda x: x.split("\t"), linesUnmapped))
    with open(outputJSONFile, 'a') as jf:
        for line in splitLinesMapped:
            # drop any rows with chr#_*
            if len(line[0].split("_")) <= 1:
                writeJSONMapped = {
                    "rate": line[3].split("__")[2],
                    "chromosome_grch37": line[3].split("__")[0],
                    "position_grch37": int(line[3].split("__")[1]),
                    "chromosome_grch38": line[0].strip('chr'),
                    "position_grch38": int(line[1])
                }
                jf.write(json.dumps(writeJSONMapped) + "\n")
            else:
                writeJSONMapped = {
                    "rate": line[3].split("__")[2],
                    "chromosome_grch37": line[3].split("__")[0],
                    "position_grch37": int(line[3].split("__")[1]),
                    "chromosome_grch38": "NA",
                    "position_grch38": "NA"
                }
                jf.write(json.dumps(writeJSONMapped) + "\n")
        for line in splitLinesUnmapped:
            if "#" not in line[0]:
                writeJSONUnmapped = {
                    "rate": line[3].split("__")[2],
                    "chromosome_grch37": line[3].split("__")[0],
                    "position_grch37": int(line[3].split("__")[1]),
                    "chromosome_grch38": "NA",
                    "position_grch38": "NA"
                }
                jf.write(json.dumps(writeJSONUnmapped) + "\n")

def main():
    print("Starting liftOver script for recombination rates...")
    try:
        inputDir = sys.argv[1]
        chainFile = sys.argv[2]
        outputJSONFile = sys.argv[3]
    except:
        print("USAGE: python3 liftOverJSONRegulome.py <INPUT_REGULOME_DATA> <CHAIN_FILE> <OUTPUT_JSON_FILENAME_W_EXTENSION>")
        print("EXAMPLE: python3 liftOverJSONRegulome.py ./ENCFF297XMQ.tsv ./hg19ToHg38.over.chain.gz regulome.json")
        sys.exit(1)

    inputBedFileName, headers = generateInputBed(inputDir)
    outputBedFileName, outputUnmappedBedFileName = runLiftOver(inputBedFileName, chainFile)
    generateJSONFile(outputBedFileName, outputUnmappedBedFileName, outputJSONFile)

    print("LiftOver completed [" + str(time.time() - start_time) + " seconds elapsed]...")

    
if __name__ == "__main__":
    main()