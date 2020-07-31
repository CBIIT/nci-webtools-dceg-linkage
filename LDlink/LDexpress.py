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
from multiprocessing import Pool
import sys
import numpy as np	
from timeit import default_timer as timer


# Set data directories using config.ini	
with open('config.ini', 'r') as f:	
    config = yaml.load(f)	
env = config['env']
api_mongo_addr = config['api']['api_mongo_addr']
dbsnp_version = config['data']['dbsnp_version']	
pop_dir = config['data']['pop_dir']	
vcf_dir = config['data']['vcf_dir']
mongo_username = config['database']['mongo_user_readonly']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']
ldexpress_threads = config['performance']['ldexpress_threads']

def get_ldexpress_tissues():
    PAYLOAD = {
            "format" : "json",
            "datasetId": "gtex_v8"
        }
    REQUEST_URL = "https://gtexportal.org/rest/v1/dataset/tissueInfo"
    try:
        r = requests.get(REQUEST_URL, params=PAYLOAD)
        responseObj = json.loads(r.text)
    except:
        errorObj = {
            "error": "Failed to retrieve tissues from GTEx Portal server."
        }
        return json.dumps(json.loads(errorObj))
    return json.dumps(responseObj)

def get_query_variant(snp_coord, pop_ids):
    # Extract query SNP phased genotypes
    vcf_query_snp_file = vcf_dir + snp_coord[1] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    tabix_query_snp_h = "tabix -H {0} | grep CHROM".format(vcf_query_snp_file)
    proc_query_snp_h = subprocess.Popen(tabix_query_snp_h, shell=True, stdout=subprocess.PIPE)
    head = [x.decode('utf-8') for x in proc_query_snp_h.stdout.readlines()][0].strip().split()
    # print("head length", len(head))

    tabix_query_snp = "tabix {0} {1}:{2}-{2} | grep -v -e END".format(vcf_query_snp_file, snp_coord[1], snp_coord[2])
    proc_query_snp = subprocess.Popen(tabix_query_snp, shell=True, stdout=subprocess.PIPE)
    tabix_query_snp_out = [x.decode('utf-8') for x in proc_query_snp.stdout.readlines()]
    print("tabix_query_snp_out length", len(tabix_query_snp_out))
    # Validate error
    if len(tabix_query_snp_out) == 0:
        print("ERROR", "len(tabix_query_snp_out) == 0")
        # handle error: snp + " is not in 1000G reference panel."
    elif len(tabix_query_snp_out) > 1:
        geno = []
        for i in range(len(tabix_query_snp_out)):
            if tabix_query_snp_out[i].strip().split()[2] == snp_coord[0]:
                geno = tabix_query_snp_out[i].strip().split()
        if geno == []:
            print("ERROR", "geno == []")
            # handle error: snp + " is not in 1000G reference panel."
    else:
        geno = tabix_query_snp_out[0].strip().split()
    
    if geno[2] != snp_coord[0]:
        print('handle warning: "Genomic position for query variant (" + snp + ") does not match RS number at 1000G position (chr" + geno[0]+":"+geno[1]+")"')
        # snp = geno[2]

    if "," in geno[3] or "," in geno[4]:
        print('handle error: snp + " is not a biallelic variant."')

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
        print('handle error: snp + " is monoallelic in the " + pop + " population."')
        
    return(geno)

def get_coords(db, rsid):
    rsid = rsid.strip("rs")
    query_results = db.dbsnp151.find_one({"id": rsid})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def LD_calcs(hap, allele, allele_n):
    # Extract haplotypes
    A = hap["00"]
    B = hap["01"]
    C = hap["10"]
    D = hap["11"]
    # N = A + B + C + D
    # tmax = max(A, B, C, D)
    delta = float(A * D - B * C)
    Ms = float((A + C) * (B + D) * (A + B) * (C + D))
    # Minor allele frequency
    # maf_q = min((A + B) / float(N), (C + D) / float(N))
    # maf_p = min((A + C) / float(N), (B + D) / float(N))
    if Ms != 0:
        # D prime
        if delta < 0:
            D_prime = abs(delta / min((A + C) * (A + B), (B + D) * (C + D)))
        else:
            D_prime = abs(delta / min((A + C) * (C + D), (A + B) * (B + D)))
        # R2
        r2 = (delta ** 2) / Ms
        # # Find Correlated Alleles
        # equiv = "="
        # # Find Correlated Alleles
        # if str(r2) != "NA" and float(r2) > 0.1:
        #     Ac = hap[sorted(hap)[0]]
        #     Bc = hap[sorted(hap)[1]]
        #     Cc = hap[sorted(hap)[2]]
        #     Dc = hap[sorted(hap)[3]]
        #     if ((Ac * Dc) / max((Bc * Cc), 0.01) > 1):
        #         match = allele[sorted(hap)[0][0]] + equiv + allele_n[sorted(hap)[0][1]] + "," + allele[sorted(hap)[3][0]] + equiv + allele_n[sorted(hap)[3][1]]
        #     else:
        #         match = allele[sorted(hap)[1][0]] + equiv + allele_n[sorted(hap)[1][1]] + "," + allele[sorted(hap)[2][0]] + equiv + allele_n[sorted(hap)[2][1]]
        # else:
        #     match = "NA"
        return {
            "r2": r2,
            "D_prime": D_prime,
            # "output": output
        }

def get_window_variants(db, snp, chromosome, position, window, pop_ids, geno, allele, r2_d, r2_d_threshold, p_threshold):
    print("get_window_variants geno[0-4...]", ", ".join(geno[0:5]))
    # Get VCF region
    vcf_file = vcf_dir + chromosome + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    tabix_snp = "tabix -fh {0} {1}:{2}-{3} | grep -v -e END".format(
        vcf_file, chromosome, position - window, position + window)
    proc = subprocess.Popen(tabix_snp, shell=True, stdout=subprocess.PIPE)
    vcf_window_snps = csv.reader([x.decode('utf-8') for x in proc.stdout.readlines()], dialect="excel-tab")

    # Loop past file information and find header
    head = next(vcf_window_snps, None)
    while head[0][0:2] == "##":
        head = next(vcf_window_snps, None)

    # Create Index of Individuals in Population
    index = []
    for i in range(9, len(head)):
        if head[i] in pop_ids:
            index.append(i)
    vcf_window_snps = list(vcf_window_snps)
    print(str(snp) + " vcf_window_snps LENGTH", len(vcf_window_snps))

    ###### SPLIT TASK UP INTO 4 PARALLEL THREADS
    # vcf_window_snps_split = np.array_split(vcf_window_snps, ldexpress_threads)	
    # for idx, arr in enumerate(vcf_window_snps_split, start=1):
    #     print("array thread " + str(idx) + " length:", len(arr))


    # Loop through SNPs
    out = []
    for geno_n in vcf_window_snps:
        if "," not in geno_n[3] and "," not in geno_n[4]:
            new_alleles_n = set_alleles(geno_n[3], geno_n[4])
            allele_n = {"0": new_alleles_n[0], "1": new_alleles_n[1]}
            hap = {"00": 0, "01": 0, "10": 0, "11": 0}
            for i in index:
                hap0 = geno[i][0]+geno_n[i][0]
                if hap0 in hap:
                    hap[hap0] += 1

                if len(geno[i]) == 3 and len(geno_n[i]) == 3:
                    hap1 = geno[i][2]+geno_n[i][2]
                    if hap1 in hap:
                        hap[hap1] += 1

            out_stats = LD_calcs(hap, allele, allele_n)
            # print("out_stats", out_stats)
            if out_stats != None:
                if ((r2_d == "r2" and out_stats["r2"] >= r2_d_threshold) or (r2_d == "d" and out_stats["D_prime"] >= r2_d_threshold)):
                    bp_n = geno_n[1]
                    rs_n = geno_n[2]
                    geno_n_chr_bp = "chr" + str(chromosome) + ":" + str(bp_n)
                    temp = [
                        rs_n, 
                        geno_n_chr_bp, 
                        out_stats['r2'], 
                        out_stats['D_prime']
                    ]
                    out.append(temp)
    # print("get_window_variants out", out)
    print("WINDOW SIZE AFTER THRESHOLD", len(out))
    return out

def set_alleles(a1, a2):
    if len(a1) == 1 and len(a2) == 1:
        a1_n = a1
        a2_n = a2
    elif len(a1) == 1 and len(a2) > 1:
        a1_n = "-"
        a2_n = a2[1:]
    elif len(a1) > 1 and len(a2) == 1:
        a1_n = a1[1:]
        a2_n = "-"
    elif len(a1) > 1 and len(a2) > 1:
        a1_n = a1[1:]
        a2_n = a2[1:]
    return(a1_n, a2_n)

# Create LDexpress function
def calculate_express(snplst, pop, request, web, tissue, r2_d, r2_d_threshold=0.1, p_threshold=0.1, window=500000):
    print("##### START LD EXPRESS CALCULATION #####")	
    print("raw snplst", snplst)
    print("raw pop", pop)
    print("raw request", request)
    print("raw web", web)
    print("raw tissue", tissue)
    print("raw r2_d", r2_d)
    print("raw r2_d_threshold", r2_d_threshold)
    print("raw p_threshold", p_threshold)
    print("raw window", window)

    start = timer()
    
    # SNP limit
    max_list = 5

    # Ensure tmp directory exists
    tmp_dir = "./tmp/"
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output for warnings and errors
    out_json = open(tmp_dir + "express" + str(request) + ".json", "w")
    output = {}

    # Validate window size is between 0 and 1,000,000
    if window < 0 or window > 1000000:
        output["error"] = "Window value must be a number between 0 and 1,000,000."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "", "")

    # Open SNPs file
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

    # Connect to Mongo snp database
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
        output["error"] = "dbSNP is currently unavailable. Please contact support."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "", "")

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
    pop_list = [x.decode('utf-8') for x in proc.stdout.readlines()]

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    tissue_ids = tissue.split("+")
    print("tissue_ids", tissue_ids)

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
            output["error"] = "Input list of RS numbers is empty"
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    # Generate warnings for query variants not found in dbsnp
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

    thinned_list = []

    print("##### FIND GWAS VARIANTS IN WINDOW #####")	
    # establish low/high window for each query snp
    # window = 500000 # -/+ 500Kb = 500,000Bp = 1Mb = 1,000,000 Bp total
    found = {}	
    # calculate and store LD info for all LD pairs	
    # ldPairs = []
    # # search query snp windows in gwas_catalog
    for snp_coord in snp_coords:
        # print("query snp_coord", snp_coord)
        (geno) = get_query_variant(snp_coord, pop_ids)
        # print("geno[0-4...]", ", ".join(geno[0:5]))
        new_alleles = set_alleles(geno[3], geno[4])
        allele = {"0": new_alleles[0], "1": new_alleles[1]}
        # # print("allele", allele)

        found[snp_coord[0]] = get_window_variants(db, snp_coord[0], snp_coord[1], snp_coord[2], window, pop_ids, geno, allele, r2_d, r2_d_threshold, p_threshold)

        # print("found", snp_coord[0], len(found[snp_coord[0]]))
        # if found[snp_coord[0]] is not None:
        #     thinned_list.append(snp_coord[0])
        #     # Calculate LD statistics of variant pairs ?in parallel?	
        #     for record in found[snp_coord[0]]:	
        #         ldPairs.append([snp_coord[0], str(snp_coord[1]), str(snp_coord[2]), "rs" + record["SNP_ID_CURRENT"], str(record["chromosome_grch37"]), str(record["position_grch37"])])	
        # else:	
        #     queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No variants found within window, variant removed."])
                
    print("found", found)

    # ldPairsUnique = [list(x) for x in set(tuple(x) for x in ldPairs)]	
    # # print("ldPairsUnique", ldPairsUnique)	
    # print("ldPairsUnique", len(ldPairsUnique))	
    # print("##### BEGIN MULTITHREADING LD CALCULATIONS #####")	
    # # start = timer()	
    # # leverage multiprocessing to calculate all LDpairs	
    # threads = 4	
    # splitLDPairsUnique = np.array_split(ldPairsUnique, threads)	
    # getLDStatsArgs = []	
    # for thread in range(threads):	
    #     getLDStatsArgs.append([splitLDPairsUnique[thread].tolist(), pop_ids, thread])	
    # # print("getLDStatsArgs", getLDStatsArgs)	
    # with Pool(processes=threads) as pool:	
    #     ldInfoSubsets = pool.map(get_ld_stats_sub, getLDStatsArgs)	
       	
    # # end = timer()	
    # # print("TIME ELAPSED:", str(end - start) + "(s)")	
    # print("##### END MULTITHREADING LD CALCULATIONS #####")	
    # print("ldInfoSubsets", json.dumps(ldInfoSubsets))	
    # print("ldInfoSubsets length ", len(ldInfoSubsets))	
    # merge all ldInfo Pool subsets into one ldInfo object	
    # ldInfo = {}	
    # for ldInfoSubset in ldInfoSubsets:	
    #     for key in ldInfoSubset.keys():	
    #         if key not in ldInfo.keys():	
    #             ldInfo[key] = {}	
    #             ldInfo[key] = ldInfoSubset[key]	
    #         else:	
    #             for subsetKey in ldInfoSubset[key].keys():	
    #                 ldInfo[key][subsetKey] = ldInfoSubset[key][subsetKey]	

    # print("ldInfo", json.dumps(ldInfo))
        	
    # for snp_coord in snp_coords:	
    #     # print("snp_coord", snp_coord)
    #     (matched_snps, window_problematic_snps) = get_gwas_fields(snp_coord[0], snp_coord[1], snp_coord[2], found[snp_coord[0]], pops, pop_ids, ldInfo, r2_d, r2_d_threshold)
        
    #     # windowWarnings += window_problematic_snps
    #     if (len(matched_snps) > 0):
    #         details[snp_coord[0]] = {	
    #             "aaData": matched_snps
    #         }
    #     else:
    #         # remove from thinned_list
    #         thinned_list.remove(snp_coord[0])
    #         queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No variants in LD found within window, variant removed."]) 

    details["queryWarnings"] = {
        "aaData": queryWarnings
    }

    # Check if thinned list is empty, if it is, display error
    # if len(thinned_list) < 1:
    #     output["error"] = "No variants in LD with GWAS Catalog."
    #     json_output = json.dumps(output, sort_keys=True, indent=2)
    #     print(json_output, file=out_json)
    #     out_json.close()
    #     return("", "", "")

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()
    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("##### LDEXPRESS COMPLETE #####")
    return (sanitized_query_snps, thinned_list, details)


def main():
    # snplst = sys.argv[1]
    snplst = "../tests/end-to-end/test-data/sample_LDexpress.txt"
    pop = "YRI+CEU"
    request = 8888
    web = False
    r2_d = "r2"
    r2_d_threshold = 0.1
    p_threshold = 0.1
    window = 50000
    tissue = "Adipose_Subcutaneous+Adipose_Visceral_Omentum"

    # Run function
    (sanitized_query_snps, thinned_list, details) = calculate_express(snplst, pop, request, web, tissue, r2_d, r2_d_threshold, p_threshold, window)
    print()
    print("##### FINAL LDEXPRESS.PY OUT - RETURN TO FRONTEND #####")
    print("query_snps", sanitized_query_snps)
    print("thinned_snps", thinned_list)
    print("details", json.dumps(details))
    # print("##### GET GTEx TISSUES #####")
    # print(get_ldexpress_tissues())

if __name__ == "__main__":
    main()