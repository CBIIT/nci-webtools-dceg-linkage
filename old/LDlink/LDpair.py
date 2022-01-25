#!/usr/bin/env python3
import yaml
import json
import math
import os
from pymongo import MongoClient
from bson import json_util, ObjectId
import boto3
import botocore
import subprocess
import sys
import time
import re
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars, get_rsnum

# Create LDpair function

def calculate_pair(snp_pairs, pop, web, genome_build, request):

    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    env = config['env']
    api_mongo_addr = config['api']['api_mongo_addr']
    dbsnp_version = config['data']['dbsnp_version']
    population_samples_dir = config['data']['population_samples_dir']
    data_dir = config['data']['data_dir']
    tmp_dir = config['data']['tmp_dir']
    genotypes_dir = config['data']['genotypes_dir']
    aws_info = config['aws']
    mongo_username = config['database']['mongo_user_readonly']
    mongo_password = config['database']['mongo_password']
    mongo_port = config['database']['mongo_port']

    export_s3_keys = retrieveAWSCredentials()

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    output_list = []

    snp_pair_limit = 10
    
    # Throw max SNP pairs error message
    if len(snp_pairs) > snp_pair_limit:
        error_out = [{
            "error": "Maximum SNP pair list is " + str(snp_pair_limit) + " pairs. Your list contains " + str(len(snp_pairs)) + " pairs."
        }]
        return(json.dumps(error_out, sort_keys=True, indent=2))

    # Validate genome build param
    # print("genome_build " + genome_build)
    if genome_build not in genome_build_vars['vars']:
        error_out = [{
            "error": "Invalid genome build. Please specify either " + ", ".join(genome_build_vars['vars']) + "."
        }]
        return(json.dumps(error_out, sort_keys=True, indent=2))

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(data_dir + population_samples_dir + pop_i + ".txt")
        else:
            error_out = [{
                "error": pop_i + " is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            }]
            return(json.dumps(error_out, sort_keys=True, indent=2))

    get_pops = "cat " + " ".join(pop_dirs)
    pop_list = [x.decode('utf-8') for x in subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    # Connect to Mongo snp database
    if env == 'local' or env == 'docker':
        mongo_host = api_mongo_addr
    else: 
        mongo_host = 'localhost'
    if web:
        client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
    else:
        if env == 'local' or env == 'docker':
            client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
        else:
            client = MongoClient('localhost', mongo_port)
    db = client["LDLink"]

    def get_coords(db, rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coord_rsid(db, snp):
        if snp[0:2] == "rs":
            return snp
        else:
            snp_info_lst = get_rsnum(db, snp, genome_build)
            print("snp_info_lst")
            print(snp_info_lst)
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
                            ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                        else:
                            output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                    elif len(ref_variants) == 0 and len(snp_info_lst) > 1:
                        var_id = "rs" + snp_info_lst[0]['id']
                        if "warning" in output:
                            output["warning"] = output["warning"] + \
                            ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                        else:
                            output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                    else:
                        var_id = "rs" + ref_variants[0]
                    return var_id
                elif len(snp_info_lst) == 1:
                    var_id = "rs" + snp_info_lst[0]['id']
                    return var_id
                else:
                    return snp
            else:
                return snp
        return snp

    if len(snp_pairs) < 1:
        output = {}
        output["error"] = "Missing at least 1 SNP pair input."
        output_list.append(output)

    for pair in snp_pairs:
        output = {}
        output["pair"] = pair

        if len(pair) < 2 or len(pair) > 2 or len(pair[0]) < 3 or len(pair[1]) < 3:
            output["error"] = "Missing or additional SNPs in pair."
            output_list.append(output)
            continue

        # trim any whitespace
        snp1 = pair[0].lower().strip()
        snp2 = pair[1].lower().strip()

        # Find RS numbers in snp database
        # SNP1
        if re.compile(r'rs\d+', re.IGNORECASE).match(snp1) is None and re.compile(r'chr\d+:\d+', re.IGNORECASE).match(snp1) is None and re.compile(r'chr[X|Y]:\d+', re.IGNORECASE).match(snp1) is None:
            output["error"] = snp1 + " is not a valid SNP."
            output_list.append(output)
            continue
        snp1 = replace_coord_rsid(db, snp1)
        snp1_coord = get_coords(db, snp1)
        if snp1_coord == None or snp1_coord[genome_build_vars[genome_build]['position']] == "NA":
            output["error"] = snp1 + " is not in dbSNP build " + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ")."
            output_list.append(output)
            continue

        # SNP2
        if re.compile(r'rs\d+', re.IGNORECASE).match(snp2) is None and re.compile(r'chr\d+:\d+', re.IGNORECASE).match(snp2) is None and re.compile(r'chr[X|Y]:\d+', re.IGNORECASE).match(snp2) is None:
            output["error"] = snp1 + " is not a valid SNP."
            output_list.append(output)
            continue
        snp2 = replace_coord_rsid(db, snp2)
        snp2_coord = get_coords(db, snp2)
        if snp2_coord == None or snp2_coord[genome_build_vars[genome_build]['position']] == "NA":
            output["error"] = snp2 + " is not in dbSNP build " + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ")."
            output_list.append(output)
            continue

        # Check if SNPs are on the same chromosome
        if snp1_coord['chromosome'] != snp2_coord['chromosome']:
            output["warning"] = snp1 + " and " + \
                snp2 + " are on different chromosomes"

        # Check if input SNPs are on chromosome Y while genome build == grch38
        # SNP1
        if snp1_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
            output["error"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp1_coord['id'] + " - chr" + snp1_coord['chromosome'] + ":" + snp1_coord[genome_build_vars[genome_build]['position']] + ")"
            output_list.append(output) 
            continue

        # SNP2
        if snp2_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
            output["error"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp2_coord['id'] + " - chr" + snp2_coord['chromosome'] + ":" + snp2_coord[genome_build_vars[genome_build]['position']] + ")"
            output_list.append(output)
            continue

        # Extract 1000 Genomes phased genotypes

        # SNP1
        vcf_filePath1 = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % snp1_coord['chromosome'])
        vcf_file1 = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath1)

        checkS3File(aws_info, config['aws']['bucket'], vcf_filePath1)

        tabix_snp1_offset = export_s3_keys + " cd {3}; tabix -D {0} {1}:{2}-{2} | grep -v -e END".format(
            vcf_file1, genome_build_vars[genome_build]['1000G_chr_prefix'] + snp1_coord['chromosome'], snp1_coord[genome_build_vars[genome_build]['position']], data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
        vcf1_offset = [x.decode('utf-8') for x in subprocess.Popen(tabix_snp1_offset, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

        # SNP2
        vcf_filePath2 = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % snp2_coord['chromosome'])
        vcf_file2 = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath2)

        checkS3File(aws_info, config['aws']['bucket'], vcf_filePath2)

        tabix_snp2_offset = export_s3_keys + " cd {3}; tabix -D {0} {1}:{2}-{2} | grep -v -e END".format(
            vcf_file2, genome_build_vars[genome_build]['1000G_chr_prefix'] + snp2_coord['chromosome'], snp2_coord[genome_build_vars[genome_build]['position']], data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
        vcf2_offset = [x.decode('utf-8') for x in subprocess.Popen(tabix_snp2_offset, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

        vcf1_pos = snp1_coord[genome_build_vars[genome_build]['position']]
        vcf2_pos = snp2_coord[genome_build_vars[genome_build]['position']]
        vcf1 = vcf1_offset
        vcf2 = vcf2_offset

        # Import SNP VCF files

        # SNP1
        if len(vcf1) == 0:
            output["error"] = snp1 + " is not in 1000G reference panel."
            output_list.append(output)
            continue

        elif len(vcf1) > 1:
            geno1 = []
            for i in range(len(vcf1)):
                if vcf1[i].strip().split()[2] == snp1:
                    geno1 = vcf1[i].strip().split()
                    geno1[0] = geno1[0].lstrip('chr')
            if geno1 == []:
                output["error"] = snp1 + " is not in 1000G reference panel."
                output_list.append(output)
                continue

        else:
            geno1 = vcf1[0].strip().split()
            geno1[0] = geno1[0].lstrip('chr')

        if geno1[2] != snp1 and snp1[0:2] == "rs" and "rs" in geno1[2]:
            if "warning" in output:
                output["warning"] = output["warning"] + \
                    ". Genomic position for query variant1 (" + snp1 + \
                    ") does not match RS number at 1000G position (chr" + \
                    geno1[0]+":"+geno1[1]+" = "+geno1[2]+")"
            else:
                output["warning"] = "Genomic position for query variant1 (" + snp1 + \
                    ") does not match RS number at 1000G position (chr" + \
                    geno1[0]+":"+geno1[1]+" = "+geno1[2]+")"
            snp1 = geno1[2]

        if "," in geno1[3] or "," in geno1[4]:
            output["error"] = snp1 + " is not a biallelic variant."
            output_list.append(output)
            continue

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

        allele1 = {"0|0": [snp1_a1, snp1_a1], "0|1": [snp1_a1, snp1_a2], "1|0": [snp1_a2, snp1_a1], "1|1": [
            snp1_a2, snp1_a2], "0": [snp1_a1, "."], "1": [snp1_a2, "."], "./.": [".", "."], ".": [".", "."]}

        # SNP2
        if len(vcf2) == 0:
            output["error"] = snp2 + " is not in 1000G reference panel."
            output_list.append(output)
            continue

        elif len(vcf2) > 1:
            geno2 = []
            for i in range(len(vcf2)):
                if vcf2[i].strip().split()[2] == snp2:
                    geno2 = vcf2[i].strip().split()
                    geno2[0] = geno2[0].lstrip('chr')
            if geno2 == []:
                output["error"] = snp2 + " is not in 1000G reference panel."
                output_list.append(output)
                continue

        else:
            geno2 = vcf2[0].strip().split()
            geno2[0] = geno2[0].lstrip('chr')

        if geno2[2] != snp2 and snp2[0:2] == "rs" and "rs" in geno2[2]:
            if "warning" in output:
                output["warning"] = output["warning"] + \
                    ". Genomic position for query variant2 (" + snp2 + \
                    ") does not match RS number at 1000G position (chr" + \
                    geno2[0]+":"+geno2[1]+" = "+geno2[2]+")"
            else:
                output["warning"] = "Genomic position for query variant2 (" + snp2 + \
                    ") does not match RS number at 1000G position (chr" + \
                    geno2[0]+":"+geno2[1]+" = "+geno2[2]+")"
            snp2 = geno2[2]

        if "," in geno2[3] or "," in geno2[4]:
            output["error"] = snp2 + " is not a biallelic variant."
            output_list.append(output)
            continue

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

        allele2 = {"0|0": [snp2_a1, snp2_a1], "0|1": [snp2_a1, snp2_a2], "1|0": [snp2_a2, snp2_a1], "1|1": [
            snp2_a2, snp2_a2], "0": [snp2_a1, "."], "1": [snp2_a2, "."], "./.": [".", "."], ".": [".", "."]}

        if geno1[1] != vcf1_pos:
            output["error"] = "VCF File does not match variant coordinates for SNP1."
            output_list.append(output)
            continue

        if geno2[1] != vcf2_pos:
            output["error"] = "VCF File does not match variant coordinates for SNP2."
            output_list.append(output)
            continue

        # Get headers
        tabix_snp1_h = export_s3_keys + " cd {1}; tabix -HD {0} | grep CHROM".format(vcf_file1, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
        head1 = [x.decode('utf-8') for x in subprocess.Popen(tabix_snp1_h, shell=True, stdout=subprocess.PIPE).stdout.readlines()][0].strip().split()

        tabix_snp2_h = export_s3_keys + " cd {1}; tabix -HD {0} | grep CHROM".format(vcf_file2, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
        head2 =  [x.decode('utf-8') for x in subprocess.Popen(tabix_snp2_h, shell=True, stdout=subprocess.PIPE).stdout.readlines()][0].strip().split()

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
        tmax = max(A, B, C, D)

        hap1 = sorted(hap, key=hap.get, reverse=True)[0]
        hap2 = sorted(hap, key=hap.get, reverse=True)[1]
        hap3 = sorted(hap, key=hap.get, reverse=True)[2]
        hap4 = sorted(hap, key=hap.get, reverse=True)[3]

        delta = float(A * D - B * C)
        Ms = float((A + C) * (B + D) * (A + B) * (C + D))
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
            D_prime = "NA"
            r2 = "NA"
            chisq = "NA"
            p = "NA"

        # Find Correlated Alleles
        if str(r2) != "NA" and float(r2) > 0.1:
            Ac=hap[sorted(hap)[0]]
            Bc=hap[sorted(hap)[1]]
            Cc=hap[sorted(hap)[2]]
            Dc=hap[sorted(hap)[3]]

            if ((Ac*Dc) / max((Bc*Cc), 0.01) > 1):
                corr1 = snp1 + "(" + sorted(hap)[0].split("_")[0] + ") allele is correlated with " + snp2 + "(" + sorted(hap)[0].split("_")[1] + ") allele"
                corr2 = snp1 + "(" + sorted(hap)[3].split("_")[0] + ") allele is correlated with " + snp2 + "(" + sorted(hap)[3].split("_")[1] + ") allele"
                corr_alleles = [corr1, corr2]
            else:
                corr1 = snp1 + "(" + sorted(hap)[1].split("_")[0] + ") allele is correlated with " + snp2 + "(" + sorted(hap)[1].split("_")[1] + ") allele"
                corr2 = snp1 + "(" + sorted(hap)[2].split("_")[0] + ") allele is correlated with " + snp2 + "(" + sorted(hap)[2].split("_")[1] + ") allele"
                corr_alleles = [corr1, corr2]
        else:
            corr_alleles = [snp1 + " and " + snp2 + " are in linkage equilibrium"]
            

        # Create JSON output
        snp_1 = {}
        snp_1["rsnum"] = snp1
        snp_1["coord"] = "chr" + snp1_coord['chromosome'] + ":" + \
            vcf1_pos

        snp_1_allele_1 = {}
        snp_1_allele_1["allele"] = sorted(hap)[0].split("_")[0]
        snp_1_allele_1["count"] = str(A + B)
        snp_1_allele_1["frequency"] = str(round(float(A + B) / N, 3))
        snp_1["allele_1"] = snp_1_allele_1

        snp_1_allele_2 = {}
        snp_1_allele_2["allele"] = sorted(hap)[2].split("_")[0]
        snp_1_allele_2["count"] = str(C + D)
        snp_1_allele_2["frequency"] = str(round(float(C + D) / N, 3))
        snp_1["allele_2"] = snp_1_allele_2
        output["snp1"] = snp_1

        snp_2 = {}
        snp_2["rsnum"] = snp2
        snp_2["coord"] = "chr" + snp2_coord['chromosome'] + ":" + \
            vcf2_pos

        snp_2_allele_1 = {}
        snp_2_allele_1["allele"] = sorted(hap)[0].split("_")[1]
        snp_2_allele_1["count"] = str(A + C)
        snp_2_allele_1["frequency"] = str(round(float(A + C) / N, 3))
        snp_2["allele_1"] = snp_2_allele_1

        snp_2_allele_2 = {}
        snp_2_allele_2["allele"] = sorted(hap)[1].split("_")[1]
        snp_2_allele_2["count"] = str(B + D)
        snp_2_allele_2["frequency"] = str(round(float(B + D) / N, 3))
        snp_2["allele_2"] = snp_2_allele_2
        output["snp2"] = snp_2

        two_by_two = {}
        cells = {}
        cells["c11"] = str(A)
        cells["c12"] = str(B)
        cells["c21"] = str(C)
        cells["c22"] = str(D)
        two_by_two["cells"] = cells
        two_by_two["total"] = str(N)
        output["two_by_two"] = two_by_two

        haplotypes = {}
        hap_1 = {}
        hap_1["alleles"] = hap1
        hap_1["count"] = str(hap[hap1])
        hap_1["frequency"] = str(round(float(hap[hap1]) / N, 3))
        haplotypes["hap1"] = hap_1

        hap_2 = {}
        hap_2["alleles"] = hap2
        hap_2["count"] = str(hap[hap2])
        hap_2["frequency"] = str(round(float(hap[hap2]) / N, 3))
        haplotypes["hap2"] = hap_2

        hap_3 = {}
        hap_3["alleles"] = hap3
        hap_3["count"] = str(hap[hap3])
        hap_3["frequency"] = str(round(float(hap[hap3]) / N, 3))
        haplotypes["hap3"] = hap_3

        hap_4 = {}
        hap_4["alleles"] = hap4
        hap_4["count"] = str(hap[hap4])
        hap_4["frequency"] = str(round(float(hap[hap4]) / N, 3))
        haplotypes["hap4"] = hap_4
        output["haplotypes"] = haplotypes

        statistics = {}
        if Ms != 0:
            statistics["d_prime"] = str(round(D_prime, 4))
            statistics["r2"] = str(round(r2, 4))
            statistics["chisq"] = str(round(chisq, 4))
            if p >= 0.0001:
                statistics["p"] = str(round(p, 4))
            else:
                statistics["p"] = "<0.0001"
        else:
            statistics["d_prime"] = D_prime
            statistics["r2"] = r2
            statistics["chisq"] = chisq
            statistics["p"] = p

        output["statistics"] = statistics
        output["corr_alleles"] = corr_alleles
        output["request"] = request
        output_list.append(output)

    ### OUTPUT ERROR IF ONLY SINGLE SNP PAIR ###
    if len(snp_pairs) == 1 and len(output_list) == 1 and "error" in output_list[0]:
        return(json.dumps(output_list, sort_keys=True, indent=2))

    # Generate output file only for single SNP pair inputs
    if len(snp_pairs) == 1 and len(output_list) == 1:
        ldpair_out = open(tmp_dir + "LDpair_" + request + ".txt", "w")
        print("Query SNPs:", file=ldpair_out)
        print(output_list[0]["snp1"]["rsnum"] + \
            " (" + output_list[0]["snp1"]["coord"] + ")", file=ldpair_out)
        print(output_list[0]["snp2"]["rsnum"] + \
            " (" + output_list[0]["snp2"]["coord"] + ")", file=ldpair_out)
        print("", file=ldpair_out)
        print(pop + " Haplotypes:", file=ldpair_out)
        print(" " * 15 + output_list[0]["snp2"]["rsnum"], file=ldpair_out)
        print(" " * 15 + \
            output_list[0]["snp2"]["allele_1"]["allele"] + " " * \
            7 + output_list[0]["snp2"]["allele_2"]["allele"], file=ldpair_out)
        print(" " * 13 + "-" * 17, file=ldpair_out)
        print(" " * 11 + output_list[0]["snp1"]["allele_1"]["allele"] + " | " + output_list[0]["two_by_two"]["cells"]["c11"] + " " * (5 - len(output["two_by_two"]["cells"]["c11"])) + " | " + output["two_by_two"]["cells"]["c12"] + " " * (
            5 - len(output_list[0]["two_by_two"]["cells"]["c12"])) + " | " + output_list[0]["snp1"]["allele_1"]["count"] + " " * (5 - len(output["snp1"]["allele_1"]["count"])) + " (" + output["snp1"]["allele_1"]["frequency"] + ")", file=ldpair_out)
        print(output_list[0]["snp1"]["rsnum"] + " " * \
            (10 - len(output_list[0]["snp1"]["rsnum"])) + " " * 3 + "-" * 17, file=ldpair_out)
        print(" " * 11 + output_list[0]["snp1"]["allele_2"]["allele"] + " | " + output_list[0]["two_by_two"]["cells"]["c21"] + " " * (5 - len(output["two_by_two"]["cells"]["c21"])) + " | " + output["two_by_two"]["cells"]["c22"] + " " * (
            5 - len(output_list[0]["two_by_two"]["cells"]["c22"])) + " | " + output_list[0]["snp1"]["allele_2"]["count"] + " " * (5 - len(output["snp1"]["allele_2"]["count"])) + " (" + output["snp1"]["allele_2"]["frequency"] + ")", file=ldpair_out)
        print(" " * 13 + "-" * 17, file=ldpair_out)
        print(" " * 15 + output_list[0]["snp2"]["allele_1"]["count"] + " " * (5 - len(output_list[0]["snp2"]["allele_1"]["count"])) + " " * 3 + output["snp2"]["allele_2"]["count"] + " " * (
            5 - len(output_list[0]["snp2"]["allele_2"]["count"])) + " " * 3 + output_list[0]["two_by_two"]["total"], file=ldpair_out)
        print(" " * 14 + "(" + output_list[0]["snp2"]["allele_1"]["frequency"] + ")" + " " * (5 - len(output_list[0]["snp2"]["allele_1"]["frequency"])) + \
            " (" + output_list[0]["snp2"]["allele_2"]["frequency"] + ")" + \
            " " * (5 - len(output_list[0]["snp2"]["allele_2"]["frequency"])), file=ldpair_out)
        print("", file=ldpair_out)
        print("          " + output_list[0]["haplotypes"]["hap1"]["alleles"] + ": " + \
            output_list[0]["haplotypes"]["hap1"]["count"] + \
            " (" + output_list[0]["haplotypes"]["hap1"]["frequency"] + ")", file=ldpair_out)
        print("          " + output_list[0]["haplotypes"]["hap2"]["alleles"] + ": " + \
            output_list[0]["haplotypes"]["hap2"]["count"] + \
            " (" + output_list[0]["haplotypes"]["hap2"]["frequency"] + ")", file=ldpair_out)
        print("          " + output_list[0]["haplotypes"]["hap3"]["alleles"] + ": " + \
            output_list[0]["haplotypes"]["hap3"]["count"] + \
            " (" + output_list[0]["haplotypes"]["hap3"]["frequency"] + ")", file=ldpair_out)
        print("          " + output_list[0]["haplotypes"]["hap4"]["alleles"] + ": " + \
            output["haplotypes"]["hap4"]["count"] + \
            " (" + output["haplotypes"]["hap4"]["frequency"] + ")", file=ldpair_out)
        print("", file=ldpair_out)
        print("          D': " + output_list[0]["statistics"]["d_prime"], file=ldpair_out)
        print("          R2: " + output_list[0]["statistics"]["r2"], file=ldpair_out)
        print("      Chi-sq: " + output_list[0]["statistics"]["chisq"], file=ldpair_out)
        print("     p-value: " + output_list[0]["statistics"]["p"], file=ldpair_out)
        print("", file=ldpair_out)
        if len(output_list[0]["corr_alleles"]) == 2:
            print(output_list[0]["corr_alleles"][0], file=ldpair_out)
            print(output_list[0]["corr_alleles"][1], file=ldpair_out)
        else:
            print(output_list[0]["corr_alleles"][0], file=ldpair_out)

        try:
            output_list[0]["warning"]
        except KeyError:
            www = "do nothing"
        else:
            print("WARNING: " + output_list[0]["warning"] + "!", file=ldpair_out)
        ldpair_out.close()

    # Return output
    return(json.dumps(output_list, sort_keys=True, indent=2))

def main():
    import json
    import sys
    import random

    request = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
    web = False # set to False if not called via Flask

    # Import LDpair options
    if len(sys.argv) == 4:
        snp_pairs = sys.argv[1] # ex [["rs3", "rs4"]]
        pop = sys.argv[2] # ex "YRI+CEU"
        genome_build = sys.argv[3] # "grch37", "grch38", or "grch38_high_coverage"
    else:
        print("Correct useage is: LDpair.py snp_pairs populations genome_build")
        sys.exit()

    # Run function
    out_json = calculate_pair(snp_pairs, pop, web, genome_build, request)

    # Print output
    json_dict = json.loads(out_json)
    try:
        json_dict["error"]

    except KeyError:
        print("")
        print("Query SNPs:")
        print(json_dict["snp1"]["rsnum"] + \
            " (" + json_dict["snp1"]["coord"] + ")")
        print(json_dict["snp2"]["rsnum"] + \
            " (" + json_dict["snp2"]["coord"] + ")")
        print("")
        print(pop + " Haplotypes:")
        print(" " * 15 + json_dict["snp2"]["rsnum"])
        print(" " * 15 + json_dict["snp2"]["allele_1"]["allele"] + \
            " " * 7 + json_dict["snp2"]["allele_2"]["allele"])
        print(" " * 13 + "-" * 17)
        print(" " * 11 + json_dict["snp1"]["allele_1"]["allele"] + " | " + json_dict["two_by_two"]["cells"]["c11"] + " " * (5 - len(json_dict["two_by_two"]["cells"]["c11"])) + " | " + json_dict["two_by_two"]["cells"]["c12"] + " " * (
            5 - len(json_dict["two_by_two"]["cells"]["c12"])) + " | " + json_dict["snp1"]["allele_1"]["count"] + " " * (5 - len(json_dict["snp1"]["allele_1"]["count"])) + " (" + json_dict["snp1"]["allele_1"]["frequency"] + ")")
        print(json_dict["snp1"]["rsnum"] + " " * \
            (10 - len(json_dict["snp1"]["rsnum"])) + " " * 3 + "-" * 17)
        print(" " * 11 + json_dict["snp1"]["allele_2"]["allele"] + " | " + json_dict["two_by_two"]["cells"]["c21"] + " " * (5 - len(json_dict["two_by_two"]["cells"]["c21"])) + " | " + json_dict["two_by_two"]["cells"]["c22"] + " " * (
            5 - len(json_dict["two_by_two"]["cells"]["c22"])) + " | " + json_dict["snp1"]["allele_2"]["count"] + " " * (5 - len(json_dict["snp1"]["allele_2"]["count"])) + " (" + json_dict["snp1"]["allele_2"]["frequency"] + ")")
        print(" " * 13 + "-" * 17)
        print(" " * 15 + json_dict["snp2"]["allele_1"]["count"] + " " * (5 - len(json_dict["snp2"]["allele_1"]["count"])) + " " * 3 + json_dict["snp2"]["allele_2"]["count"] + " " * (
            5 - len(json_dict["snp2"]["allele_2"]["count"])) + " " * 3 + json_dict["two_by_two"]["total"])
        print(" " * 14 + "(" + json_dict["snp2"]["allele_1"]["frequency"] + ")" + " " * (5 - len(json_dict["snp2"]["allele_1"]["frequency"])) + \
            " (" + json_dict["snp2"]["allele_2"]["frequency"] + ")" + \
            " " * (5 - len(json_dict["snp2"]["allele_2"]["frequency"])))
        print("")
        print("          " + json_dict["haplotypes"]["hap1"]["alleles"] + ": " + \
            json_dict["haplotypes"]["hap1"]["count"] + \
            " (" + json_dict["haplotypes"]["hap1"]["frequency"] + ")")
        print("          " + json_dict["haplotypes"]["hap2"]["alleles"] + ": " + \
            json_dict["haplotypes"]["hap2"]["count"] + \
            " (" + json_dict["haplotypes"]["hap2"]["frequency"] + ")")
        print("          " + json_dict["haplotypes"]["hap3"]["alleles"] + ": " + \
            json_dict["haplotypes"]["hap3"]["count"] + \
            " (" + json_dict["haplotypes"]["hap3"]["frequency"] + ")")
        print("          " + json_dict["haplotypes"]["hap4"]["alleles"] + ": " + \
            json_dict["haplotypes"]["hap4"]["count"] + \
            " (" + json_dict["haplotypes"]["hap4"]["frequency"] + ")")
        print("")
        print("          D': " + json_dict["statistics"]["d_prime"])
        print("          R2: " + json_dict["statistics"]["r2"])
        print("      Chi-sq: " + json_dict["statistics"]["chisq"])
        print("     p-value: " + json_dict["statistics"]["p"])
        print("")
        if len(json_dict["corr_alleles"]) == 2:
            print(json_dict["corr_alleles"][0])
            print(json_dict["corr_alleles"][1])
        else:
            print(json_dict["corr_alleles"][0])

        try:
            json_dict["warning"]
        except KeyError:
            print("")
        else:
            print("WARNING: " + json_dict["warning"] + "!")
            print("")

    else:
        print("")
        print(json_dict["error"])
        print("")


if __name__ == "__main__":
    main()
