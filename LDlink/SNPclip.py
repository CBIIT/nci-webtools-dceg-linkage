#!/usr/bin/env python3
import yaml
import json
import math
import operator
import os
from pymongo import MongoClient
from bson import json_util, ObjectId
import boto3
import botocore
import subprocess
import sys
import collections
from LDcommon import checkS3File, retrieveAWSCredentials, retrieveTabix1000GData, genome_build_vars, get_rsnum,connectMongoDBReadOnly
from LDcommon import validsnp,get_coords,replace_coords_rsid_list
###########
# SNPclip #
###########

# Create SNPtip function

def calculate_clip(snplst, pop, request, web, genome_build, r2_threshold=0.1, maf_threshold=0.01):
    max_list = 5000
    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    dbsnp_version = config['data']['dbsnp_version']
    population_samples_dir = config['data']['population_samples_dir']
    data_dir = config['data']['data_dir']
    tmp_dir = config['data']['tmp_dir']
    genotypes_dir = config['data']['genotypes_dir']
    aws_info = config['aws']
   
    export_s3_keys = retrieveAWSCredentials()

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    out_json = open(tmp_dir+"clip"+request+".json", "w")
    output = {}

   # Validate genome build param
    snps=validsnp(snplst,genome_build,max_list)
      #if return value is string, then it is error message and need to return the message
    if isinstance(snps, str):
        print(snps, file=out_json)
        out_json.close()
        return("", "", "")

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(data_dir + population_samples_dir + pop_i + ".txt")
        else:
            output["error"] = pop_i+" is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    get_pops = "cat " + " ".join(pop_dirs)
    pop_list = [x.decode('utf-8') for x in subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(True)

    snps = replace_coords_rsid_list(db, snps,genome_build,output)

    # Find RS numbers in snp database
    details = collections.OrderedDict()
    rs_nums = []
    snp_pos = []
    snp_coords = []
    warn = []
    tabix_coords = ""
    for snp_i in snps:
        if len(snp_i) > 0:
            if len(snp_i[0]) > 2:
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                    snp_coord = get_coords(db, snp_i[0])
                    if snp_coord != None and snp_coord[genome_build_vars[genome_build]['position']] != "NA":
                        # check if variant is on chrY for genome build = GRCh38
                        if snp_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
                            if "warning" in output:
                                output["warning"] = output["warning"] + \
                                    ". " + "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
                            else:
                                output["warning"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
                            warn.append(snp_i[0])
                            details[snp_i[0]] = ["NA", "NA", "Chromosome Y variants are unavailable for GRCh38, only available for GRCh37."]
                        else:
                            rs_nums.append(snp_i[0])
                            snp_pos.append(snp_coord[genome_build_vars[genome_build]['position']])
                            temp = [snp_i[0], snp_coord['chromosome'], snp_coord[genome_build_vars[genome_build]['position']]]
                            snp_coords.append(temp)
                    else:
                        warn.append(snp_i[0])
                        details[snp_i[0]] = ["NA", "NA", "Variant not found in dbSNP" + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + "), variant removed."]
                else:
                    warn.append(snp_i[0])
                    details[snp_i[0]] = ["NA", "NA",
                                         "Not a RS number, query removed."]
            else:
                warn.append(snp_i[0])
                details[snp_i[0]] = ["NA", "NA",
                                     "Not a RS number, query removed."]
        else:
            output["error"] = "Input list of RS numbers is empty"
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "", "")

    if warn != []:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
        else:
            output["warning"] = "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)

    if len(rs_nums) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers or coordinates. " + output["warning"]
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

    # Make tabix formatted coordinates
    snp_coord_str = [genome_build_vars[genome_build]['1000G_chr_prefix'] + snp_coords[0][1]+":"+i+"-"+i for i in snp_pos]
    tabix_coords = " "+" ".join(snp_coord_str)

    # Extract 1000 Genomes phased genotypes
    vcf_filePath = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (snp_coords[0][1]))
    vcf_query_snp_file = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath)

    checkS3File(aws_info, config['aws']['bucket'], vcf_filePath)

    vcf = retrieveTabix1000GData(vcf_query_snp_file, tabix_coords, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])

    # Make MAF function
    def calc_maf(genos):
        vals = {"0|0": 0, "0|1": 0, "1|0": 0, "1|1": 0, "0": 0, "1": 0}
        for i in range(len(genos)):
            if genos[i] in vals:
                vals[genos[i]] += 1

        zeros = vals["0|0"]*2+vals["0|1"]+vals["1|0"]+vals["0"]
        ones = vals["1|1"]*2+vals["0|1"]+vals["1|0"]+vals["1"]
        total = zeros+ones

        f0 = zeros*1.0/total
        f1 = ones*1.0/total
        maf = min(f0, f1)

        return f0, f1, maf

    # Define function to correct indel alleles
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

    # Make R2 function
    def calc_r2(var1, var2):
        hap_vals = {"0|0-0|0": 0, "0|0-0|1": 0, "0|0-1|0": 0, "0|0-1|1": 0, "0|1-0|0": 0, "0|1-0|1": 0, "0|1-1|0": 0, "0|1-1|1": 0, "1|0-0|0": 0,
                    "1|0-0|1": 0, "1|0-1|0": 0, "1|0-1|1": 0, "1|1-0|0": 0, "1|1-0|1": 0, "1|1-1|0": 0, "1|1-1|1": 0, "0-0": 0, "0-1": 0, "1-0": 0, "1-1": 0}
        for i in range(len(var1)):
            ind_geno = var1[i]+"-"+var2[i]
            if ind_geno in hap_vals:
                hap_vals[ind_geno] += 1

        A = hap_vals["0|0-0|0"]*2+hap_vals["0|0-0|1"]+hap_vals["0|0-1|0"]+hap_vals["0|1-0|0"] + \
            hap_vals["0|1-0|1"]+hap_vals["1|0-0|0"] + \
            hap_vals["1|0-1|0"]+hap_vals["0-0"]
        B = hap_vals["0|0-0|1"]+hap_vals["0|0-1|0"]+hap_vals["0|0-1|1"]*2+hap_vals["0|1-1|0"] + \
            hap_vals["0|1-1|1"]+hap_vals["1|0-0|1"] + \
            hap_vals["1|0-1|1"]+hap_vals["0-1"]
        C = hap_vals["0|1-0|0"]+hap_vals["0|1-1|0"]+hap_vals["1|0-0|0"]+hap_vals["1|0-0|1"] + \
            hap_vals["1|1-0|0"]*2+hap_vals["1|1-0|1"] + \
            hap_vals["1|1-1|0"]+hap_vals["1-0"]
        D = hap_vals["0|1-0|1"]+hap_vals["0|1-1|1"]+hap_vals["1|0-1|0"]+hap_vals["1|0-1|1"] + \
            hap_vals["1|1-0|1"]+hap_vals["1|1-1|0"] + \
            hap_vals["1|1-1|1"]*2+hap_vals["1-1"]

        delta = float(A*D-B*C)
        Ms = float((A+C)*(B+D)*(A+B)*(C+D))
        if Ms != 0:
            r2 = (delta**2)/Ms
        else:
            r2 = None

        return(r2)

    # Import SNP VCF file
    hap_dict = {}
    h = 0
    while vcf[h][0:2] == "##":
        h += 1

    head = vcf[h].strip().split()

    # Extract population specific haplotypes
    pop_index = []
    for i in range(9, len(head)):
        if head[i] in pop_ids:
            pop_index.append(i)

    rsnum_lst = []

    for g in range(h+1, len(vcf)):
        geno = vcf[g].strip().split()
        geno[0] = geno[0].lstrip('chr')
        if geno[1] not in snp_pos:
            if "warning" in output:
                output["warning"] = output["warning"]+". Genomic position ("+geno[1]+") in VCF file does not match db" + \
                    dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ") search coordinates for query variant"
            else:
                output["warning"] = "Genomic position ("+geno[1]+") in VCF file does not match db" + \
                    dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ") search coordinates for query variant"
            continue

        if snp_pos.count(geno[1]) == 1:
            rs_query = rs_nums[snp_pos.index(geno[1])]

        else:
            pos_index = []
            for p in range(len(snp_pos)):
                if snp_pos[p] == geno[1]:
                    pos_index.append(p)
            for p in pos_index:
                if rs_nums[p] not in rsnum_lst:
                    rs_query = rs_nums[p]
                    break

        if rs_query in rsnum_lst:
            continue

        rs_1000g = geno[2]

        if rs_query == rs_1000g:
            rsnum = rs_1000g
        else:
            count = -2
            found = "false"
            while count <= 2 and count+g < len(vcf):
                geno_next = vcf[g+count].strip().split()
                geno_next[0] = geno_next[0].lstrip('chr')
                if len(geno_next) >= 3 and rs_query == geno_next[2]:
                    found = "true"
                    break
                count += 1

            if found == "false":
                if "rs" in rs_1000g:
                    if "warning" in output:
                        output["warning"] = output["warning"] + \
                            ". Genomic position for query variant ("+rs_query + \
                            ") does not match RS number at 1000G position (chr" + \
                            geno[0]+":"+geno[1]+" = "+rs_1000g+")"
                    else:
                        output["warning"] = "Genomic position for query variant ("+rs_query + \
                            ") does not match RS number at 1000G position (chr" + \
                            geno[0]+":"+geno[1]+" = "+rs_1000g+")"

                indx = [i[0] for i in snps].index(rs_query)
                # snps[indx][0]=geno[2]
                # rsnum=geno[2]
                snps[indx][0] = rs_query
                rsnum = rs_query
                # try:
                # 	indx=[i[0] for i in snps].index(rs_query)
                # 	snps[indx][0]=geno[2]
                # 	rsnum=geno[2]
                # except ValueError:
                # 	print("List does not contain value:")
                # 	print "#####"
                # 	print "variable rs_query " + rs_query
                # 	print "variable snps " + str(snps)
                # 	print "#####"
            else:
                continue

        details[rsnum] = ["chr"+geno[0]+":"+geno[1]]

        if "," not in geno[3] and "," not in geno[4]:
            temp_genos = []
            for i in range(len(pop_index)):
                temp_genos.append(geno[pop_index[i]])
            f0, f1, maf = calc_maf(temp_genos)
            a0, a1 = set_alleles(geno[3], geno[4])
            details[rsnum].append(
                a0+"="+str(round(f0, 3))+", "+a1+"="+str(round(f1, 3)))
            if maf_threshold <= maf:
                hap_dict[rsnum] = [temp_genos]
                rsnum_lst.append(rsnum)
            else:
                details[rsnum].append(
                    "Variant MAF is "+str(round(maf, 4))+", variant removed.")
        else:
            details[rsnum].append(geno[3]+"=NA, "+geno[4]+"=NA")
            details[rsnum].append("Variant is not biallelic, variant removed.")

    for i in rs_nums:
        if i not in rsnum_lst:
            if i not in details:
                index_i = rs_nums.index(i)
                details[i] = ["chr"+snp_coords[index_i][1]+":"+snp_coords[index_i][2]+"-" +
                              snp_coords[index_i][2], "NA", "Variant not in 1000G VCF file, variant removed."]

    # Thin the SNPs
    # sup_2=u"\u00B2"
    sup_2 = "2"
    i = 0
    while i < len(rsnum_lst):
        details[rsnum_lst[i]].append("Variant kept.")
        remove_list = []
        for j in range(i+1, len(rsnum_lst)):
            r2 = calc_r2(hap_dict[rsnum_lst[i]][0], hap_dict[rsnum_lst[j]][0])
            if r2_threshold <= r2:
                snp = rsnum_lst[j]
                details[snp].append("Variant in LD with "+rsnum_lst[i] +
                                    " (R"+sup_2+"="+str(round(r2, 4))+"), variant removed.")
                remove_list.append(snp)
        for snp in remove_list:
            rsnum_lst.remove(snp)
        i += 1

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()
    return(snps, rsnum_lst, details)

def main():
    tmp_dir = "./tmp/"

    # Import SNPclip options
    if len(sys.argv) == 6:
        web = sys.argv[1]
        snplst = sys.argv[2]
        pop = sys.argv[3]
        request = sys.argv[4]
        genome_build = sys.argv[5]
        r2_threshold = 0.10
        maf_threshold = 0.01
    elif len(sys.argv) == 7:
        web = sys.argv[1]
        snplst = sys.argv[2]
        pop = sys.argv[3]
        request = sys.argv[4]
        genome_build = sys.argv[5]
        r2_threshold = sys.argv[6]
        maf_threshold = 0.01
    elif len(sys.argv) == 8:
        web = sys.argv[1]
        snplst = sys.argv[2]
        pop = sys.argv[3]
        request = sys.argv[4]
        genome_build = sys.argv[5]
        r2_threshold = sys.argv[6]
        maf_threshold = sys.argv[7]
    else:
        print("Correct useage is: SNPclip.py false snplst populations request (optional: r2_threshold maf_threshold)")
        sys.exit()

    # Run function
    snps, thin_list, details = calculate_clip(
        snplst, pop, request, web, genome_build, r2_threshold, maf_threshold)

    # Print output
    with open(tmp_dir+"clip"+request+".json") as f:
        json_dict = json.load(f)

    try:
        json_dict["error"]

    except KeyError:
        #print ""
        # print "LD Thinned SNP list ("+pop+"):"
        # for snp in thin_list:
        # 	print snp

        # print ""
        print("RS Number\tPosition\tAlleles\tDetails")
        for snp in snps:
            print(snp[0]+"\t"+"\t".join(details[snp[0]]))

        try:
            json_dict["warning"]

        except KeyError:
            print("")
        else:
            print("")
            print("WARNING: "+json_dict["warning"]+"!")
            print("")

    else:
        print("")
        print(json_dict["error"])
        print("")


if __name__ == "__main__":
    main()
