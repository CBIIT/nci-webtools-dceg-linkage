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

def get_ldexpress_tissues(web):
    try:
        with open('config.ini', 'r') as c:
            config = yaml.load(c)
        env = config['env']
        api_mongo_addr = config['api']['api_mongo_addr']
        mongo_username = config['database']['mongo_user_readonly']
        mongo_password = config['database']['mongo_password']
        mongo_port = config['database']['mongo_port']

        # Connect to Mongo snp database
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

def get_query_variant(snp_coord, pop_ids):
    queryVariantWarnings = []
    # Extract query SNP phased genotypes
    vcf_query_snp_file = vcf_dir + snp_coord[1] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    tabix_query_snp_h = "tabix -H {0} | grep CHROM".format(vcf_query_snp_file)
    proc_query_snp_h = subprocess.Popen(tabix_query_snp_h, shell=True, stdout=subprocess.PIPE)
    head = [x.decode('utf-8') for x in proc_query_snp_h.stdout.readlines()][0].strip().split()
    # print("head length", len(head))

    tabix_query_snp = "tabix {0} {1}:{2}-{2} | grep -v -e END".format(vcf_query_snp_file, snp_coord[1], snp_coord[2])
    proc_query_snp = subprocess.Popen(tabix_query_snp, shell=True, stdout=subprocess.PIPE)
    tabix_query_snp_out = [x.decode('utf-8') for x in proc_query_snp.stdout.readlines()]
    # print("tabix_query_snp_out length", len(tabix_query_snp_out))
    # Validate error
    if len(tabix_query_snp_out) == 0:
        # print("ERROR", "len(tabix_query_snp_out) == 0")
        # handle error: snp + " is not in 1000G reference panel."
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not in 1000G reference panel."])
    elif len(tabix_query_snp_out) > 1:
        geno = []
        for i in range(len(tabix_query_snp_out)):
            if tabix_query_snp_out[i].strip().split()[2] == snp_coord[0]:
                geno = tabix_query_snp_out[i].strip().split()
        if geno == []:
            # print("ERROR", "geno == []")
            # handle error: snp + " is not in 1000G reference panel."
            queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not in 1000G reference panel."])
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

def getGTExTissueAPI(snp, tissue_ids):
    PAYLOAD = {
        "format" : "json",
        "snpId": snp,
        "tissueSiteDetailId": ",".join(tissue_ids),
        "datasetId": "gtex_v8"
    }
    REQUEST_URL = "https://gtexportal.org/rest/v1/association/singleTissueEqtl"
    r = requests.get(REQUEST_URL, params=PAYLOAD)
    # print(json.loads(r.text))
    return (json.loads(r.text))

def getGTExTissueMongoDB(db, chromosome, position, tissue_ids):
    if "gtex_tissue_eqtl" in db.list_collection_names():
        documents = list(db.gtex_tissue_eqtl.find({
            "chr_b37": str(chromosome), 
            "variant_pos_b37": str(position),
            "tissueSiteDetailId": str(tissue_ids[0])
        }))
        # print("documents", documents)
        tissues = {
            "singleTissueEqtl": documents
        }
        # json_output = json.dumps(tissues, default=json_util.default, sort_keys=True, indent=2)
        return tissues
    else:
        return None

def chunkWindow(pos, window, threads):
    if (pos - window <= 0):
        minPos = 0
    else:
        minPos = pos - window
    maxPos = pos + window
    windowRange = maxPos - minPos
    chunks = []
    newMin = minPos
    newMax = 0
    for _ in range(threads):
        newMax = newMin + (windowRange / threads)
        chunks.append([math.ceil(newMin), math.ceil(newMax)])
        newMin = newMax
    return chunks

def get_window_variants(snp, chromosome, windowMinPos, windowMaxPos, pop_ids, geno, allele, r2_d, r2_d_threshold):
    # Get VCF region
    vcf_file = vcf_dir + chromosome + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    tabix_snp = "tabix -fh {0} {1}:{2}-{3} | grep -v -e END".format(
        vcf_file, chromosome, windowMinPos, windowMaxPos)
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
    print(str(snp) + " vcf_window_snps RAW LENGTH", len(vcf_window_snps))
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
                    out.append([rs_n, chromosome, bp_n, out_stats["r2"], out_stats["D_prime"]])
                    
    return out

def get_window_variants_sub(threadCommandArgs):
    windowChunkRange = threadCommandArgs[0]
    thread = threadCommandArgs[1]	
    snp = threadCommandArgs[2]
    chromosome = threadCommandArgs[3]		
    pop_ids = threadCommandArgs[4]
    geno = threadCommandArgs[5]
    allele = threadCommandArgs[6]
    r2_d = threadCommandArgs[7]
    r2_d_threshold = threadCommandArgs[8]
    print("thread " + str(thread) + " kicked")	
    print("windowChunkRange", windowChunkRange)
    return get_window_variants(snp, chromosome, windowChunkRange[0], windowChunkRange[1], pop_ids, geno, allele, r2_d, r2_d_threshold)

def get_tissues(db, windowSNPs, p_threshold, tissue_ids):
    gtexQueryRequestCount = 0
    gtexQueryReturnCount = 0
    out = []
    for snp in windowSNPs:
        rs_n = snp[0]
        chromosome = snp[1]
        position = snp[2]
        r2 = snp[3]
        D_prime = snp[4]
        geno_n_chr_bp = "chr" + str(chromosome) + ":" + str(position)
        gtexQueryRequestCount += 1
        ###### RETRIEVE GTEX TISSUE INFO FROM API ######
        (tissue_stats) = getGTExTissueAPI(rs_n, tissue_ids)
        ###### RETRIEVE GTEX TISSUE INFO FROM MONGODB ######
        # (tissue_stats) = getGTExTissueMongoDB(db, chromosome, position, tissue_ids)
        if tissue_stats != None and len(tissue_stats['singleTissueEqtl']) > 0:
            gtexQueryReturnCount += 1
            for tissue_obj in tissue_stats['singleTissueEqtl']:
                if float(tissue_obj['pValue']) < float(p_threshold):
                # if float(tissue_obj['pval_nominal']) < float(p_threshold):
                    temp = [
                        rs_n, 
                        geno_n_chr_bp, 
                        r2, 
                        D_prime,
                        tissue_obj['geneSymbol'],
                        # "NA",
                        tissue_obj['gencodeId'],
                        # tissue_obj['gene_id'],
                        tissue_obj['tissueSiteDetailId'],
                        tissue_obj['nes'],
                        # tissue_obj['slope'],
                        tissue_obj['pValue'],
                        # tissue_obj['pval_nominal'],
                        rs_n
                    ]
                    out.append(temp)
    print("get_tissues out length", len(out))
    print("# of gtex queries made (gtexQueryRequestCount)", gtexQueryRequestCount)
    print("# of gtex queries returned (gtexQueryReturnCount)", gtexQueryReturnCount)
    return out

def get_tissues_sub(threadCommandArgs):
    windowSNPs = threadCommandArgs[0]
    thread = threadCommandArgs[1]
    p_threshold = threadCommandArgs[2]
    tissue_ids = threadCommandArgs[3]
    web = threadCommandArgs[4]
    print("thread " + str(thread) + " kicked")	
    print("thread executing", len(windowSNPs), "gtex queries...")
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
    return get_tissues(db, windowSNPs, p_threshold, tissue_ids)

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
    max_list = 20

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
    for snp_coord in snp_coords:
        (geno, queryVariantWarnings) = get_query_variant(snp_coord, pop_ids)
        new_alleles = set_alleles(geno[3], geno[4])
        allele = {"0": new_alleles[0], "1": new_alleles[1]}
        ###### SPLIT TASK UP INTO # PARALLEL THREADS ######

        # find query window snps via tabix, calculate LD and apply R2/D' thresholds
        windowChunkRanges = chunkWindow(snp_coord[2], window, ldexpress_threads)
        # print("windowChunkRanges", windowChunkRanges)
        getWindowVariantsArgs = []	
        for thread in range(ldexpress_threads):	
            getWindowVariantsArgs.append([windowChunkRanges[thread], thread, snp_coord[0], snp_coord[1], pop_ids, geno, allele, r2_d, r2_d_threshold])	
        with Pool(processes=ldexpress_threads) as pool:	
            windowLDSubsets = pool.map(get_window_variants_sub, getWindowVariantsArgs)
        # flatten pooled ld window results
        windowLDSubsetsFlat = [val for sublist in windowLDSubsets for val in sublist]
        print("windowLDSubsetsFlat length", len(windowLDSubsetsFlat))

        # find gtex tissues for window snps via mongodb, apply p-value threshold
        windowLDSubsetsChunks = np.array_split(windowLDSubsetsFlat, ldexpress_threads)
        getTissuesArgs = []	
        for thread in range(ldexpress_threads):	
            getTissuesArgs.append([windowLDSubsetsChunks[thread].tolist(), thread, p_threshold, tissue_ids, web])	
        with Pool(processes=ldexpress_threads) as pool:	
            tissueResultsSubsets = pool.map(get_tissues_sub, getTissuesArgs)	

        # flatten tissue results
        matched_snps = [val for sublist in tissueResultsSubsets for val in sublist]
        print("matched_snps length", len(matched_snps))

        print("FINAL # RESULTS FOR", snp_coord[0], len(matched_snps))
        if (len(matched_snps) > 0):
            details[snp_coord[0]] = {	
                "aaData": matched_snps
            }
            # add snp to thinned_list
            thinned_list.append(snp_coord[0])
        else:
            queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No variants in LD found within window, variant removed."]) 
        
    details["queryWarnings"] = {
        "aaData": queryVariantWarnings + queryWarnings
    }

    # Check if thinned list is empty, if it is, display error
    if len(thinned_list) < 1:
        output["error"] = "No variants in LD with GTEx."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "", "")

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
    window = 500000
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