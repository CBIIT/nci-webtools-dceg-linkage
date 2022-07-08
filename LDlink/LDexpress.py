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
import boto3
import botocore
from timeit import default_timer as timer
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars,connectMongoDBReadOnly
from LDcommon import get_coords,get_population,validsnp,replace_coords_rsid_list,get_coords,get_query_variant_c,chunkWindow,get_output
from LDutilites import get_config
# Set data directories using config.yml 
param_list = get_config()
dbsnp_version = param_list['dbsnp_version']
data_dir = param_list['data_dir']
tmp_dir = param_list['tmp_dir']
population_samples_dir = param_list['population_samples_dir']
genotypes_dir = param_list['genotypes_dir']
aws_info = param_list['aws_info']
num_subprocesses = param_list['num_subprocesses']

def get_ldexpress_tissues(web):
    try:
       db = connectMongoDBReadOnly(web)
    except ConnectionFailure:
        print("MongoDB is down")
        print("syntax: mongod --dbpath /local/content/analysistools/public_html/apps/LDlink/data/mongo/data/db/ --auth")
        return "Failed to connect to server."
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

# Create LDexpress function
def calculate_express(snplst, pop, request, web, tissues, r2_d, genome_build, r2_d_threshold=0.1, p_threshold=0.1, window=500000):
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
    print("raw genome_build", genome_build)
    full_start = timer()
    
    # SNP limit
    max_list = 10
    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    errors_warnings = {}
       # Parse SNPs list
    sanitized_query_snps = validsnp(snplst,genome_build,max_list)
    #if return value is string, then it is error message and need to return the message
    if isinstance(sanitized_query_snps, str):
        return("", "", "", "", "", sanitized_query_snps)
    # Validate window size is between 0 and 1,000,000
    if window < 0 or window > 1000000:
        errors_warnings["error"] = "Window value must be a number between 0 and 1,000,000."
        return("", "", "", "", "", errors_warnings)
     # Connect to Mongo database
    db = connectMongoDBReadOnly(web)
    # Check if dbsnp collection in MongoDB exists, if not, display error
    if "dbsnp" not in db.list_collection_names():
        errors_warnings["error"] = "dbSNP is currently unavailable. Please contact support."
        return("", "", "", "", "", errors_warnings)
    # Select desired ancestral populations
    pop_ids = get_population(pop,request,errors_warnings)
    if isinstance(pop_ids, str):
        return("", "", "", "", "", errors_warnings)
    sanitized_query_snps = replace_coords_rsid_list(db, sanitized_query_snps,genome_build,errors_warnings)
    # print("sanitized_query_snps", sanitized_query_snps)
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
                if snp_coord != None and snp_coord[genome_build_vars[genome_build]['position']] != "NA":
                     # check if variant is on chrY for genome build = GRCh38
                    if snp_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
                        if "warning" in errors_warnings:
                            errors_warnings["warning"] = errors_warnings["warning"] + \
                                ". " + "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
                        else:
                            errors_warnings["warning"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
                        warn.append(snp_i[0])
                    else:
                        rs_nums.append(snp_i[0])
                        snp_pos.append(snp_coord[genome_build_vars[genome_build]['position']])
                        temp = [snp_i[0], str(snp_coord['chromosome']), int(snp_coord[genome_build_vars[genome_build]['position']])]
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
            return("", "", "", "", "", errors_warnings)
    # Generate warnings for query variants not found in dbsnp
    if warn != []:
        if "warning" in errors_warnings:
            errors_warnings["warning"] = errors_warnings["warning"] + \
                ". The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
        else:
            errors_warnings["warning"] = "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
    # Generate errors if no query variants are valid in dbsnp
    if len(rs_nums) == 0:
        errors_warnings["error"] = "Input SNP list does not contain any valid RS numbers or coordinates. " + errors_warnings["warning"]
        subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
        return("", "", "", "", "", errors_warnings)
    thinned_snps = []
    print("##### FIND GWAS VARIANTS IN WINDOW #####")   
    # establish low/high window for each query snp
    # ex: window = 500000 # -/+ 500Kb = 500,000Bp = 1Mb = 1,000,000 Bp total
    combined_matched_snps = []
    for snp_coord in snp_coords:
        find_window_ld_start = timer()
        (geno, tmpdist, queryVariantWarnings) = get_query_variant_c(snp_coord, pop_ids, str(request), genome_build, True)
        # print("queryVariantWarnings", queryVariantWarnings)
        if (len(queryVariantWarnings) > 0):
            queryWarnings += queryVariantWarnings
        if (geno is not None):
            ###### SPLIT TASK UP INTO # PARALLEL SUBPROCESSES ######
            # find query window snps via tabix, calculate LD and apply R2/D' thresholds
            windowChunkRanges = chunkWindow(snp_coord[2], window, num_subprocesses)

            ld_subprocess_commands = []
            for subprocess_id in range(num_subprocesses):
                getWindowVariantsArgs = " ".join([str(web), str(snp_coord[0]), str(snp_coord[1]), str(windowChunkRanges[subprocess_id][0]), str(windowChunkRanges[subprocess_id][1]), str(request), str(subprocess_id), str(r2_d), str(r2_d_threshold), str(genome_build)])
                # print("getWindowVariantsArgs", getWindowVariantsArgs)
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
                getTissuesArgs = " ".join([str(web), str(request), str(subprocess_id), str(p_threshold), str(tissues), str(genome_build)])
                #print(getTissuesArgs)
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
            # print("FINAL # RESULTS FOR", snp_coord[0], len(matched_snps))
            if (len(matched_snps) > 0):
                # details[snp_coord[0]] = { 
                # details["results"] = {    
                #     "aaData": matched_snps
                # }
                combined_matched_snps += matched_snps
                # add snp to thinned_snps
                thinned_snps.append(snp_coord[0])
            else:
                queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No entries in GTEx are identified using the LDexpress search criteria."]) 
            query_window_tissues_end = timer()
            print("QUERY WINDOW TISSUES TIME ELAPSED:", str(query_window_tissues_end - query_window_tissues_start) + "(s)")
        # clean up tmp files generated by each query snp
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        subprocess.call("rm " + tmp_dir + "express_ld_*_" + str(request) + ".txt", shell=True)
    
    # add full results
    details["results"] = {  
        "aaData": combined_matched_snps
    }
    # find unique thinned genes and tissues
    thinned_genes = sorted(list(set(list(map(lambda row: row[5], combined_matched_snps)))))
    thinned_tissues = sorted(list(set(list(map(lambda row: row[7], combined_matched_snps)))))
    
    # # clean up tmp file(s) generated by each calculation
    subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
    details["queryWarnings"] = {
        "aaData": queryWarnings
    }
    # Check if thinned list is empty, if it is, display error
    if len(thinned_snps) < 1:
        errors_warnings["error"] = "No entries in GTEx are identified using the LDexpress search criteria."
        return("", "", "", "", "", errors_warnings)
    full_end = timer()  
    print("TIME ELAPSED:", str(full_end - full_start) + "(s)")  
    print("##### LDEXPRESS COMPLETE #####")
    return (sanitized_query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings)
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
    genome_build = 'grch37'
    # Run function
    (sanitized_query_snps, thinned_snps, details, errors_warnings) = calculate_express(snplst, pop, request, web, tissues, r2_d, genome_build, r2_d_threshold, p_threshold, window)
    print()
    print("##### FINAL LDEXPRESS.PY OUT - RETURN TO FRONTEND #####")
    print("query_snps", sanitized_query_snps)
    print("thinned_snps", thinned_snps)
    print("details", json.dumps(details))
    # print("##### GET GTEx TISSUES #####")
    # print(get_ldexpress_tissues())
if __name__ == "__main__":
    main()
