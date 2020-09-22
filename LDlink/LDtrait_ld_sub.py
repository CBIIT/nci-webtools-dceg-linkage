import yaml
import csv
import json
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
import requests

request = sys.argv[1]
subprocess_id = sys.argv[2]

# Set data directories using config.yml
with open('config.yml', 'r') as f:
    config = yaml.load(f)
env = config['env']
api_mongo_addr = config['api']['api_mongo_addr']
pop_dir = config['data']['pop_dir']
vcf_dir = config['data']['vcf_dir']
reg_dir = config['data']['reg_dir']
mongo_username = config['database']['mongo_user_readonly']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']

tmp_dir = "./tmp/"

# Get population ids
pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
ids = []
for i in range(len(pop_list)):
    ids.append(pop_list[i].strip())

pop_ids = list(set(ids))

variantPairs = []

with open(tmp_dir + 'trait_ld_' + str(subprocess_id) + '_' + str(request) + '.txt') as snpPairsFile: 
    lines = snpPairsFile.readlines() 
    for line in lines: 
        variantPairs.append(line.strip().split("\t"))

def get_ld_stats(variantPair, pop_ids):	
    # parse ld pair array parameter input
    snp1 = variantPair[0]
    snp1_coord = {
        "chromosome": variantPair[1], 
        "position": variantPair[2]
    }
    snp2 = variantPair[3]
    snp2_coord = {
        "chromosome": variantPair[4], 
        "position": variantPair[5]
    }

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
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "alleles": "NA",	
            "output": output	
        }	
    elif len(vcf1) > 1:	
        geno1 = []	
        for i in range(len(vcf1)):	
            if vcf1[i].strip().split()[2] == snp1:	
                geno1 = vcf1[i].strip().split()	
        if geno1 == []:	
            output["error"].append(snp1 + " is not in 1000G reference panel.")	
            return {	
                "r2": "NA",	
                "D_prime": "NA",	
                "p": "NA",	
                "alleles": "NA",	
                "output": output	
            }	
    else:	
        geno1 = vcf1[0].strip().split()	
    if geno1[2] != snp1:	
        output["warning"].append("Genomic position for query variant1 (" + snp1 + ") does not match RS number at 1000G position (chr" + geno1[0]+":"+geno1[1]+")")	
        snp1 = geno1[2]	
    if "," in geno1[3] or "," in geno1[4]:	
        output["error"].append(snp1 + " is not a biallelic variant.")	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "alleles": "NA",	
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
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "alleles": "NA",	
            "output": output	
        }	
    elif len(vcf2) > 1:	
        geno2 = []	
        for i in range(len(vcf2)):	
            if vcf2[i].strip().split()[2] == snp2:	
                geno2 = vcf2[i].strip().split()	
        if geno2 == []:	
            output["error"].append(snp2 + " is not in 1000G reference panel.")	
            return {	
                "r2": "NA",	
                "D_prime": "NA",	
                "p": "NA",	
                "alleles": "NA",	
                "output": output	
            }	
    else:	
        geno2 = vcf2[0].strip().split()	
    if geno2[2] != snp2:	
        output["warning"].append("Genomic position for query variant2 (" + snp2 + ") does not match RS number at 1000G position (chr" + geno2[0] + ":" + geno2[1] + ")")	
        snp2 = geno2[2]	
    if "," in geno2[3] or "," in geno2[4]:	
        output["error"].append(snp2 + " is not a biallelic variant.")	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "alleles": "NA",	
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

    if geno1[1] != vcf1_pos:	
        output["error"].append("VCF File does not match variant coordinates for SNP1.")	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "alleles": "NA",	
            "output": output	
        }	
    if geno2[1] != vcf2_pos:	
        output["error"].append("VCF File does not match variant coordinates for SNP2.")	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "p": "NA",	
            "alleles": "NA",	
            "output": output	
        }	

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

    # Sort haplotypes
    A = hap[sorted(hap)[0]]
    B = hap[sorted(hap)[1]]
    C = hap[sorted(hap)[2]]
    D = hap[sorted(hap)[3]]
    N = A + B + C + D
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
    else:
        output["error"].append("Variant MAF is 0.0, variant removed.")	
        return {	
            "r2": "NA",	
            "D_prime": "NA",	
            "alleles": "NA",	
            "output": output	
        }

    allele1 = str(sorted(hap)[0].split("_")[1])
    allele1_freq = str(round(float(A + C) / N, 3)) if N > float(A + C) else "NA"

    allele2 = str(sorted(hap)[1].split("_")[1])
    allele2_freq = str(round(float(B + D) / N, 3)) if N > float(B + D) else "NA"

    alleles = ", ".join(["=".join([allele1, allele1_freq]),"=".join([allele2, allele2_freq])])

    return {
        "r2": r2,
        "D_prime": D_prime,
        "alleles": alleles,
        "output": output
    }

def get_ld_pairs(pop_ids, variantPairs):
    ldInfoSubset = {}	
    for variantPair in variantPairs:
        ld = get_ld_stats(variantPair, pop_ids)		
        if variantPair[0] not in ldInfoSubset:		
            ldInfoSubset[variantPair[0]] = {}		
            ldInfoSubset[variantPair[0]][variantPair[3]] = ld		
        else:		
            ldInfoSubset[variantPair[0]][variantPair[3]] = ld
    return ldInfoSubset

out = get_ld_pairs(pop_ids, variantPairs)

print(json.dumps(out))