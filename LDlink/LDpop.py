#!/usr/bin/env python
import yaml
import json
import math
import os
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
import time
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = contents[0].split('=')[1]
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])

# Create LDpop function

def calculate_pop(snp1, snp2, pop, web, request=None):

    # trim any whitespace
    snp1 = snp1.strip()
    snp2 = snp2.strip() 

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    dbsnp_version = config['data']['dbsnp_version']
    pop_dir = config['data']['pop_dir']
    vcf_dir = config['data']['vcf_dir']

    tmp_dir = "./tmp/"

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    output = {}

    # Connect to Mongo snp database
    if web:
        client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
    else:
        client = MongoClient('localhost', port)
    db = client["LDLink"]

    def get_chrom_coords(db, rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp151.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Query genomic coordinates
    def get_rsnum(db, coord):
        temp_coord = coord.strip("chr").split(":")
        chro = temp_coord[0]
        pos = temp_coord[1]
        query_results = db.dbsnp151.find({"chromosome": chro, "position": pos})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coord_rsid(db, snp):
        if snp[0:2] == "rs":
            return snp
        else:
            snp_info_lst = get_rsnum(db, snp)
            print "snp_info_lst"
            print snp_info_lst
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

    snp1 = replace_coord_rsid(db, snp1)
    snp2 = replace_coord_rsid(db, snp2)
    
    snp1_coord = get_chrom_coords(db, snp1)
    snp2_coord = get_chrom_coords(db, snp2)

    # Check if RS numbers are in snp database
    # SNP1
    if snp1_coord == None:
        output["error"] = snp1 + " is not in dbSNP build " + dbsnp_version + "."
        return(json.dumps(output, sort_keys=True, indent=2))
    # SNP2
    if snp2_coord == None:
        output["error"] = snp2 + " is not in dbSNP build " + dbsnp_version + "."
        return(json.dumps(output, sort_keys=True, indent=2))
    # Check if SNPs are on the same chromosome
    if snp1_coord['chromosome'] != snp2_coord['chromosome']:
        output["warning"] = snp1 + " and " + \
            snp2 + " are on different chromosomes"
  
    #empty list for paths to population data
    pop_dirs = []
    pop_split = pop.split("+")
    # pop_dir = "1000gpopulationdefs/"
    
    for pop_i in pop_split:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(pop_dir + pop_i + ".txt")
        else:
            output["error"] = pop_i + " is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            return(json.dumps(output, sort_keys=True, indent=2))
           

    #make empty dictionary to keep sample IDs in for each wanted population 
    ID_dict = {k: [] for k in pop_split}
    adds = ["CHROM", "POS", "ID", "REF", "ALT"]
    
    for pop_i in pop_split:        
        with open(pop_dir + pop_i + ".txt", "r") as f:
            print pop_dir + pop_i + ".txt"
            for line in f:
                cleanedLine = line.strip()
                if cleanedLine: # is not empty
                    ID_dict[pop_i].append(cleanedLine)
            for entry in adds:
                ID_dict[pop_i].append(entry)
            print ID_dict
    
    # Extract 1000 Genomes phased genotypes
    # SNP1
    # vcf_dir = "vcfs/"
   
    vcf_rs1 = vcf_dir + snp1_coord['chromosome'] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    rs1_test = "tabix {0} {1}:{2}-{2} | grep -v -e END".format(vcf_rs1, snp1_coord['chromosome'], snp1_coord['position']) 
    proc1 = subprocess.Popen(rs1_test, shell=True, stdout=subprocess.PIPE)
    vcf1 = proc1.stdout.readlines()[0].strip().split()

    vcf_rs2 = vcf_dir + snp2_coord['chromosome'] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    rs2_test = "tabix {0} {1}:{2}-{2}".format(vcf_rs2, snp2_coord['chromosome'], snp2_coord['position'])
    proc2 = subprocess.Popen(rs2_test, shell=True, stdout=subprocess.PIPE)
    vcf2 = proc2.stdout.readlines()[0].strip().split()
    

    # Get headers
    tabix_snp1_h = "tabix -H {0} | grep CHROM".format(vcf_rs1)
    proc1_h = subprocess.Popen(tabix_snp1_h, shell=True, stdout=subprocess.PIPE)
    head1 = proc1_h.stdout.readlines()[0].strip().split()

    tabix_snp2_h = "tabix -H {0} | grep CHROM".format(vcf_rs2)
    proc2_h = subprocess.Popen(tabix_snp2_h, shell=True, stdout=subprocess.PIPE)
    head2 = proc2_h.stdout.readlines()[0].strip().split()


    
    rs1_dict = dict(zip(head1, vcf1))
    rs2_dict = dict(zip(head2, vcf2))

    # Check if SNPs are in 1000G reference panel
    # SNP1
    if len(vcf1) == 0:
        output["error"] = snp1 + " is not in 1000G reference panel."
        return(json.dumps(output, sort_keys=True, indent=2))
    # SNP2
    if len(vcf2) == 0:
        output["error"] = snp2 + " is not in 1000G reference panel."
        return(json.dumps(output, sort_keys=True, indent=2))
    

    if snp1 != rs1_dict["ID"]:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". Genomic position for query variant1 (" + snp1 + \
                ") does not match RS number at 1000G position (chr" + \
                rs1_dict["#CHROM"]+":"+rs1_dict["POS"]+")"
        else:
            output["warning"] = "Genomic position for query variant1 (" + snp1 + \
                ") does not match RS number at 1000G position (chr" + \
                rs1_dict["#CHROM"]+":"+rs1_dict["POS"]+")"
        snp1 = rs1_dict["ID"]

    if snp2 != rs2_dict["ID"]:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". Genomic position for query variant2 (" + snp2 + \
                ") does not match RS number at 1000G position (chr" + \
                rs2_dict["#CHROM"]+":"+rs2_dict["POS"]+")"
        else:
            output["warning"] = "Genomic position for query variant2 (" + snp2 + \
                ") does not match RS number at 1000G position (chr" + \
                rs2_dict["#CHROM"]+":"+rs2_dict["POS"]+")"
        snp2 = rs2_dict["ID"]
    
    if "<" in rs1_dict["REF"]:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                "." + snp1 + "is a CNV marker. " 
        else:
            output["warning"] = snp1 + "is a CNV marker. " 
            
    if "<" in rs2_dict["REF"]:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                "." + snp2 + "is a CNV marker. " 
        else:
            output["warning"] = snp2 + "is a CNV marker. " 
    
    geno_ind = {
        "rs1" : {k: [] for k in pop_split},
        "rs2" : {k: [] for k in pop_split} 
    }
    


    #SNP1
    for colname in rs1_dict:       
        for key in ID_dict:
            if (colname in ID_dict[key]) and (colname not in adds):
                geno_ind["rs1"][key].append(rs1_dict[colname])
    
    #SNP2            
    for colname in rs2_dict:       
        for key in ID_dict:
            if (colname in ID_dict[key]) and (colname not in adds):
                geno_ind["rs2"][key].append(rs2_dict[colname])
    
    #population freqency dictionary to fill in
    pop_freqs = {
        "ref_freq_snp1" : { }, \
        "ref_freq_snp2" : { }, \
        "alt_freq_snp1" : { }, \
        "alt_freq_snp2" : { }, \
        "total_alleles": { }
    }           
    
    for key in geno_ind["rs1"]:
        pop_freqs["total_alleles"][key] = float(2*geno_ind["rs1"][key].count("0|0") + 2*geno_ind["rs1"][key].count("0|1") +  2*geno_ind["rs1"][key].count("1|1") + 2* geno_ind["rs1"][key].count("1|0"))
        pop_freqs["ref_freq_snp1"][key] = round(((2*geno_ind["rs1"][key].count("0|0") + geno_ind["rs1"][key].count("0|1") + geno_ind["rs1"][key].count("1|0"))/ float(pop_freqs["total_alleles"][key])) *100, 2)
        pop_freqs["ref_freq_snp2"][key] = round(((2*geno_ind["rs2"][key].count("0|0") + geno_ind["rs2"][key].count("0|1") + geno_ind["rs2"][key].count("1|0"))/ float(pop_freqs["total_alleles"][key])) *100, 2)
        pop_freqs["alt_freq_snp1"][key] = round(((2*geno_ind["rs1"][key].count("1|1") + geno_ind["rs1"][key].count("0|1") + geno_ind["rs1"][key].count("1|0"))/ float(pop_freqs["total_alleles"][key])) *100, 2)
        pop_freqs["alt_freq_snp2"][key] = round(((2*geno_ind["rs2"][key].count("1|1") + geno_ind["rs2"][key].count("0|1") + geno_ind["rs2"][key].count("1|0"))/ float(pop_freqs["total_alleles"][key])) *100, 2)
        
    #get sample size for each population
    sample_size_dict = {}  
     
    for key in ID_dict:
        sample_size_dict[key] = len(ID_dict[key])- len(adds)
        
    # Combine phased genotype
    # Extract haplotypes
    hap = {k: {"0_0": 0, "0_1": 0, "1_0": 0, "1_1": 0} for k in pop_split}
    
    for pop in geno_ind["rs1"]:
        for ind in range(len(geno_ind["rs1"][pop])):
            hap1 = geno_ind["rs1"][pop][ind][0] + "_" + geno_ind["rs2"][pop][ind][0]
            hap2 = geno_ind["rs1"][pop][ind][2] + "_" + geno_ind["rs2"][pop][ind][2]

            if hap1 in hap[pop]:
                hap[pop][hap1] += 1           
                hap[pop][hap2] += 1
        
    # Sort haplotypes
    matrix_values = {k : {"A": "", "B": "", "C": "", "D": "", "N": "", "delta" : "", "Ms" : "" , "D_prime":"", "r2":""} for k in pop_split}
    for pop in hap:
        matrix_values[pop]["A"] = hap[pop][sorted(hap[pop])[0]]
        matrix_values[pop]["B"] = hap[pop][sorted(hap[pop])[1]]
        matrix_values[pop]["C"] = hap[pop][sorted(hap[pop])[2]]
        matrix_values[pop]["D"] = hap[pop][sorted(hap[pop])[3]]
        matrix_values[pop]["N"] = matrix_values[pop]["A"] + matrix_values[pop]["B"] + matrix_values[pop]["C"] + matrix_values[pop]["D"]
        matrix_values[pop]["delta"] = float(matrix_values[pop]["A"] * matrix_values[pop]["D"] - matrix_values[pop]["B"] * matrix_values[pop]["C"])
        matrix_values[pop]["Ms"] = float((matrix_values[pop]["A"] + matrix_values[pop]["C"]) * (matrix_values[pop]["B"] + matrix_values[pop]["D"]) * (matrix_values[pop]["A"] + matrix_values[pop]["B"]) * (matrix_values[pop]["C"] + matrix_values[pop]["D"]))
        if matrix_values[pop]["Ms"] != 0:
            # D prime
            if matrix_values[pop]["delta"] < 0:
                matrix_values[pop]["D_prime"] = abs(matrix_values[pop]["delta"] / min((matrix_values[pop]["A"] + matrix_values[pop]["C"]) * (matrix_values[pop]["A"] + matrix_values[pop]["B"]), (matrix_values[pop]["B"] + matrix_values[pop]["D"]) * (matrix_values[pop]["C"] + matrix_values[pop]["D"])))
            else:
                matrix_values[pop]["D_prime"] = abs(matrix_values[pop]["delta"] / min((matrix_values[pop]["A"] + matrix_values[pop]["C"]) * (matrix_values[pop]["C"] + matrix_values[pop]["D"]), (matrix_values[pop]["A"] + matrix_values[pop]["B"]) * (matrix_values[pop]["B"] + matrix_values[pop]["D"])))
            # R2
            matrix_values[pop]["r2"]= (matrix_values[pop]["delta"]**2) / matrix_values[pop]["Ms"]
        else:
            matrix_values[pop]["D_prime"] = "NA"
            matrix_values[pop]["r2"] = "NA"
    
    for pops in sample_size_dict:    
        output[pops] = {
            'Population': pops , 
            'N': sample_size_dict[pops], \
            rs1_dict["ID"] + ' Allele Freq': {rs1_dict["REF"] : str(pop_freqs["ref_freq_snp1"][pops]) + "%", \
            rs1_dict["ALT"] : str(pop_freqs["alt_freq_snp1"][pops]) + "%"} , \
            rs2_dict["ID"] + ' Allele Freq': {rs2_dict["REF"] : str(pop_freqs["ref_freq_snp2"][pops]) + "%", \
            rs2_dict["ALT"] : str(pop_freqs["alt_freq_snp2"][pops]) + "%"}, "D'" : matrix_values[pops]["D_prime"], \
            "R2" : matrix_values[pops]["r2"]
        }
    
    print json.dumps(output)
    # return(json.dumps(output, sort_keys=True, indent=2))
    return output


def main():
    snp1 = sys.argv[1]
    snp2 = sys.argv[2]
    pop = sys.argv[3]
    web = False
    request = None

    # Run function
    out_json = calculate_pop(snp1, snp2, pop, web, request)

    # Print output
    print out_json

if __name__ == "__main__":
    main()
