# this script is written to use the liftOver program to convert LDlink MongoDB collections with GRCh37 positions to GRCh38
# http://genome.ucsc.edu/goldenPath/help/hgTracksHelp.html#Liftover
# requirement: you must download liftOver precompiled executable binary and place in PATH before running script

import time
from pymongo import MongoClient
from bson import json_util, ObjectId
start_time = time.time()  # measure script's run time

def generateInputBed():
    return []

def runLiftOver():
    # usage: liftOver oldFile map.chain newFile unMapped
    return []

def main():
    print("Starting liftOver script...")

    print("LiftOver completed [" + str(time.time() - start_time) + " seconds elapsed]...")

    
if __name__ == "__main__":
    main()