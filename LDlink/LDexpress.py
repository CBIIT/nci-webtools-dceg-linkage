#!/usr/bin/env python3

import yaml
import json
import copy
import math
import os
import collections
import re
import requests
import csv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
import subprocess
from multiprocessing.dummy import Pool
import sys
import numpy as np	
from timeit import default_timer as timer

# Set data directories using config.yml	
with open('config.yml', 'r') as f:	
    config = yaml.load(f)	
env = config['env']
api_mongo_addr = config['api']['api_mongo_addr']
dbsnp_version = config['data']['dbsnp_version']	
pop_dir = config['data']['pop_dir']	
vcf_dir = config['data']['vcf_dir']
mongo_username = config['database']['mongo_user_readonly']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']
num_subprocesses = config['performance']['num_subprocesses']

def get_ldexpress_tissues(web):
    try:
        with open('config.yml', 'r') as c:
            config = yaml.load(c)
        env = config['env']
        api_mongo_addr = config['api']['api_mongo_addr']
        mongo_username = config['database']['mongo_user_readonly']
        mongo_password = config['database']['mongo_password']
        mongo_port = config['database']['mongo_port']

        # Connect to Mongo database
        if env == 'local':
            mongo_host = api_mongo_addr
        else: 
            mongo_host = 'localhost'
        if web:
            client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host + '/admin', mongo_port)
        else:
            if env == 'local':
                client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host + '/admin', mongo_port)
            else:
                client = MongoClient('localhost', mongo_port)
    except ConnectionFailure:
        print("MongoDB is down")
        print("syntax: mongod --dbpath /local/content/analysistools/public_html/apps/LDlink/data/mongo/data/db/ --auth")
        return "Failed to connect to server."

    db = client["LDLink"]
    if "gtex_tissues" in db.list_collection_names():
        documents = list(db.gtex_tissues.find())
        # print("documents", documents)
        tissues = {
            "tissueInfo": documents
        }
        json_output = json.dumps(tissues, default=json_util.default, sort_keys=True, indent=2)
        return json_output
    else:
        return None

def get_query_variant(snp_coord, pop_ids, request):
    tmp_dir = "./tmp/"
    queryVariantWarnings = []
    # Extract query SNP phased genotypes
    vcf_query_snp_file = vcf_dir + snp_coord[1] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    tabix_query_snp_h = "tabix -H {0} | grep CHROM".format(vcf_query_snp_file)
    proc_query_snp_h = subprocess.Popen(tabix_query_snp_h, shell=True, stdout=subprocess.PIPE)
    head = [x.decode('utf-8') for x in proc_query_snp_h.stdout.readlines()][0].strip().split()
    # print("head length", len(head))

    tabix_query_snp = "tabix {0} {1}:{2}-{2} | grep -v -e END > {3}".format(vcf_query_snp_file, snp_coord[1], snp_coord[2], tmp_dir + "snp_no_dups_" + request + ".vcf")
    subprocess.call(tabix_query_snp, shell=True)
    # proc_query_snp = subprocess.Popen(tabix_query_snp, shell=True, stdout=subprocess.PIPE)
    # tabix_query_snp_out = [x.decode('utf-8') for x in proc_query_snp.stdout.readlines()]
    tabix_query_snp_out = open(tmp_dir + "snp_no_dups_" + request + ".vcf").readlines()
    # print("tabix_query_snp_out length", len(tabix_query_snp_out))
    # Validate error
    if len(tabix_query_snp_out) == 0:
        # print("ERROR", "len(tabix_query_snp_out) == 0")
        # handle error: snp + " is not in 1000G reference panel."
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not in 1000G reference panel."])
        subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return (None, queryVariantWarnings)
    elif len(tabix_query_snp_out) > 1:
        geno = []
        for i in range(len(tabix_query_snp_out)):
            if tabix_query_snp_out[i].strip().split()[2] == snp_coord[0]:
                geno = tabix_query_snp_out[i].strip().split()
        if geno == []:
            # print("ERROR", "geno == []")
            # handle error: snp + " is not in 1000G reference panel."
            queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not in 1000G reference panel."])
            subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
            subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
            return (None, queryVariantWarnings)
    else:
        geno = tabix_query_snp_out[0].strip().split()
    
    if geno[2] != snp_coord[0]:
        # print('handle warning: "Genomic position for query variant (" + snp + ") does not match RS number at 1000G position (chr" + geno[0]+":"+geno[1]+")"')
        queryVariantWarnings.append([snp_coord[0], "NA", "Genomic position does not match RS number at 1000G position (chr" + geno[0] + ":" + geno[1] + ")."])
        # snp = geno[2]

    if "," in geno[3] or "," in geno[4]:
        # print('handle error: snp + " is not a biallelic variant."')
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not a biallelic."])

    index = []
    for i in range(9, len(head)):
        if head[i] in pop_ids:
            index.append(i)

    genotypes = {"0": 0, "1": 0}
    for i in index:
        sub_geno = geno[i].split("|")
        for j in sub_geno:
            if j in genotypes:
                genotypes[j] += 1
            else:
                genotypes[j] = 1

    if genotypes["0"] == 0 or genotypes["1"] == 0:
        # print('handle error: snp + " is monoallelic in the " + pop + " population."')
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is monoallelic in the chosen population(s)."])
        
    return(geno, queryVariantWarnings)

def get_coords(db, rsid):
    rsid = rsid.strip("rs")
    query_results = db.dbsnp151.find_one({"id": rsid})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def chunkWindow(pos, window, num_subprocesses):
    if (pos - window <= 0):
        minPos = 0
    else:
        minPos = pos - window
    maxPos = pos + window
    windowRange = maxPos - minPos
    chunks = []
    newMin = minPos
    newMax = 0
    for _ in range(num_subprocesses):
        newMax = newMin + (windowRange / num_subprocesses)
        chunks.append([math.ceil(newMin), math.ceil(newMax)])
        newMin = newMax
    return chunks

# collect output in parallel
def get_output(process):
    return process.communicate()[0].splitlines()

# Create LDexpress function
def calculate_express(snplst, pop, request, web, tissues, r2_d, r2_d_threshold=0.1, p_threshold=0.1, window=500000):
    print("##### START LD EXPRESS CALCULATION #####")	
    print("raw snplst", snplst)
    print("raw pop", pop)
    print("raw request", request)
    print("raw web", web)
    print("raw tissues", tissues)
    print("raw r2_d", r2_d)
    print("raw r2_d_threshold", r2_d_threshold)
    print("raw p_threshold", p_threshold)
    print("raw window", window)

    full_start = timer()
    
    # SNP limit
    max_list = 10

    # Ensure tmp directory exists
    tmp_dir = "./tmp/"
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    errors_warnings = {}

    # Validate window size is between 0 and 1,000,000
    if window < 0 or window > 1000000:
        errors_warnings["error"] = "Window value must be a number between 0 and 1,000,000."
        return("", "", "", errors_warnings)

    # Parse SNPs list
    snps_raw = snplst.split("+")
    # Generate error if # of inputted SNPs exceeds limit
    if len(snps_raw) > max_list:
        errors_warnings["error"] = "Maximum SNP list is " + \
            str(max_list)+" RS numbers. Your list contains " + \
            str(len(snps_raw))+" entries."
        return("", "", "", errors_warnings)
    # Remove duplicate RS numbers
    sanitized_query_snps = []
    for snp_raw in snps_raw:
        snp = snp_raw.strip()
        if snp not in sanitized_query_snps:
            sanitized_query_snps.append([snp])

    # Connect to Mongo database
    if env == 'local':
        mongo_host = api_mongo_addr
    else: 
        mongo_host = 'localhost'
    if web:
        client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@'+mongo_host+'/admin', mongo_port)
    else:
        if env == 'local':
            client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@'+mongo_host+'/admin', mongo_port)
        else:
            client = MongoClient('localhost', mongo_port)
    db = client["LDLink"]
    # Check if dbsnp collection in MongoDB exists, if not, display error
    if "dbsnp151" not in db.list_collection_names():
        errors_warnings["error"] = "dbSNP is currently unavailable. Please contact support."
        return("", "", "", errors_warnings)

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(pop_dir+pop_i+".txt")
        else:
            errors_warnings["error"] = pop_i + " is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            return("", "", "", errors_warnings)

    # get_pops = "cat " + " ".join(pop_dirs)
    # proc = subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE)
    # pop_list = [x.decode('utf-8') for x in proc.stdout.readlines()]

    get_pops = "cat " + " ".join(pop_dirs) + " > " + tmp_dir + "pops_" + request + ".txt"
    subprocess.call(get_pops, shell=True)

    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    # tissue_ids = tissue.split("+")
    # print("tissue_ids", tissue_ids)

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
                new_snp_lst.append(snp_raw_i)
            else:
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
                            if "warning" in errors_warnings:
                                errors_warnings["warning"] = errors_warnings["warning"] + \
                                    ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                            else:
                                errors_warnings["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                        elif len(ref_variants) == 0 and len(snp_info_lst) > 1:
                            var_id = "rs" + snp_info_lst[0]['id']
                            if "warning" in errors_warnings:
                                errors_warnings["warning"] = errors_warnings["warning"] + \
                                    ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
                            else:
                                errors_warnings["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0]
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
    print("sanitized_query_snps", sanitized_query_snps)

    # Find genomic coords of query snps in dbsnp 
    details = {}
    rs_nums = []
    snp_pos = []
    snp_coords = []
    warn = []
    # windowWarnings = []
    queryWarnings = []
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
                    queryWarnings.append([snp_i[0], "NA", "Variant not found in dbSNP" + dbsnp_version + ", variant removed."])
            else:
                # Generate warning if query variant is not a genomic position or rs number
                warn.append(snp_i[0])
                queryWarnings.append([snp_i[0], "NA", "Not a valid SNP, variant removed."])
        else:
            # Generate error for empty query variant
            errors_warnings["error"] = "Input list of RS numbers is empty"
            subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
            return("", "", "", errors_warnings)

    # Generate warnings for query variants not found in dbsnp
    if warn != []:
        errors_warnings["warning"] = "The following RS number(s) or coordinate(s) were not found in dbSNP " + \
            dbsnp_version + ": " + ", ".join(warn)

    # Generate errors if no query variants are valid in dbsnp
    if len(rs_nums) == 0:
        errors_warnings["error"] = "Input SNP list does not contain any valid RS numbers that are in dbSNP " + dbsnp_version + "."
        subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
        return("", "", "", errors_warnings)

    thinned_list = []

    print("##### FIND GWAS VARIANTS IN WINDOW #####")	
    # establish low/high window for each query snp
    # ex: window = 500000 # -/+ 500Kb = 500,000Bp = 1Mb = 1,000,000 Bp total
    for snp_coord in snp_coords:
        find_window_ld_start = timer()

        (geno, queryVariantWarnings) = get_query_variant(snp_coord, pop_ids, str(request))
        if (len(queryVariantWarnings) > 0):
            queryWarnings += queryVariantWarnings
        if (geno is not None):
            ###### SPLIT TASK UP INTO # PARALLEL SUBPROCESSES ######

            # find query window snps via tabix, calculate LD and apply R2/D' thresholds
            windowChunkRanges = chunkWindow(snp_coord[2], window, num_subprocesses)
            
            ld_subprocess_commands = []
            for subprocess_id in range(num_subprocesses):
                getWindowVariantsArgs = " ".join([str(web), str(snp_coord[0]), str(snp_coord[1]), str(windowChunkRanges[subprocess_id][0]), str(windowChunkRanges[subprocess_id][1]), str(request), str(subprocess_id), str(r2_d), str(r2_d_threshold)])
                ld_subprocess_commands.append("python3 LDexpress_ld_sub.py " + getWindowVariantsArgs)

            ld_subprocesses = [subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in ld_subprocess_commands]
            # collect output in parallel
            pool = Pool(len(ld_subprocesses))
            windowLDSubsets = pool.map(get_output, ld_subprocesses)
            pool.close()
            pool.join()

            # flatten pooled ld window results
            windowLDSubsetsFlat = [val.decode('utf-8').strip().split("\t") for sublist in windowLDSubsets for val in sublist]
            # print("windowLDSubsetsFlat length", len(windowLDSubsetsFlat))

            find_window_ld_end = timer()
            # print("FIND WINDOW SNPS AND CALCULATE LD TIME ELAPSED:", str(find_window_ld_end - find_window_ld_start) + "(s)")

            # find gtex tissues for window snps via mongodb, apply p-value threshold

            query_window_tissues_start = timer()

            windowLDSubsetsChunks = np.array_split(windowLDSubsetsFlat, num_subprocesses)

            for subprocess_id in range(num_subprocesses):
                with open(tmp_dir + 'express_ld_' + str(subprocess_id) + '_' + str(request) + '.txt', 'w') as snpsLDFile:
                    for snp_ld_data in windowLDSubsetsChunks[subprocess_id].tolist():
                        snpsLDFile.write("\t".join(snp_ld_data) + "\n")

            tissues_subprocess_commands = []
            for subprocess_id in range(num_subprocesses):
                getTissuesArgs = " ".join([str(web), str(request), str(subprocess_id), str(p_threshold), str(tissues)])
                tissues_subprocess_commands.append("python3 LDexpress_tissues_sub.py " + getTissuesArgs)

            tissues_subprocesses = [subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in tissues_subprocess_commands]

            # getTissuesArgs = []	
            # for subprocess_id in range(num_subprocesses):	
            #     getTissuesArgs.append([windowLDSubsetsChunks[subprocess_id].tolist(), subprocess_id, p_threshold, tissue_ids, web])	
            # with Pool(processes=num_subprocesses) as pool:	
            #     tissueResultsSubsets = pool.map(get_tissues_sub, getTissuesArgs)	

            # collect output in parallel
            pool = Pool(len(tissues_subprocesses))
            tissueResultsSubsets = pool.map(get_output, tissues_subprocesses)
            pool.close()
            pool.join()

            # flatten pooled tissues results
            matched_snps = [val.decode('utf-8').strip().split("\t") for sublist in tissueResultsSubsets for val in sublist]
            # print("matched_snps length", len(matched_snps))

            # # flatten tissue results
            # matched_snps = [val for sublist in tissueResultsSubsets for val in sublist]
            # print("matched_snps length", len(matched_snps))

            # print("FINAL # RESULTS FOR", snp_coord[0], len(matched_snps))
            if (len(matched_snps) > 0):
                details[snp_coord[0]] = {	
                    "aaData": matched_snps
                }
                # add snp to thinned_list
                thinned_list.append(snp_coord[0])
            else:
                queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No entries in GTEx are identified using the LDexpress search criteria."]) 

            query_window_tissues_end = timer()
            print("QUERY WINDOW TISSUES TIME ELAPSED:", str(query_window_tissues_end - query_window_tissues_start) + "(s)")
        # clean up tmp files generated by each query snp
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        subprocess.call("rm " + tmp_dir + "express_ld_*_" + str(request) + ".txt", shell=True)
    # # clean up tmp file(s) generated by each calculation
    subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
    

    details["queryWarnings"] = {
        "aaData": queryWarnings
    }

    # Check if thinned list is empty, if it is, display error
    if len(thinned_list) < 1:
        errors_warnings["error"] = "No entries in GTEx are identified using the LDexpress search criteria."
        return("", "", "", errors_warnings)

    full_end = timer()	
    print("TIME ELAPSED:", str(full_end - full_start) + "(s)")	
    print("##### LDEXPRESS COMPLETE #####")
    return (sanitized_query_snps, thinned_list, details, errors_warnings)


def main():
    # snplst = sys.argv[1]
    snplst = "../tests/end-to-end/test-data/sample_LDexpress.txt"
    pop = "YRI+CEU"
    request = 8888
    web = False
    r2_d = "r2"
    r2_d_threshold = 0.1
    p_threshold = 0.1
    window = 500000
    tissues = "Adipose_Subcutaneous+Adipose_Visceral_Omentum"

    # Run function
    (sanitized_query_snps, thinned_list, details, errors_warnings) = calculate_express(snplst, pop, request, web, tissues, r2_d, r2_d_threshold, p_threshold, window)
    print()
    print("##### FINAL LDEXPRESS.PY OUT - RETURN TO FRONTEND #####")
    print("query_snps", sanitized_query_snps)
    print("thinned_snps", thinned_list)
    print("details", json.dumps(details))
    # print("##### GET GTEx TISSUES #####")
    # print(get_ldexpress_tissues())

if __name__ == "__main__":
    main()