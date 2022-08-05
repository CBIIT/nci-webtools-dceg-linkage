#!/usr/bin/env python3

import yaml
import json
import copy
import math
import os
import collections
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
import subprocess
from multiprocessing.dummy import Pool
import sys
import numpy as np	
from timeit import default_timer as timer
from LDcommon import genome_build_vars, get_rsnum,connectMongoDBReadOnly
from LDcommon import validsnp, replace_coords_rsid_list,get_coords,get_population,get_output
from LDutilites import get_config

# Set data directories using config.yml	
param_list = get_config()
population_samples_dir = param_list['population_samples_dir']
data_dir = param_list['data_dir']
tmp_dir = param_list['tmp_dir']
num_subprocesses = param_list['num_subprocesses']
dbsnp_version = param_list['dbsnp_version']

def get_ldtrait_timestamp(web):
    try:
        db = connectMongoDBReadOnly(web)    
    except ConnectionFailure:
        print("MongoDB is down")
        print("syntax: mongod --dbpath /local/content/analysistools/public_html/apps/LDlink/data/mongo/data/db/ --auth")
        return "Failed to connect to server."

    for document in db.gwas_catalog.find().sort("_id", -1).limit(1):
        object_id_datetime = document.get('_id').generation_time
    json_output = json.dumps(object_id_datetime, default=json_util.default, sort_keys=True, indent=2)
    return json_output


def get_window_variants(db, chromosome, position, window, genome_build):
    query_results = db.gwas_catalog.find({
        "chromosome": chromosome, 
        genome_build_vars[genome_build]['position']: {
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

def castFloat(val):
    try:
        val_float = float(val)
        return val_float
    except ValueError:
        return val

def findRangeString(val):
    result = re.sub(r"\[*\]*[a-zA-Z]*\s*", "", val)
    if len(result) > 0:
        return result
    else:
        return "NA"

def get_gwas_fields(query_snp, query_snp_chr, query_snp_pos, found, pops, pop_ids, ldInfo, r2_d, r2_d_threshold, genome_build):	    
    matched_snps = []
    window_problematic_snps = []
    for record in found:
        ld = ldInfo.get(query_snp).get("rs" + record["SNP_ID_CURRENT"])
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
                matched_record.append("chr" + str(record["chromosome"]) + ":" + str(record[genome_build_vars[genome_build]['position']]))
                # Alleles	
                matched_record.append(ld["alleles"])	
                # R2	
                matched_record.append(ld["r2"])	
                # D'	
                matched_record.append(ld["D_prime"])	
                # LDpair (Link)	
                matched_record.append([query_snp, "rs" + record["SNP_ID_CURRENT"], "%2B".join(expandSelectedPopulationGroups(pops))])
                # Risk Allele
                matched_record.append(record["RISK ALLELE FREQUENCY"] if ("RISK ALLELE FREQUENCY" in record and len(record["RISK ALLELE FREQUENCY"]) > 0) else "NA")
                # Beta or OR
                matched_record.append(castFloat(record["OR or BETA"]) if ("OR or BETA" in record and len(record["OR or BETA"]) > 0) else "NA")
                # Effect Size (95% CI)
                matched_record.append(findRangeString(record["95% CI (TEXT)"]) if ("95% CI (TEXT)" in record and len(record["95% CI (TEXT)"]) > 0) else "NA")
                # P-value
                matched_record.append(record["P-VALUE"] if ("P-VALUE" in record and len(record["P-VALUE"]) > 0) else "NA")
                # GWAS Catalog (Link)
                matched_record.append("rs" + record["SNP_ID_CURRENT"])
                # Details
                # matched_record.append("Variant found in GWAS catalog within window.")
                # print("matched_record", matched_record)
                matched_snps.append(matched_record)
            else: 
                if (r2_d == "r2"):
                    problematic_record = [query_snp, "rs" + record["SNP_ID_CURRENT"], "chr" + str(record["chromosome"]) + ":" + str(record[genome_build_vars[genome_build]['position']]), record["DISEASE/TRAIT"] if ("DISEASE/TRAIT" in record and len(record["DISEASE/TRAIT"]) > 0) else "NA", "R2 value (" + str(ld["r2"]) + ") below threshold (" + str(r2_d_threshold) + ")"]
                    window_problematic_snps.append(problematic_record)
                else:
                    problematic_record = [query_snp, "rs" + record["SNP_ID_CURRENT"], "chr" + str(record["chromosome"]) + ":" + str(record[genome_build_vars[genome_build]['position']]), record["DISEASE/TRAIT"] if ("DISEASE/TRAIT" in record and len(record["DISEASE/TRAIT"]) > 0) else "NA", "D' value (" + str(ld["D_prime"]) + ") below threshold. (" + str(r2_d_threshold) + ")"]
                    window_problematic_snps.append(problematic_record)
        else:
            problematic_record = [query_snp, "rs" + record["SNP_ID_CURRENT"], "chr" + str(record["chromosome"]) + ":" + str(record[genome_build_vars[genome_build]['position']]), record["DISEASE/TRAIT"] if ("DISEASE/TRAIT" in record and len(record["DISEASE/TRAIT"]) > 0) else "NA", " ".join(ld["output"]["error"])]
            window_problematic_snps.append(problematic_record)
    return (matched_snps, window_problematic_snps)

# Create LDtrait function
def calculate_trait(snplst, pop, request, web, r2_d, genome_build, r2_d_threshold=0.1, window=500000):
    print("##### START LD TRAIT CALCULATION #####")	
    start = timer()
    
    # snp limit
    max_list = 50

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output for warnings and errors
    out_json = open(tmp_dir + "trait" + str(request) + ".json", "w")
    output = {}

    # Validate genome build param
    sanitized_query_snps=validsnp(snplst,genome_build,max_list)
      #if return value is string, then it is error message and need to return the message
    if isinstance(sanitized_query_snps, str):
        print(sanitized_query_snps, file=out_json)
        out_json.close()
        return("", "", "")
     
    # Validate window size is between 0 and 1,000,000
    if window < 0 or window > 1000000:
        output["error"] = "Window value must be a number between 0 and 1,000,000."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "", "")

   

    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(web) 
    # Check if gwas_catalog collection in MongoDB exists, if not, display error
    if "gwas_catalog" not in db.list_collection_names():
        output["error"] = "GWAS Catalog database is currently being updated. Please check back later."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "", "")

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_ids = get_population(pop, request,output)

    sanitized_query_snps = replace_coords_rsid_list(db, sanitized_query_snps,genome_build,output)

    # find genomic coords of query snps in dbsnp 
    # query_snp_details = []
    # details = collections.OrderedDict()
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
                        if "warning" in output:
                            output["warning"] = output["warning"] + \
                                ". " + "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
                        else:
                            output["warning"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
                        warn.append(snp_i[0])
                        queryWarnings.append([snp_i[0], "NA", "Chromosome Y variants are unavailable for GRCh38, only available for GRCh37."])
                    else:
                        rs_nums.append(snp_i[0])
                        snp_pos.append(int(snp_coord[genome_build_vars[genome_build]['position']]))
                        temp = [snp_i[0], str(snp_coord['chromosome']), int(snp_coord[genome_build_vars[genome_build]['position']])]
                        snp_coords.append(temp)
                else:
                    # Generate warning if query variant is not found in dbsnp
                    warn.append(snp_i[0])
                    queryWarnings.append([snp_i[0], "NA", "Variant not found in dbSNP" + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + "), variant removed."])
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

    # generate warnings for query variants not found in dbsnp
    if warn != []:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
        else:
            output["warning"] = "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)

    # Generate errors if no query variants are valid in dbsnp
    if len(rs_nums) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers or coordinates. " + str(output["warning"] if "warning" in output else "")
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
    ldPairs = []
    snp_coords_gwas = []
    # search query snp windows in gwas_catalog
    for snp_coord in snp_coords:
        # print(snp_coord)
        found[snp_coord[0]] = get_window_variants(db, snp_coord[1], snp_coord[2], window, genome_build)
        # print("found", snp_coord[0], len(found[snp_coord[0]]))
        if found[snp_coord[0]] is not None:
            thinned_list.append(snp_coord[0])
            snp_coords_gwas.append(snp_coord)
            # Calculate LD statistics of variant pairs ?in parallel?	
            for record in found[snp_coord[0]]:	
                ldPairs.append([snp_coord[0], str(snp_coord[1]), str(snp_coord[2]), "rs" + record["SNP_ID_CURRENT"], str(record["chromosome"]), str(record[genome_build_vars[genome_build]['position']])])	
                snp_coords_gwas.append(["rs" + record["SNP_ID_CURRENT"], str(record["chromosome"]), str(record[genome_build_vars[genome_build]['position']])])
        else:	
            queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No variants found within window, variant removed."])
                
    ldPairsUnique = [list(x) for x in set(tuple(x) for x in ldPairs)]
    snp_coords_gwas_unique = [list(x) for x in set(tuple(x) for x in ldPairs)]
    #print(snp_coords_gwas)	
    # print("ldPairsUnique", ldPairsUnique)	
    # print("ldPairsUnique length", len(ldPairsUnique))	
    # print("##### BEGIN MULTIPROCESSING LD CALCULATIONS #####")	
    # start = timer()	
    # leverage multiprocessing to calculate all LDpairs	
    splitLDPairsUnique = np.array_split(ldPairsUnique, num_subprocesses)

    # write ld pairs to tmp files to be picked up by ld calculation subprocesses
    for subprocess_id in range(num_subprocesses):
        with open(tmp_dir + 'trait_ld_' + str(subprocess_id) + '_' + str(request) + '.txt', 'w') as snpsPairFile:
            for snps_pair in splitLDPairsUnique[subprocess_id].tolist():
                snpsPairFile.write("\t".join(snps_pair) + "\n")

    ld_subprocess_commands = []
    for subprocess_id in range(num_subprocesses):
        getPairLDArgs = " ".join([str(request), str(subprocess_id), genome_build])
        ld_subprocess_commands.append("python3 LDtrait_ld_sub.py " + getPairLDArgs)

    ld_subprocesses = [subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in ld_subprocess_commands]

    #for subp in ld_subprocesses:
    #    for line in subp.stdout:
    #        print(line.decode().strip())
    # collect output in parallel
    pool = Pool(len(ld_subprocesses))
    ldInfoSubsets = pool.map(get_output, ld_subprocesses)
    pool.close()
    pool.join()	

    # flatten pooled ld pair results
    ldInfoSubsetsFlat = [val.decode('utf-8').strip() for sublist in ldInfoSubsets for val in sublist]
    
    # end = timer()	
    # print("TIME ELAPSED:", str(end - start) + "(s)")	
    # print("##### END MULTIPROCESSING LD CALCULATIONS #####")	
    # print("ldInfoSubsets", ldInfoSubsets)	
    # print("ldInfoSubsets length ", len(ldInfoSubsets))	
    # merge all ldInfo Pool subsets into one ldInfo object	
    ldInfo = {}	
    for ldInfoSubset in ldInfoSubsetsFlat:
        ldInfoSubsetObj = json.loads(ldInfoSubset)
        for key in ldInfoSubsetObj.keys():	
            if key not in ldInfo.keys():	
                ldInfo[key] = {}	
                ldInfo[key] = ldInfoSubsetObj[key]	
            else:	
                for subsetKey in ldInfoSubsetObj[key].keys():	
                    ldInfo[key][subsetKey] = ldInfoSubsetObj[key][subsetKey]	

    # print("ldInfo", json.dumps(ldInfo))

    # clean up tmp file(s) generated by ld pair calculations
    subprocess.call("rm " + tmp_dir + "trait_ld_*_" + str(request) + ".txt", shell=True)
    subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
        	
    for snp_coord in snp_coords:	
        # print("snp_coord", snp_coord)
        (matched_snps, window_problematic_snps) = get_gwas_fields(snp_coord[0], snp_coord[1], snp_coord[2], found[snp_coord[0]], pops, pop_ids, ldInfo, r2_d, r2_d_threshold, genome_build)
        
        # windowWarnings += window_problematic_snps
        if (len(matched_snps) > 0):
            details[snp_coord[0]] = {	
                "aaData": matched_snps
            }
        else:
            # remove from thinned_list
            thinned_list.remove(snp_coord[0])
            queryWarnings.append([snp_coord[0], "chr" + str(snp_coord[1]) + ":" + str(snp_coord[2]), "No entries in the GWAS Catalog are identified using the LDtrait search criteria."]) 

    # details["windowWarnings"] = {
    #     "aaData": windowWarnings
    # }
    details["queryWarnings"] = {
        "aaData": queryWarnings
    }

    # Check if thinned list is empty, if it is, display error
    if len(thinned_list) < 1:
        output["error"] = "No entries in the GWAS Catalog are identified using the LDtrait search criteria."
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
    print("##### LDTRAIT COMPLETE #####")
    return (sanitized_query_snps, thinned_list, details)


def main():
    # snplst = sys.argv[1]
    snplst = "5_LDtrait_snps.txt"
    pop = "YRI"
    request = 8888
    web = False
    r2_d = "r2"
    genome_build = "grch37"
    r2_d_threshold = 0.1
    window=500000

    # Run function
    (sanitized_query_snps, thinned_list, details) = calculate_trait(snplst, pop, request, web, r2_d, genome_build, r2_d_threshold, window)
    print("query_snps", sanitized_query_snps)
    print("thinned_snps", thinned_list)
    print("details", json.dumps(details))

if __name__ == "__main__":
    main()