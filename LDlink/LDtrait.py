#!/usr/bin/env python3

import yaml
import json
# import math
# import operator
import os
import collections
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = contents[0].split('=')[1]
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])


def pretty_print_json(obj):
    return json.dumps(obj, sort_keys = True, indent = 4, separators = (',', ': '))

def get_window_variants(db, chromosome, position, window):
    query_results = db.gwas_catalog.find({
        "chromosome_grch37": chromosome, 
        "position_grch37": {
            "$gte": (position - window) if (position - window) > 0 else 0, 
            "$lte": position + window
        }
    })
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def get_gwas_fields(query_snp, found):
    matched_gwas = []
    for record in found:
        matched_record = []
        matched_record.append(query_snp)
        matched_record.append(record["MAPPED_TRAIT"])
        matched_record.append("rs" + record["SNP_ID_CURRENT"])
        matched_record.append("chr" + str(record["chromosome_grch37"]) + ":" + str(record["position_grch37"]))
        matched_record.append("Variant found in GWAS catalog within window.")
        matched_gwas.append(matched_record)
    return matched_gwas

# Create LDtrait function
# def calculate_trait(snplst, pop, request, web, r2_d, r2_d_threshold=0.1):
def calculate_trait(snplst, pop, request, web, r2_d, r2_d_threshold=0.1):

    # snp limit
    max_list = 250

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    dbsnp_version = config['data']['dbsnp_version']
    pop_dir = config['data']['pop_dir']
    vcf_dir = config['data']['vcf_dir']

    # Ensure tmp directory exists
    tmp_dir = "./tmp/"
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output for warnings and errors
    out_json = open(tmp_dir + "trait" + str(request) + ".json", "w")
    output = {}

    # initialize output dict -> json
    # out_json = {
    #     "found": {},
    #     "not_found": [],
    #     "populations": pop
    # }


    # open snps file
    with open(snplst, 'r') as fp:
        snps_raw = fp.readlines()
        # Generate error if # of inputted SNPs exceeds limit
        if len(snps_raw) > max_list:
            output["error"] = "Maximum SNP list is " + \
            str(max_list)+" RS numbers. Your list contains " + \
            str(len(snps_raw))+" entries."
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")
        # Remove duplicate RS numbers
        sanitized_query_snps = []
        for snp_raw in snps_raw:
            snp = snp_raw.strip()
            if snp not in sanitized_query_snps:
                sanitized_query_snps.append([snp])

    # print("remove duplicates & sanitize", sanitized_query_snps) 


    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(pop_dir+pop_i+".txt")
        else:
            output["error"] = pop_i+" is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    get_pops = "cat " + " ".join(pop_dirs)
    proc = subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE)
    pop_list = proc.stdout.readlines()

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    # print "pop_ids", pop_ids


    # Connect to Mongo snp database
    if web:
        client = MongoClient('mongodb://' + username + ':' + password + '@localhost/admin', port)
    else:
        client = MongoClient('localhost', port)
    db = client["LDLink"]

    # Get genomic coordinates from rs number from dbsnp151
    def get_coords(db, rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp151.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized


    # Get rs number from genomic coordinates from dbsnp151
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
                # print "reached 1", snp_raw_i
                new_snp_lst.append(snp_raw_i)
            else:
                # print "reached 2", snp_raw_i
                snp_info_lst = get_rsnum(db, snp_raw_i[0])
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

    sanitized_query_snps = replace_coords_rsid(db, sanitized_query_snps)


    # find genomic coords of query snps in dbsnp 
    # query_snp_details = []
    # details = collections.OrderedDict()
    details = {}
    rs_nums = []
    snp_pos = []
    snp_coords = []
    warn = []
    warnings = []
    for snp_i in sanitized_query_snps:
        if (len(snp_i) > 0 and len(snp_i[0]) > 2):
            if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                # query variant to get genomic coordinates in dbsnp
                snp_coord = get_coords(db, snp_i[0])
                if snp_coord != None:
                    rs_nums.append(snp_i[0])
                    snp_pos.append(int(snp_coord['position']))
                    temp = [snp_i[0], str(snp_coord['chromosome']), int(snp_coord['position'])]
                    snp_coords.append(temp)
                else:
                    # Generate warning if query variant is not found in dbsnp
                    warn.append(snp_i[0])
                    warnings.append([snp_i[0], "NA", "NA", "Variant not found in dbSNP" + dbsnp_version + ", variant removed."])
            else:
                # Generate warning if query variant is not a genomic position or rs number
                warn.append(snp_i[0])
                warnings.append([snp_i[0], "NA", "NA", "Not a valid SNP, query removed."])
        else:
            # Generate error for empty query variant
            output["error"] = "Input list of RS numbers is empty"
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    # print("rs_nums", rs_nums)
    # print("snp_pos", snp_pos)
    # print("snp_coords", snp_coords)
    print("warn", warn)
    details["warnings"] = {
        "aaData": warnings
    }

    # generate warnings for query variants not found in dbsnp
    if warn != []:
        output["warning"] = "The following RS number(s) or coordinate(s) were not found in dbSNP " + \
            dbsnp_version + ": " + ", ".join(warn)

    # Generate errors if no query variants are valid in dbsnp
    if len(rs_nums) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers that are in dbSNP " + \
            dbsnp_version + "."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "", "")

    # Check SNPs are all on the same chromosome
    for i in range(len(snp_coords)):
        if snp_coords[0][1] != snp_coords[i][1]:
            output["error"] = "Not all input variants are on the same chromosome: "+snp_coords[i-1][0]+"=chr" + \
                str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0] + \
                "=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+"."
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    


    # # search dbsnp for snp's genomic coordinates
    # for snp in sanitized_query_snps:
    #     snp_info = get_coords(db, snp[0])
    #     if snp_info is not None:
    #         query_snp_details.append({
    #             "rsnum": snp[0],
    #             "chromosome": str(snp_info["chromosome"]),
    #             "position": int(snp_info["position"])
    #         })
    #     # else:
    #     #     out_json["not_found"].append(snp)
    
    # print "query_snp_details", pretty_print_json(query_snp_details)
    # print

    thinned_list = []

    # establish low/high window for each query snp
    window = 2000000
    # search query snp windows in gwas_catalog
    for snp_coord in snp_coords:
        # print(snp_coord)
        found = get_window_variants(db, snp_coord[1], snp_coord[2], window)
        # print("found: " + str(len(found)))
        if found is not None:
            thinned_list.append(snp_coord[0])
            details[snp_coord[0]] = {	
                "aaData": get_gwas_fields(snp_coord[0], found)	
            }
            # out_json["found"][query_snp["rsnum"]] = get_gwas_fields(found)
        # else:
            # out_json["not_found"].append(query_snp["rsnum"])

    # return (thinned_list, sanitized_query_snps, out_json)

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()
    # print("##### LDTRAIT DETAILS: #####")
    # print(details)
    return (sanitized_query_snps, thinned_list, details)


def main():
    # snplst = sys.argv[1]
    snplst = "5_LDtrait_snps.txt"
    pop = "YRI"
    request = 8888
    web = False
    r2_d = "r2"
    r2_d_threshold = 0.15

    # Run function
    (thinned_list, sanitized_query_snps, details) = calculate_trait(snplst, pop, request, web, r2_d, r2_d_threshold)
    print("snp_list", thinned_list)
    print("snps", sanitized_query_snps)
    print("details", json.dumps(details))
    # print "out_json", pretty_print_json(out_json)

if __name__ == "__main__":
    main()