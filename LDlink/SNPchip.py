#!/usr/bin/env python3

###########
# SNPchip #
###########

import yaml

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
import os
import bson.regex
import operator
import os
import json
import sys
from LDcommon import genome_build_vars,connectMongoDBReadOnly,validsnp,replace_coords_rsid_list,get_coords


def get_platform_request(web):

    try:
        db = connectMongoDBReadOnly(True)       
    except ConnectionFailure:
        print("MongoDB is down")
        print("syntax: mongod --dbpath /local/content/analysistools/public_html/apps/LDlink/data/mongo/data/db/ --auth")
        return "Failed to connect to server."

    cursor = db.platforms.find(
        {"platform": {'$regex': '.*'}}).sort("platform", -1)
    platforms = {}
    for document in cursor:
        platforms[document["code"]] = document["platform"]
    json_output = json.dumps(platforms, sort_keys=True, indent=2)
    return json_output


# Create SNPchip function
def convert_codeToPlatforms(platform_query, web):
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    tmp_dir = config['data']['tmp_dir']

    platforms = []
    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(True)
    code_array = platform_query.split('+')
    cursor = db.platforms.find({"code": {'$in': code_array}})
    for document in cursor:
        platforms.append(document["platform"])
    # print(platforms)
    return platforms


def calculate_chip(snplst, platform_query, web, request, genome_build):

    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    tmp_dir = config['data']['tmp_dir']
    dbsnp_version = config['data']['dbsnp_version']


    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    out_json = open(tmp_dir+'proxy'+request+".json", "w")
    output = {}

    snps = validsnp(snplst,genome_build,5000)
    #if return value is string, then it is error message and need to return the message
    if isinstance(snps, str):
        return snps
        
    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(True)
    snps = replace_coords_rsid_list(db, snps,genome_build,output)

    # Find RS numbers in snp database
    rs_nums = []
    snp_pos = []
    snp_coords = []
    warn = []
    tabix_coords = ""
    for snp_i in snps:
        if len(snp_i) > 0:
            if len(snp_i[0]) > 2:
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                    snp_coord = get_coords(db, snp_i[0])
                    if snp_coord != None and snp_coord[genome_build_vars[genome_build]['position']] != "NA":
                        if snp_coord['chromosome'] == "X":
                            chr = 23
                        elif snp_coord['chromosome'] == "Y":
                            chr = 24
                        else:
                            chr = int(snp_coord['chromosome'])
                        rs_nums.append(snp_i[0])
                        snp_pos.append(snp_coord[genome_build_vars[genome_build]['position']])
                        temp = [snp_i[0], chr, int(snp_coord[genome_build_vars[genome_build]['position']])]
                        snp_coords.append(temp)
                    else:
                        warn.append(snp_i[0])
                else:
                    warn.append(snp_i[0])
            else:
                warn.append(snp_i[0])

    output["warning"] = ""
    output["error"] = ""
    if warn != [] and len(rs_nums) != 0:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
        else:
            output["warning"] = "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
    elif len(rs_nums) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers or coordinates. " + output["warning"]
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        createOutputFile(request, genome_build)
        return json_output

    # Sort by chromosome and then position
    snp_coords_sort = sorted(snp_coords, key=operator.itemgetter(1, 2))

    # Convert chromosome 23 and 24 back to X and Y
    for i in range(len(snp_coords_sort)):
        if snp_coords_sort[i][1] == 23:
            snp_coords_sort[i][1] = "X"
        elif snp_coords_sort[i][1] == 24:
            snp_coords_sort[i][1] = "Y"
        else:
            snp_coords_sort[i][1] = str(snp_coords_sort[i][1])

    platformcount = 0
    count = 0
    platform_NOT = []
    if platform_query != "":  # <--If user did not enter platforms as a request
        platform_list = convert_codeToPlatforms(platform_query, web)
    # Quering MongoDB to get platforms for position/chromsome pairs
    else:
        platform_list = []

    print("platform_list", platform_list)

    for k in range(len(snp_coords_sort)):
        platforms = []
        position = str(snp_coords_sort[k][2])
        Chr = str(snp_coords_sort[k][1])
        cursor = ()
        platform = ""
        count = count+1
        cursor = db.snp_col.find({genome_build_vars[genome_build]['chromosome']: str(Chr), genome_build_vars[genome_build]['position']: int(position)})

        for document in cursor:
            for z in range(0, len(document["data"])):
                if((document["data"][z]["platform"] in platform_list or document["data"][z]["platform"].rstrip(' Array') in platform_list) and platform_query != ""):
                    platforms.append(document["data"][z]["platform"])
                elif(platform_query == ""):
                    platforms.append(document["data"][z]["platform"])
        if(platforms == []):
            rs = snp_coords_sort[k][0]
            platform_NOT.append(rs)
        output[str(k)] = [str(snp_coords_sort[k][0]), snp_coords_sort[k]
                          [1]+":"+str(snp_coords_sort[k][2]), ','.join(platforms)]
    if(platform_NOT != [] and len(platform_NOT) != count):
        warning = output["warning"]
        warning = warning+"The following RS number did not have any platforms found: " + \
            ", ".join(platform_NOT)+". "
        output["warning"] = warning
    elif (len(platform_NOT) == count):
        error = output["warning"]
        error = error+"Entries from the input variant list were not found in any of the selected arrays. "
        output["warning"] = error
    # Output JSON file
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()
    createOutputFile(request, genome_build)

    return json_output


def createOutputFile(request, genome_build):
    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    tmp_dir = config['data']['tmp_dir']

    details_file = open(tmp_dir+'details'+request+".txt", "w")

    with open(tmp_dir + "proxy"+request+".json") as out_json:
        json_dict = json.load(out_json)

    rs_dict = dict(json_dict)
    del rs_dict['error']
    del rs_dict['warning']

    # Header
    header = ["RS Number", "Position (" + genome_build_vars[genome_build]['title'] + ")", "Arrays"]
    print("\t".join(header), file=details_file)

    # Body
    for i in range(0, len(rs_dict)):
        print("\t".join(rs_dict[str(i)]), file=details_file)

    # Footer
    try:
        json_dict["warning"]
    except KeyError:
        print("", file=details_file)
    else:
        print(json_dict["warning"])
        if(json_dict["warning"] != ""):
            print("", file=details_file)
            print("WARNING: "+json_dict["warning"], file=details_file)
            print("", file=details_file)
            print("")
            print("WARNING: "+json_dict["warning"])

    try:
        json_dict["error"]
    except KeyError:
        print("", file=details_file)
    else:
        print(json_dict["error"])
        if (json_dict["error"] != ""):
            print("", file=details_file)
            print("ERROR: "+json_dict["error"], file=details_file)
            print("", file=details_file)
            print("")
            print("ERROR: "+json_dict["error"])

    details_file.close()


def main():

    # Import SNPchip options
    if len(sys.argv) == 4:
        web = sys.argv[1]
        snplst = sys.argv[2]
        platform_query = sys.argv[3]
        request = sys.argv[4]
        genome_build = sys.argv[5]
    else:
        print("Correct useage is: SNPchip.py false snplst platforms request, enter \"\" for platform_query if empty otherwise seperate each platform by a \"+\"")
        sys.exit()

    # Run function
    calculate_chip(snplst, platform_query, web, request, genome_build)


if __name__ == "__main__":
    main()
