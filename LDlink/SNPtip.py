#!/usr/bin/env python
import json
import math
import operator
import os
import subprocess
import sys
import yaml
from pymongo import MongoClient
from bson import json_util, ObjectId
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = contents[0].split('=')[1]
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])

# SNPtip
# Locate genomic location and SNP annotation

# Create SNPtip function
def calculate_tip(snplst, request):

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    dbsnp_version = config['data']['dbsnp_version']

    tmp_dir = "./tmp/"

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    out_json = open(tmp_dir+"matrix"+request+".json", "w")
    output = {}

    # Open SNP list file
    snps_raw = open(snplst).readlines()
    max_list = 5000
    if len(snps_raw) > max_list:
        output["error"] = "Maximum SNP list is " + \
            str(max_list)+" RS numbers. Your list contains " + \
            str(len(snps_raw))+" entries."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print >> out_json, json_output
        out_json.close()
        return("")

    # Remove duplicate RS numbers
    snps = []
    for snp_raw in snps_raw:
        snp = snp_raw.strip().split()
        if snp not in snps:
            snps.append(snp)

    # Connect to Mongo snp database
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
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
    snp_coords = []
    warn = []
    for snp_i in snps:
        if len(snp_i) > 0:
            if len(snp_i[0]) > 2:
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                    snp_coord = get_coords(db, snp_i[0])
                    if snp_coord != None:
                        chr = snp_coord['chromosome']
                        if chr == "X":
                            chr = "23"
                        if chr == "Y":
                            chr = "24"
                        temp = [snp_i[0], int(chr), int(snp_coord['position'])]
                        snp_coords.append(temp)
                    else:
                        warn.append(snp_i[0])
                else:
                    warn.append(snp_i[0])
            else:
                warn.append(snp_i[0])

    if warn != []:
        output["warning"] = "The following RS number(s) or coordinate(s) were not found in dbSNP " + \
            dbsnp_version + ": " + ", ".join(warn)

    if len(snp_coords) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers that are in dbSNP " + \
            dbsnp_version + "."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print >> out_json, json_output
        out_json.close()
        return("")

    # Sort by chromosome and position
    from operator import itemgetter
    snp_sorted = sorted(snp_coords, key=itemgetter(1, 2))

    # Convert back to X and Y
    snp_sorted_chr = []
    for i in snp_sorted:
        if i[1] == 23:
            chr = "X"
        elif i[1] == 24:
            chr = "Y"
        else:
            chr = i[1]
        temp = [i[0], str(chr), str(i[2])]
        snp_sorted_chr.append(temp)

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print >> out_json, json_output
    out_json.close()
    return(snp_sorted_chr)


def main():
    import json
    import sys
    tmp_dir = "./tmp/"

    # Import LDmatrix options
    if len(sys.argv) == 3:
        snplst = sys.argv[1]
        request = sys.argv[2]
    else:
        print "Correct useage is: SNPtip.py snplst request"
        sys.exit()

    # Run function
    out_info = calculate_tip(snplst, request)

    # Print output
    with open(tmp_dir+"matrix"+request+".json") as f:
        json_dict = json.load(f)

    try:
        json_dict["error"]

    except KeyError:
        print ""
        header = "RS Number\tChromosome\tPosition(GRCh37)"
        print header
        for i in out_info:
            print "\t".join(i)

        try:
            json_dict["warning"]

        except KeyError:
            print ""
        else:
            print ""
            print "WARNING: "+json_dict["warning"]+"."
            print ""

    else:
        print ""
        print json_dict["error"]
        print ""


if __name__ == "__main__":
    main()
