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
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars, get_rsnum,connectMongoDBReadOnly,validsnp
from LDcommon import replace_coord_rsid, get_coords,get_population,get_query_variant_c,check_allele
from LDutilites import get_config
# Create LDpair function

def calculate_pair(snp_pairs, pop, web, genome_build, request):

    # Set data directories using config.yml
    param_list = get_config()
    env = param_list['env']
    dbsnp_version = param_list['dbsnp_version']
    population_samples_dir = param_list['population_samples_dir']
    data_dir = param_list['data_dir']
    tmp_dir = param_list['tmp_dir']
    genotypes_dir = param_list['genotypes_dir']
    aws_info = param_list['aws_info']

    export_s3_keys = retrieveAWSCredentials()

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    output_list = []
    snp_pair_limit = 10
    
    # # Throw max SNP pairs error message
    # if len(snp_pairs) > snp_pair_limit:
    #     error_out = [{
    #         "error": "Maximum SNP pair list is " + str(snp_pair_limit) + " pairs. Your list contains " + str(len(snp_pairs)) + " pairs."
    #     }]
    #     return(json.dumps(error_out, sort_keys=True, indent=2))

    #if return value is string, then it is error message and need to return the message
    snps = validsnp(snp_pairs,genome_build,snp_pair_limit)
    if isinstance(snps, str):
       return snps
    # Select desired ancestral populations
    pop_ids = get_population(pop,request,{})
    if isinstance(pop_ids, str):
        error_out = json.loads(pop_ids)
        return(json.dumps([error_out], sort_keys=True, indent=2))
 
    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(web)

    if len(snp_pairs) < 1:
        output = {}
        output["error"] = "Missing at least 1 SNP pair input. " + str(output["warning"] if "warning" in output else "")
        output_list.append(output)

    for pair in snp_pairs:
        output = {}
        output["pair"] = pair

        if len(pair) < 2 or len(pair) > 2 or len(pair[0]) < 3 or len(pair[1]) < 3:
            output["error"] = "Missing or additional SNPs in pair. " + str(output["warning"] if "warning" in output else "")
            output_list.append(output)
            continue

        # trim any whitespace
        snp1 = pair[0].lower().strip()
        snp2 = pair[1].lower().strip()

        # Find RS numbers in snp database
        # SNP1
        if re.compile(r'rs\d+', re.IGNORECASE).match(snp1) is None and re.compile(r'chr\d+:\d+', re.IGNORECASE).match(snp1) is None and re.compile(r'chr[X|Y]:\d+', re.IGNORECASE).match(snp1) is None:
            output["error"] = snp1 + " is not a valid SNP. " + str(output["warning"] if "warning" in output else "")
            output_list.append(output)
            continue
        snp1 = replace_coord_rsid(db, snp1,genome_build,output)
        snp1_coord = get_coords(db, snp1)
        if snp1_coord == None or snp1_coord[genome_build_vars[genome_build]['position']] == "NA":
            output["error"] = snp1 + " is not in dbSNP build " + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + "). " + str(output["warning"] if "warning" in output else "")
            output_list.append(output)
            continue

        # SNP2
        if re.compile(r'rs\d+', re.IGNORECASE).match(snp2) is None and re.compile(r'chr\d+:\d+', re.IGNORECASE).match(snp2) is None and re.compile(r'chr[X|Y]:\d+', re.IGNORECASE).match(snp2) is None:
            output["error"] = snp2 + " is not a valid SNP. " + str(output["warning"] if "warning" in output else "")
            output_list.append(output)
            continue
        snp2 = replace_coord_rsid(db, snp2,genome_build,output)
        snp2_coord = get_coords(db, snp2)
        if snp2_coord == None or snp2_coord[genome_build_vars[genome_build]['position']] == "NA":
            output["error"] = snp2 + " is not in dbSNP build " + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + "). " + str(output["warning"] if "warning" in output else "")
            output_list.append(output)
            continue
       
        # Check if SNPs are on the same chromosome
        if snp1_coord['chromosome'] != snp2_coord['chromosome']:
            output["warning"] = str(output["warning"] if "warning" in output else "") + snp1 + " and " + snp2 + " are on different chromosomes. "
 
        # Check if input SNPs are on chromosome Y while genome build == grch38
        # SNP1
        if snp1_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
            output["error"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp1_coord['id'] + " - chr" + snp1_coord['chromosome'] + ":" + snp1_coord[genome_build_vars[genome_build]['position']] + "). " + str(output["warning"] if "warning" in output else "")
            output_list.append(output) 
            continue

        # SNP2
        if snp2_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
            output["error"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp2_coord['id'] + " - chr" + snp2_coord['chromosome'] + ":" + snp2_coord[genome_build_vars[genome_build]['position']] + "). " + str(output["warning"] if "warning" in output else "")
            output_list.append(output)
            continue

        # Extract 1000 Genomes phased genotypes

        # SNP1
        temp = [snp1, str(snp1_coord['chromosome']), snp1_coord[genome_build_vars[genome_build]['position']]]
        #vcf1,head1 = retrieveTabix1000GDataSingle(temp[2],temp, genome_build, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'],request, False)
        (vcf1, head1, output2) = get_query_variant_c(temp, pop_ids, str(request), genome_build, False,output)   
        #output_list.append(output)
        #if "error" in output:
        #    output_list.append(output)
        #    continue
        temp = [snp2, str(snp2_coord['chromosome']), snp2_coord[genome_build_vars[genome_build]['position']]]
        (vcf2, head2, output2) = get_query_variant_c(temp, pop_ids, str(request), genome_build, False,output)   
        output_list.append(output)
        if "error" in output:
            output_list.append(output)
            continue
        vcf1_pos = snp1_coord[genome_build_vars[genome_build]['position']]
        vcf2_pos = snp2_coord[genome_build_vars[genome_build]['position']]

        geno1 = vcf1
        geno2 = vcf2
   
        allele1,snp1_a1, snp1_a2 = check_allele(geno1)
        allele2,snp2_a1, snp2_a2 = check_allele(geno2)

        if geno1[1] != vcf1_pos:
            output["warning"] = str(output["warning"] if "warning" in output else "")  + "VCF File does not match variant coordinates for SNP1. "
            #output_list.append(output)
            geno1[1] = vcf1_pos

        if geno2[1] != vcf2_pos:
            output["warning"] = str(output["warning"] if "warning" in output else "")  + "VCF File does not match variant coordinates for SNP2. "
            #output_list.append(output)
            geno2[1] = vcf2_pos

    
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
