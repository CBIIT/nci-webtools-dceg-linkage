#!/usr/bin/env python3

import yaml
import json
import copy
import math
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

# Set data directories using config.yml	
with open('config.yml', 'r') as f:	
    config = yaml.load(f)	
dbsnp_version = config['data']['dbsnp_version']	
pop_dir = config['data']['pop_dir']	
vcf_dir = config['data']['vcf_dir']


# def pretty_print_json(obj):
#     return json.dumps(obj, sort_keys = True, indent = 4, separators = (',', ': '))

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

def expandSelectedPopulationGroups(pops):
    expandedPops = copy.deepcopy(pops)
    pop_groups = {
        "ALL": ["ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"],
        "AFR": ["YRI", "LWK", "GWD", "MSL", "ESN", "ASW", "ACB"],
        "AMR": ["MXL", "PUR", "CLM", "PEL"],
        "EAS": ["CHB", "JPT", "CHS", "CDX", "KHV"],
        "EUR": ["CEU", "TSI", "FIN", "GBR" , "IBS"],
        "SAS": ["GIH", "PJL", "BEB", "STU" , "ITU"]
    }
    if "ALL" in pops:
        expandedPops.remove("ALL")
        expandedPops = pop_groups["ALL"]
        expandedPops = list(set(expandedPops)) # unique elements
        return expandedPops
    else:
        if "AFR" in pops:
            expandedPops.remove("AFR")
            expandedPops = expandedPops + pop_groups["AFR"]
            expandedPops = list(set(expandedPops)) # unique elements
        if "AMR" in pops:
            expandedPops.remove("AMR")
            expandedPops = expandedPops + pop_groups["AMR"]
            expandedPops = list(set(expandedPops)) # unique elements
        if "EAS" in pops:
            expandedPops.remove("EAS")
            expandedPops = expandedPops + pop_groups["EAS"]
            expandedPops = list(set(expandedPops)) # unique elements
        if "EUR" in pops:
            expandedPops.remove("EUR")
            expandedPops = expandedPops + pop_groups["EUR"]
            expandedPops = list(set(expandedPops)) # unique elements
        if "SAS" in pops:
            expandedPops.remove("SAS")
            expandedPops = expandedPops + pop_groups["SAS"]
            expandedPops = list(set(expandedPops)) # unique elements
    return expandedPops

def get_ld_stats(snp1, snp1_coord,  snp2, snp2_coord, pops, pop_ids):	
    # errors/warnings encountered	
    output = {	
        "error": [],	
        "warning": []	
    }	
    # Extract 1000 Genomes phased genotypes	
    # SNP1	
    vcf_file1 = vcf_dir + snp1_coord['chromosome'] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"	
    tabix_snp1_offset = "tabix {0} {1}:{2}-{2} | grep -v -e END".format(	
        vcf_file1, snp1_coord['chromosome'], snp1_coord['position'])	
    proc1_offset = subprocess.Popen(	
        tabix_snp1_offset, shell=True, stdout=subprocess.PIPE)	
    vcf1_offset = [x.decode('utf-8') for x in proc1_offset.stdout.readlines()]	
    # SNP2	
    vcf_file2 = vcf_dir + snp2_coord['chromosome'] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"	
    tabix_snp2_offset = "tabix {0} {1}:{2}-{2} | grep -v -e END".format(	
        vcf_file2, snp2_coord['chromosome'], snp2_coord['position'])	
    proc2_offset = subprocess.Popen(	
        tabix_snp2_offset, shell=True, stdout=subprocess.PIPE)	
    vcf2_offset = [x.decode('utf-8') for x in proc2_offset.stdout.readlines()]	
    vcf1_pos = snp1_coord['position']	
    vcf2_pos = snp2_coord['position']	
    vcf1 = vcf1_offset	
    vcf2 = vcf2_offset	
    # SNP1	
    if len(vcf1) == 0:	
        output["error"].append(snp1 + " is not in 1000G reference panel.")	
        # return(json.dumps(output, sort_keys=True, indent=2))	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }	
    elif len(vcf1) > 1:	
        geno1 = []	
        for i in range(len(vcf1)):	
            if vcf1[i].strip().split()[2] == snp1:	
                geno1 = vcf1[i].strip().split()	
        if geno1 == []:	
            output["error"].append(snp1 + " is not in 1000G reference panel.")	
            # return(json.dumps(output, sort_keys=True, indent=2))	
            return {	
                "r2": "NA",	
                "D_prime": "NA",	
                "p": "NA",	
                "corr_alleles": "NA",	
                "output": output	
            }	
    else:	
        geno1 = vcf1[0].strip().split()	
    if geno1[2] != snp1:	
        output["warning"].append("Genomic position for query variant1 (" + snp1 + ") does not match RS number at 1000G position (chr" + geno1[0]+":"+geno1[1]+")")	
        snp1 = geno1[2]	
    if "," in geno1[3] or "," in geno1[4]:	
        output["error"].append(snp1 + " is not a biallelic variant.")	
        # return(json.dumps(output, sort_keys=True, indent=2))	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }	
    if len(geno1[3]) == 1 and len(geno1[4]) == 1:	
        snp1_a1 = geno1[3]	
        snp1_a2 = geno1[4]	
    elif len(geno1[3]) == 1 and len(geno1[4]) > 1:	
        snp1_a1 = "-"	
        snp1_a2 = geno1[4][1:]	
    elif len(geno1[3]) > 1 and len(geno1[4]) == 1:	
        snp1_a1 = geno1[3][1:]	
        snp1_a2 = "-"	
    elif len(geno1[3]) > 1 and len(geno1[4]) > 1:	
        snp1_a1 = geno1[3][1:]	
        snp1_a2 = geno1[4][1:]	
    allele1 = {	
        "0|0": [snp1_a1, snp1_a1], 	
        "0|1": [snp1_a1, snp1_a2], 	
        "1|0": [snp1_a2, snp1_a1], 	
        "1|1": [snp1_a2, snp1_a2], 	
        "0": [snp1_a1, "."], 	
        "1": [snp1_a2, "."], 	
        "./.": [".", "."], 	
        ".": [".", "."]	
    }	
    # SNP2	
    if len(vcf2) == 0:	
        output["error"].append(snp2 + " is not in 1000G reference panel.")	
        # return(json.dumps(output, sort_keys=True, indent=2))	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }	
    elif len(vcf2) > 1:	
        geno2 = []	
        for i in range(len(vcf2)):	
            if vcf2[i].strip().split()[2] == snp2:	
                geno2 = vcf2[i].strip().split()	
        if geno2 == []:	
            output["error"].append(snp2 + " is not in 1000G reference panel.")	
            # return(json.dumps(output, sort_keys=True, indent=2))	
            return {	
                "r2": "NA",	
                "D_prime": "NA",	
                "p": "NA",	
                "corr_alleles": "NA",	
                "output": output	
            }	
    else:	
        geno2 = vcf2[0].strip().split()	
    if geno2[2] != snp2:	
        output["warning"].append("Genomic position for query variant2 (" + snp2 + ") does not match RS number at 1000G position (chr" + geno2[0] + ":" + geno2[1] + ")")	
        snp2 = geno2[2]	
    if "," in geno2[3] or "," in geno2[4]:	
        output["error"].append(snp2 + " is not a biallelic variant.")	
        # return(json.dumps(output, sort_keys=True, indent=2))	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }	
    if len(geno2[3]) == 1 and len(geno2[4]) == 1:	
        snp2_a1 = geno2[3]	
        snp2_a2 = geno2[4]	
    elif len(geno2[3]) == 1 and len(geno2[4]) > 1:	
        snp2_a1 = "-"	
        snp2_a2 = geno2[4][1:]	
    elif len(geno2[3]) > 1 and len(geno2[4]) == 1:	
        snp2_a1 = geno2[3][1:]	
        snp2_a2 = "-"	
    elif len(geno2[3]) > 1 and len(geno2[4]) > 1:	
        snp2_a1 = geno2[3][1:]	
        snp2_a2 = geno2[4][1:]	
    allele2 = {	
        "0|0": [snp2_a1, snp2_a1], 	
        "0|1": [snp2_a1, snp2_a2], 	
        "1|0": [snp2_a2, snp2_a1], 	
        "1|1": [snp2_a2, snp2_a2], 	
        "0": [snp2_a1, "."], 	
        "1": [snp2_a2, "."], 	
        "./.": [".", "."], 	
        ".": [".", "."]	
    }	
    # print(allele1)	
    # print(allele2)	
    # print("geno1[1]", geno1[1], "vcf1_pos", vcf1_pos)	
    # print("geno2[1]", geno2[1], "vcf2_pos", vcf2_pos)	
    if geno1[1] != vcf1_pos:	
        output["error"].append("VCF File does not match variant coordinates for SNP1.")	
        # return(json.dumps(output, sort_keys=True, indent=2))	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }	
    if geno2[1] != vcf2_pos:	
        output["error"].append("VCF File does not match variant coordinates for SNP2.")	
        # return(json.dumps(output, sort_keys=True, indent=2))	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }	
    # print("output", output)	
    # Get headers	
    tabix_snp1_h = "tabix -H {0} | grep CHROM".format(vcf_file1)	
    proc1_h = subprocess.Popen(	
        tabix_snp1_h, shell=True, stdout=subprocess.PIPE)	
    head1 = [x.decode('utf-8') for x in proc1_h.stdout.readlines()][0].strip().split()	
    tabix_snp2_h = "tabix -H {0} | grep CHROM".format(vcf_file2)	
    proc2_h = subprocess.Popen(	
        tabix_snp2_h, shell=True, stdout=subprocess.PIPE)	
    head2 = [x.decode('utf-8') for x in proc2_h.stdout.readlines()][0].strip().split()	
    # Combine phased genotypes	
    geno = {}	
    for i in range(9, len(head1)):	
        geno[head1[i]] = [allele1[geno1[i]], ".."]	
    for i in range(9, len(head2)):	
        if head2[i] in geno:	
            geno[head2[i]][1] = allele2[geno2[i]]	
    # print("geno", geno)	
    # Extract haplotypes	
    hap = {}	
    for ind in pop_ids:	
        if ind in geno:	
            hap1 = geno[ind][0][0] + "_" + geno[ind][1][0]	
            hap2 = geno[ind][0][1] + "_" + geno[ind][1][1]	
            if hap1 in hap:	
                hap[hap1] += 1	
            else:	
                hap[hap1] = 1	
            if hap2 in hap:	
                hap[hap2] += 1	
            else:	
                hap[hap2] = 1	
    # Remove missing haplotypes	
    keys = list(hap.keys())	
    for key in keys:	
        if "." in key:	
            hap.pop(key, None)	
    # Check all haplotypes are present	
    if len(hap) != 4:	
        snp1_a = [snp1_a1, snp1_a2]	
        snp2_a = [snp2_a1, snp2_a2]	
        haps = [snp1_a[0] + "_" + snp2_a[0], snp1_a[0] + "_" + snp2_a[1],	
                snp1_a[1] + "_" + snp2_a[0], snp1_a[1] + "_" + snp2_a[1]]	
        for i in haps:	
            if i not in hap:	
                hap[i] = 0	
    # print("hap", hap)	
    # Sort haplotypes	
    A = hap[sorted(hap)[0]]	
    B = hap[sorted(hap)[1]]	
    C = hap[sorted(hap)[2]]	
    D = hap[sorted(hap)[3]]	
    # N = A + B + C + D	
    # tmax = max(A, B, C, D)	
    hap1 = sorted(hap, key=hap.get, reverse=True)[0]	
    hap2 = sorted(hap, key=hap.get, reverse=True)[1]	
    # hap3 = sorted(hap, key=hap.get, reverse=True)[2]	
    # hap4 = sorted(hap, key=hap.get, reverse=True)[3]	
    delta = float(A * D - B * C)	
    Ms = float((A + C) * (B + D) * (A + B) * (C + D))	
    # print("Ms=", Ms)	
    if Ms != 0:	
        # D prime	
        if delta < 0:	
            D_prime = abs(delta / min((A + C) * (A + B), (B + D) * (C + D)))	
        else:	
            D_prime = abs(delta / min((A + C) * (C + D), (A + B) * (B + D)))	
        # R2	
        r2 = (delta**2) / Ms	
        # P-value	
        num = (A + B + C + D) * (A * D - B * C)**2	
        denom = Ms	
        chisq = num / denom	
        p = 2 * (1 - (0.5 * (1 + math.erf(chisq**0.5 / 2**0.5))))	
    else:	
        output["error"].append("Variant MAF is 0.0, variant removed.")	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "corr_alleles": "NA",	
            "output": output	
        }		

    Ac=hap[sorted(hap)[0]]	
    Bc=hap[sorted(hap)[1]]	
    Cc=hap[sorted(hap)[2]]	
    Dc=hap[sorted(hap)[3]]	
    corr_alleles = "NA"	
    if ((Bc*Cc) != 0) and ((Ac*Dc) / (Bc*Cc) > 1):	
        corr1 = sorted(hap)[0].split("_")[0] + "=" + sorted(hap)[0].split("_")[1]	
        corr2 = sorted(hap)[3].split("_")[0] + "=" + sorted(hap)[3].split("_")[1]	
        corr_alleles = str(corr1) + ", " + str(corr2)	
    else:	
        corr1 = sorted(hap)[1].split("_")[0] + "=" + sorted(hap)[1].split("_")[1]	
        corr2 = sorted(hap)[2].split("_")[0] + "=" + sorted(hap)[2].split("_")[1]	
        corr_alleles = str(corr1) + ", " + str(corr2)	

    print(snp1, " ", snp1_coord, " ", snp2, " ", snp2_coord, " ", pops, " ", [r2, D_prime, p, output])	
    # return(r2, D_prime, p, corr_alleles, output)	

    return {	
        "r2": r2,	
        "D_prime": D_prime,	
        "p": p,	
        "corr_alleles": corr_alleles,	
        "output": output	
    }	

def get_gwas_fields(query_snp, query_snp_chr, query_snp_pos, found, pops, pop_ids, ldInfo, r2_d, r2_d_threshold):	    
    matched_snps = []
    problematic_snps = []
    for record in found:
        ld = ldInfo[query_snp]["rs" + record["SNP_ID_CURRENT"]]
        if (ld["r2"] != "NA" or ld["D_prime"] != "NA"):
            if ((r2_d == "r2" and ld["r2"] >= r2_d_threshold) or (r2_d == "d" and ld["D_prime"] >= r2_d_threshold)):
                matched_record = []
                # Query SNP
                # matched_record.append(query_snp)
                # GWAS Trait
                matched_record.append(record["DISEASE/TRAIT"]) 
                # RS Number
                matched_record.append("rs" + record["SNP_ID_CURRENT"]) 
                # Position
                matched_record.append("chr" + str(record["chromosome_grch37"]) + ":" + str(record["position_grch37"]))
                # Alleles	
                matched_record.append(ld["corr_alleles"])	
                # R2	
                matched_record.append(ld["r2"])	
                # D'	
                matched_record.append(ld["D_prime"])	
                # LDpair (Link)	
                matched_record.append([query_snp, "rs" + record["SNP_ID_CURRENT"], "%2B".join(expandSelectedPopulationGroups(pops))])
                # Risk Allele
                matched_record.append(record["RISK ALLELE FREQUENCY"] if ("RISK ALLELE FREQUENCY" in record and len(record["RISK ALLELE FREQUENCY"]) > 0) else "NA")
                # Effect Size (95% CI)
                matched_record.append(record["OR or BETA"] if ("OR or BETA" in record and len(record["OR or BETA"]) > 0) else "NA")
                # P-value
                matched_record.append(ld["p"])
                # GWAS Catalog (Link)
                matched_record.append("rs" + record["SNP_ID_CURRENT"])
                # Details
                # matched_record.append("Variant found in GWAS catalog within window.")
                print("matched_record", matched_record)
                matched_snps.append(matched_record)
            else: 
                if (r2_d == "r2"):
                    problematic_record = [query_snp, "rs" + record["SNP_ID_CURRENT"], "NA", "NA", "R2 value (" + str(ld["r2"]) + ") below threshold (" + str(r2_d_threshold) + ")"]
                    problematic_snps.append(problematic_record)
                else:
                    problematic_record = [query_snp, "rs" + record["SNP_ID_CURRENT"], "NA", "NA", "D' value (" + str(ld["D_prime"]) + ") below threshold. (" + str(r2_d_threshold) + ")"]
                    problematic_snps.append(problematic_record)
        else:
            problematic_record = [query_snp, "rs" + record["SNP_ID_CURRENT"], "NA", "NA", " ".join(ld["output"]["error"])]
            problematic_snps.append(problematic_record)
    return (matched_snps, problematic_snps)

# Create LDtrait function
# def calculate_trait(snplst, pop, request, web, r2_d, r2_d_threshold=0.1):
def calculate_trait(snplst, pop, request, web, r2_d, r2_d_threshold=0.1):

    # snp limit
    max_list = 250

    # # Set data directories using config.yml
    # with open('config.yml', 'r') as f:
    #     config = yaml.load(f)
    # dbsnp_version = config['data']['dbsnp_version']
    # pop_dir = config['data']['pop_dir']
    # vcf_dir = config['data']['vcf_dir']

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
    pop_list = [x.decode('utf-8') for x in proc.stdout.readlines()]

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
                    warnings.append([snp_i[0], "NA", "NA", "NA", "Variant not found in dbSNP" + dbsnp_version + ", variant removed."])
            else:
                # Generate warning if query variant is not a genomic position or rs number
                warn.append(snp_i[0])
                warnings.append([snp_i[0], "NA", "NA", "NA", "Not a valid SNP, query removed."])
        else:
            # Generate error for empty query variant
            output["error"] = "Input list of RS numbers is empty"
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    # print("warn", warn)
    # details["warnings"] = {
    #     "aaData": warnings
    # }

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
    window = 2000000 # 2Mb = 2,000,000 Bp
    found = []	
    # calculate and store LD info for all LD pairs	
    ldPairs = []
    # search query snp windows in gwas_catalog
    for snp_coord in snp_coords:
        # print(snp_coord)
        found = get_window_variants(db, snp_coord[1], snp_coord[2], window)
        # print("found: " + str(len(found)))
        if found is not None:
            thinned_list.append(snp_coord[0])
            # Calculate LD statistics of variant pairs ?in parallel?	
            for record in found:	
                ldPairs.append([snp_coord[0], str(snp_coord[1]), str(snp_coord[2]), "rs" + record["SNP_ID_CURRENT"], str(record["chromosome_grch37"]), str(record["position_grch37"])])	
        # else:	
            # out_json["not_found"].append(query_snp["rsnum"])	
            
    ldPairsUnique = [list(x) for x in set(tuple(x) for x in ldPairs)]	
    # print("ldPairsUnique", ldPairsUnique)	
    # print("ldPairsUnique", len(ldPairsUnique))	
    ldInfo = {}	
    for variantPair in ldPairsUnique:	
        # print("variantPair:", variantPair)	
        ld = get_ld_stats(variantPair[0], {"chromosome": variantPair[1], "position": variantPair[2]}, variantPair[3],{"chromosome": variantPair[4], "position": variantPair[5]}, pops, pop_ids)	
        # print("ld", ld)	
        # ld = {	
        #     "r2": "NA",	
        #     "D_prime": "NA",	
        #     "p": "NA",	
        #     "output": []	
        # }	
        # store LD calculation results in a object	
        if variantPair[0] not in ldInfo:	
            ldInfo[variantPair[0]] = {}	
            ldInfo[variantPair[0]][variantPair[3]] = ld	
        else:	
            ldInfo[variantPair[0]][variantPair[3]] = ld	
        	
    # print("ldInfo", ldInfo)	
    for snp_coord in snp_coords:	
        (matched_snps, problematic_snps) = get_gwas_fields(snp_coord[0], snp_coord[1], snp_coord[2], found, pops, pop_ids, ldInfo)	
        details[snp_coord[0]] = {	
            "aaData": matched_snps
        }
        warnings += problematic_snps

    details["warnings"] = {
        "aaData": warnings
    }

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()
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
    (sanitized_query_snps, thinned_list, details) = calculate_trait(snplst, pop, request, web, r2_d, r2_d_threshold)
    print("query_snps", sanitized_query_snps)
    print("thinned_snps", thinned_list)
    print("details", json.dumps(details))

if __name__ == "__main__":
    main()