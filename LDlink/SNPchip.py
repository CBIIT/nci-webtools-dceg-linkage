#!/usr/bin/env python

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
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = contents[0].split('=')[1]
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])


def get_platform_request(web):

    try:
        # Connect to Mongo snp database
        if web:
            client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
        else:
            client = MongoClient('localhost', port)
    except ConnectionFailure:
        print "MongoDB is down"
        print "syntax: mongod --dbpath /local/content/analysistools/public_html/apps/LDlink/data/mongo/data/db/ --auth"
        return "Failed to connect to server."

    db = client["LDLink"]
    cursor = db.platforms.find(
        {"platform": {'$regex': '.*'}}).sort("platform", -1)
    platforms = {}
    for document in cursor:
        platforms[document["code"]] = document["platform"]
    json_output = json.dumps(platforms, sort_keys=True, indent=2)
    return json_output


# Create SNPchip function
def convert_codeToPlatforms(platform_query, web):
    platforms = []
    # Connect to Mongo snp database
    if web:
        client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
    else:
        client = MongoClient('localhost', port)
    db = client["LDLink"]
    code_array = platform_query.split('+')
    cursor = db.platforms.find({"code": {'$in': code_array}})
    for document in cursor:
        platforms.append(document["platform"])
    print platforms
    return platforms


def calculate_chip(snplst, platform_query, web, request):

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    dbsnp_version = config['data']['dbsnp_version']

    tmp_dir = "./tmp/"

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    out_json = open(tmp_dir+'proxy'+request+".json", "w")
    output = {}

    # Open SNP list file
    snps_raw = open(snplst).readlines()
    if len(snps_raw) > 5000:
        output["error"] = "Maximum SNP list is 5,000 RS numbers. Your list contains " + \
            str(len(snps_raw))+" entries."
        return(json.dumps(output, sort_keys=True, indent=2))

    # Remove duplicate RS numbers
    snps = []
    for snp_raw in snps_raw:
        snp = snp_raw.strip().split()
        if snp not in snps:
            snps.append(snp)

    # Connect to Mongo snp database
    if web:
        client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
    else:
        client = MongoClient('localhost', port)
    db = client["LDLink"]

    def get_coords(db, rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp151.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Query genomic coordinates
    def get_rsnum(db, coord):
        temp_coord = coord.strip("chr").split(":")
        chro = temp_coord[0]
        pos = temp_coord[1]
        query_results = db.dbsnp151.find({"chromosome": chro, "position": pos})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coords_rsid(db, snp_lst):
        new_snp_lst = []
        for snp_raw_i in snp_lst:
            if snp_raw_i[0][0:2] == "rs":
                new_snp_lst.append(snp_raw_i)
            else:
                snp_info_lst = get_rsnum(db, snp_raw_i[0])
                print "snp_info_lst"
                print snp_info_lst
                if snp_info_lst != None:
                    if len(snp_info_lst) > 1:
                        var_id = "rs" + snp_info_lst[0]['id']
                        ref_variants = []
                        for snp_info in snp_info_lst:
                            if snp_info['id'] == snp_info['ref_id']:
                                ref_variants.append(snp_info['id'])
                        if len(ref_variants) > 1:
                            var_id = "rs" + ref_variants[0]
                            if "warning" in output:
                                output["warning"] = output["warning"] + \
                                ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                            else:
                                output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                        elif len(ref_variants) == 0 and len(snp_info_lst) > 1:
                            var_id = "rs" + snp_info_lst[0]['id']
                            if "warning" in output:
                                output["warning"] = output["warning"] + \
                                ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                            else:
                                output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                        else:
                            var_id = "rs" + ref_variants[0]
                        new_snp_lst.append([var_id])
                    elif len(snp_info_lst) == 1:
                        var_id = "rs" + snp_info_lst[0]['id']
                        new_snp_lst.append([var_id])
                    else:
                        new_snp_lst.append(snp_raw_i)
                else:
                    new_snp_lst.append(snp_raw_i)
        return new_snp_lst

    snps = replace_coords_rsid(db, snps)

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
                    if snp_coord != None:
                        if snp_coord['chromosome'] == "X":
                            chr = 23
                        elif snp_coord['chromosome'] == "Y":
                            chr = 24
                        else:
                            chr = int(snp_coord['chromosome'])
                        rs_nums.append(snp_i[0])
                        snp_pos.append(snp_coord['position'])
                        temp = [snp_i[0], chr, int(snp_coord['position'])]
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
        output["warning"] = "The following RS number(s) or coordinate(s) were not found in dbSNP " + \
            dbsnp_version + ": " + ", ".join(warn)+".\n"
    elif len(rs_nums) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers that are in dbSNP " + \
            dbsnp_version + ".\n"
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print >> out_json, json_output
        out_json.close()
        createOutputFile(request)
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

    # Connect to Mongo snp database
    if web:
        client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
    else:
        client = MongoClient('localhost', port)
    db = client["LDLink"]
    platformcount = 0
    count = 0
    platform_NOT = []
    if platform_query != "":  # <--If user did not enter platforms as a request
        platform_list = convert_codeToPlatforms(platform_query, web)
    # Quering MongoDB to get platforms for position/chromsome pairs
    else:
        platform_list = []
    for k in range(len(snp_coords_sort)):
        platforms = []
        position = str(snp_coords_sort[k][2])
        Chr = str(snp_coords_sort[k][1])
        cursor = ()
        platform = ""
        count = count+1
        if platform_query == "":  # <--If user did not enter platforms as a request
            cursor = db.snp_col.find({'$and': [{"pos": position}, {"data.chr": Chr}, {
                                     "data.platform": {'$regex': '.*'}}]})  # Json object that stores all the results
        elif platform_query != "":  # <--If user did not enter platforms as a request
            cursor = db.snp_col.find({'$and': [{"pos": position}, {"data.chr": Chr}, {
                                     "data.platform": {"$in": platform_list}}]})  # Json object that stores all the results
            # Parsing each docuemnt to retrieve platforms
        for document in cursor:
            for z in range(0, len(document["data"])):
                if(document["data"][z]["chr"] == Chr and document["data"][z]["platform"] in platform_list and platform_query != ""):
                    platform = document["data"][z]["platform"]
                    platforms.append(document["data"][z]["platform"])
                elif(document["data"][z]["chr"] == Chr and platform_query == ""):
                    platforms.append(document["data"][z]["platform"])
                    platform = document["data"][z]["platform"]
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
    print >> out_json, json_output
    out_json.close()
    createOutputFile(request)

    return json_output


def createOutputFile(request):
    tmp_dir = "./tmp/"

    details_file = open(tmp_dir+'details'+request+".txt", "w")

    with open("./tmp/proxy"+request+".json") as out_json:
        json_dict = json.load(out_json)

    rs_dict = dict(json_dict)
    del rs_dict['error']
    del rs_dict['warning']

    # Header
    header = ["RS Number", "Position (GRCh37)", "Arrays"]
    print >>details_file, "\t".join(header)

    # Body
    for i in range(0, len(rs_dict)):
        print >>details_file, "\t".join(rs_dict[str(i)])

    # Footer
    try:
        json_dict["warning"]
    except KeyError:
        print >>details_file, ""
    else:
        print json_dict["warning"]
        if(json_dict["warning"] != ""):
            print >>details_file, ""
            print >>details_file, "WARNING: "+json_dict["warning"]
            print >>details_file, ""
            print ""
            print "WARNING: "+json_dict["warning"]

    try:
        json_dict["error"]
    except KeyError:
        print >>details_file, ""
    else:
        print json_dict["error"]
        if (json_dict["error"] != ""):
            print >>details_file, ""
            print >>details_file, "ERROR: "+json_dict["error"]
            print >>details_file, ""
            print ""
            print "ERROR: "+json_dict["error"]

    details_file.close()


def main():

    # Import SNPchip options
    if len(sys.argv) == 4:
        web = sys.argv[1]
        snplst = sys.argv[2]
        platform_query = sys.argv[3]
        request = sys.argv[4]
    else:
        print "Correct useage is: SNPchip.py false snplst platforms request, enter \"\" for platform_query if empty otherwise seperate each platform by a \"+\""
        sys.exit()

    # Run function
    calculate_chip(snplst, platform_query, web, request)


if __name__ == "__main__":
    main()
