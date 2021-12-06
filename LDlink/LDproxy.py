#!/usr/bin/env python3
import yaml
import csv
import json
import operator
import os
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
import time
import threading
import weakref
import time
import boto3
import botocore
from multiprocessing.dummy import Pool
import math
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars, getRefGene, getRecomb

def chunkWindow(pos, window, num_subprocesses):
    if (pos - window <= 0):
        minPos = 0
    else:
        minPos = pos - window
    maxPos = pos + window
    windowRange = maxPos - minPos
    chunks = []
    newMin = minPos
    newMax = 0
    for _ in range(num_subprocesses):
        newMax = newMin + (windowRange / num_subprocesses)
        chunks.append([math.ceil(newMin), math.ceil(newMax)])
        newMin = newMax + 1
    return chunks

# Create LDproxy function
def calculate_proxy(snp, pop, request, web, genome_build, r2_d="r2", window=500000, collapseTranscript=True):

    # trim any whitespace
    snp = snp.lower().strip()

    start_time = time.time()

    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    env = config['env']
    api_mongo_addr = config['api']['api_mongo_addr']
    dbsnp_version = config['data']['dbsnp_version']
    data_dir = config['data']['data_dir']
    tmp_dir = config['data']['tmp_dir']
    population_samples_dir = config['data']['population_samples_dir']
    genotypes_dir = config['data']['genotypes_dir']
    aws_info = config['aws']
    mongo_username = config['database']['mongo_user_readonly']
    mongo_password = config['database']['mongo_password']
    mongo_port = config['database']['mongo_port']
    num_subprocesses = config['performance']['num_subprocesses']

    export_s3_keys = retrieveAWSCredentials()

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    if request is False:
        request = str(time.strftime("%I%M%S"))

    # Create JSON output
    out_json = open(tmp_dir + 'proxy' + request + ".json", "w")
    output = {}

    # Validate genome build param
    if genome_build not in genome_build_vars['vars']:
        output["error"] = "Invalid genome build. Please specify either " + ", ".join(genome_build_vars['vars']) + "."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    if window < 0 or window > 1000000:
        output["error"] = "Window value must be a number between 0 and 1,000,000."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    # Connect to Mongo snp database
    if env == 'local':
        mongo_host = api_mongo_addr
    else: 
        mongo_host = 'localhost'
    if web:
        client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
    else:
        if env == 'local':
            client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
        else:
            client = MongoClient('localhost', mongo_port)
    db = client["LDLink"]

    def get_coords(rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Query genomic coordinates
    def get_rsnum(coord):
        temp_coord = coord.strip("chr").split(":")
        chro = temp_coord[0]
        pos = temp_coord[1]
        query_results = db.dbsnp.find({"chromosome": chro.upper() if chro == 'x' or chro == 'y' else str(chro), genome_build_vars[genome_build]['position']: str(pos)})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coord_rsid(snp):
        if snp[0:2] == "rs":
            return snp
        else:
            snp_info_lst = get_rsnum(snp)
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

    snp = replace_coord_rsid(snp)

    # Find RS number in snp database
    snp_coord = get_coords(snp)

    if snp_coord == None or snp_coord[genome_build_vars[genome_build]['position']] == "NA":
        output["error"] = snp + " is not in dbSNP " + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ")."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    # check if variant is on chrY for genome build = GRCh38
    if snp_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
        output["error"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + ")"
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(data_dir + population_samples_dir + pop_i + ".txt")
        else:
            output["error"] = pop_i + " is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "")

    get_pops = "cat " + " ".join(pop_dirs) + " > " + \
        tmp_dir + "pops_" + request + ".txt"
    subprocess.call(get_pops, shell=True)

    # Get population ids
    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
    ids = []
    for i in range(len(pop_list)):
        ids.append(pop_list[i].strip())

    pop_ids = list(set(ids))

    # Extract query SNP phased genotypes
    vcf_filePath = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]["1000G_dir"], genome_build_vars[genome_build]["1000G_file"] % (snp_coord['chromosome']))
    vcf_file = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath)

    checkS3File(aws_info, config['aws']['bucket'], vcf_filePath)

    tabix_snp_h = export_s3_keys + " cd {1}; tabix -HD {0} | grep CHROM".format(vcf_file, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
    head = [x.decode('utf-8') for x in subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE).stdout.readlines()][0].strip().split()

    tabix_snp = export_s3_keys + " cd {4}; tabix -D {0} {1}:{2}-{2} | grep -v -e END > {3}".format(
        vcf_file, genome_build_vars[genome_build]['1000G_chr_prefix'] + snp_coord['chromosome'], snp_coord[genome_build_vars[genome_build]['position']], tmp_dir + "snp_no_dups_" + request + ".vcf", data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
    subprocess.call(tabix_snp, shell=True)

    # Check SNP is in the 1000G population, has the correct RS number, and not
    # monoallelic
    vcf = open(tmp_dir + "snp_no_dups_" + request + ".vcf").readlines()

    if len(vcf) == 0:
        output["error"] = snp + " is not in 1000G reference panel."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        subprocess.call("rm " + tmp_dir + "pops_" +
                        request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return("", "")

    elif len(vcf) > 1:
        geno = []
        for i in range(len(vcf)):
            if vcf[i].strip().split()[2] == snp:
                geno = vcf[i].strip().split()
                geno[0] = geno[0].lstrip('chr')
        if geno == []:
            output["error"] = snp + " is not in 1000G reference panel."
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            subprocess.call("rm " + tmp_dir + "pops_" +
                            request + ".txt", shell=True)
            subprocess.call("rm " + tmp_dir + "*" +
                            request + "*.vcf", shell=True)
            return("", "")

    else:
        geno = vcf[0].strip().split()
        geno[0] = geno[0].lstrip('chr')

    if geno[2] != snp and snp[0:2]=="rs" and "rs" in geno[2]:
            output["warning"] = "Genomic position for query variant (" + snp + \
                ") does not match RS number at 1000G position (chr" + \
                geno[0]+":"+geno[1]+" = "+geno[2]+")"
            snp = geno[2]

    if "," in geno[3] or "," in geno[4]:
        output["error"] = snp + " is not a biallelic variant."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        subprocess.call("rm " + tmp_dir + "pops_" +
                        request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return("", "")

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
        output["error"] = snp + \
            " is monoallelic in the " + pop + " population."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        subprocess.call("rm " + tmp_dir + "pops_" +
                        request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return("", "")

    # Define window of interest around query SNP
    # window = 500000
    coord1 = int(snp_coord[genome_build_vars[genome_build]['position']]) - window
    if coord1 < 0:
        coord1 = 0
    coord2 = int(snp_coord[genome_build_vars[genome_build]['position']]) + window
    print("")

    # Calculate proxy LD statistics in parallel
    # threads = 4
    # block = (2 * window) // 4
    # block = (2 * window) // num_subprocesses

    windowChunkRanges = chunkWindow(int(snp_coord[genome_build_vars[genome_build]['position']]), window, num_subprocesses)

    commands = []

    for subprocess_id in range(num_subprocesses):
        getWindowVariantsArgs = " ".join([str(web), str(snp), str(snp_coord['chromosome']), str(windowChunkRanges[subprocess_id][0]), str(windowChunkRanges[subprocess_id][1]), str(request), genome_build, str(subprocess_id)])
        commands.append("python3 LDproxy_sub.py " + getWindowVariantsArgs)

    processes = [subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE) for command in commands]

    # collect output in parallel
    def get_output(process):
        return process.communicate()[0].splitlines()

    if not hasattr(threading.current_thread(), "_children"):
        threading.current_thread()._children = weakref.WeakKeyDictionary()

    pool = Pool(len(processes))
    out_raw = pool.map(get_output, processes)
    pool.close()
    pool.join()

    # Aggregate output
    out_prox = []
    for i in range(len(out_raw)):
        for j in range(len(out_raw[i])):
            col = out_raw[i][j].decode('utf-8').strip().split("\t")
            col[6] = int(col[6])
            col[7] = float(col[7])
            col[8] = float(col[8])
            col.append(abs(int(col[6])))
            out_prox.append(col)

    # Sort output
    if r2_d not in ["r2", "d"]:
        if "warning" in output:
            output["warning"] = output["warning"] + ". " + r2_d + \
                " is not an acceptable value for r2_d (r2 or d required). r2 is used by default"
        else:
            output["warning"] = r2_d + \
                " is not an acceptable value for r2_d (r2 or d required). r2 is used by default"
        r2_d = "r2"

    out_dist_sort = sorted(out_prox, key=operator.itemgetter(14))

    if r2_d == "r2":
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(8), reverse=True)
    else:
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(7), reverse=True)

    # Populate JSON and text output
    outfile = open(tmp_dir + "proxy" + request + ".txt", "w")
    header = ["RS_Number", "Coord", "Alleles", "MAF", "Distance",
              "Dprime", "R2", "Correlated_Alleles", "RegulomeDB", "Function"]
    print("\t".join(header), file=outfile)

    ucsc_track = {}
    ucsc_track["header"] = ["chr", "pos", "rsid", "stat"]

    query_snp = {}
    query_snp["RS"] = out_ld_sort[0][3]
    query_snp["Alleles"] = out_ld_sort[0][1]
    query_snp["Coord"] = out_ld_sort[0][2]
    query_snp["Dist"] = out_ld_sort[0][6]
    query_snp["Dprime"] = str(round(float(out_ld_sort[0][7]), 4))
    query_snp["R2"] = str(round(float(out_ld_sort[0][8]), 4))
    query_snp["Corr_Alleles"] = out_ld_sort[0][9]
    query_snp["RegulomeDB"] = out_ld_sort[0][10]
    query_snp["MAF"] = str(round(float(out_ld_sort[0][11]), 4))
    query_snp["Function"] = out_ld_sort[0][13]

    output["query_snp"] = query_snp

    temp = [query_snp["RS"], query_snp["Coord"], query_snp["Alleles"], query_snp["MAF"], str(query_snp["Dist"]), str(
            query_snp["Dprime"]), str(query_snp["R2"]), query_snp["Corr_Alleles"], query_snp["RegulomeDB"], query_snp["Function"]]
    print("\t".join(temp), file=outfile)

    chr, pos = query_snp["Coord"].split(':')
    if r2_d == "r2":
        temp2 = [chr, pos, query_snp["RS"], query_snp["R2"]]
    else:
        temp2 = [chr, pos, query_snp["RS"], query_snp["Dprime"]]

    ucsc_track["query_snp"] = temp2

    ucsc_track["0.8-1.0"] = []
    ucsc_track["0.6-0.8"] = []
    ucsc_track["0.4-0.6"] = []
    ucsc_track["0.2-0.4"] = []
    ucsc_track["0.0-0.2"] = []

    proxies = {}
    rows = []
    digits = len(str(len(out_ld_sort)))

    for i in range(1, len(out_ld_sort)):
        if float(out_ld_sort[i][8]) > 0.01 and out_ld_sort[i][3] != snp:
            proxy_info = {}
            row = []
            proxy_info["RS"] = out_ld_sort[i][3]
            proxy_info["Alleles"] = out_ld_sort[i][4]
            proxy_info["Coord"] = out_ld_sort[i][5]
            proxy_info["Dist"] = out_ld_sort[i][6]
            proxy_info["Dprime"] = str(round(float(out_ld_sort[i][7]), 4))
            proxy_info["R2"] = str(round(float(out_ld_sort[i][8]), 4))
            proxy_info["Corr_Alleles"] = out_ld_sort[i][9]
            proxy_info["RegulomeDB"] = out_ld_sort[i][10]
            proxy_info["MAF"] = str(round(float(out_ld_sort[i][12]), 4))
            proxy_info["Function"] = out_ld_sort[i][13]
            proxies["proxy_" + (digits - len(str(i))) *
                    "0" + str(i)] = proxy_info
            chr, pos = proxy_info["Coord"].split(':')

            # Adding a row for the Data Table
            row.append(proxy_info["RS"])
            row.append(chr)
            row.append(pos)
            row.append(proxy_info["Alleles"])
            row.append(str(round(float(proxy_info["MAF"]), 4)))
            row.append(abs(proxy_info["Dist"]))
            row.append(str(round(float(proxy_info["Dprime"]), 4)))
            row.append(str(round(float(proxy_info["R2"]), 4)))
            row.append(proxy_info["Corr_Alleles"])
            row.append(proxy_info["RegulomeDB"])
            row.append("HaploReg link")
            row.append(proxy_info["Function"])
            rows.append(row)

            temp = [proxy_info["RS"], proxy_info["Coord"], proxy_info["Alleles"], proxy_info["MAF"], str(proxy_info["Dist"]), str(
                    proxy_info["Dprime"]), str(proxy_info["R2"]), proxy_info["Corr_Alleles"], proxy_info["RegulomeDB"], proxy_info["Function"]]
            print("\t".join(temp), file=outfile)

            chr, pos = proxy_info["Coord"].split(':')
            if r2_d == "r2":
                temp2 = [chr, pos, proxy_info["RS"],
                         round(float(out_ld_sort[i][8]), 4)]
            else:
                temp2 = [chr, pos, proxy_info["RS"],
                         round(float(out_ld_sort[i][7]), 4)]

            if 0.8 < temp2[3] <= 1.0:
                ucsc_track["0.8-1.0"].append(temp2)
            elif 0.6 < temp2[3] <= 0.8:
                ucsc_track["0.6-0.8"].append(temp2)
            elif 0.4 < temp2[3] <= 0.6:
                ucsc_track["0.4-0.6"].append(temp2)
            elif 0.2 < temp2[3] <= 0.4:
                ucsc_track["0.2-0.4"].append(temp2)
            else:
                ucsc_track["0.0-0.2"].append(temp2)

    track = open(tmp_dir + "track" + request + ".txt", "w")
    print("browser position chr" + \
        str(snp_coord['chromosome']) + ":" + str(coord1) + "-" + str(coord2), file=track)
    print("", file=track)

    if r2_d == "r2":
        print("track type=bedGraph name=\"R2 Plot\" description=\"Plot of R2 values\" color=50,50,50 visibility=full alwaysZero=on graphType=bar maxHeightPixels=60", file=track)
    else:
        print("track type=bedGraph name=\"D Prime Plot\" description=\"Plot of D prime values\" color=50,50,50 visibility=full alwaysZero=on graphType=bar maxHeightPixels=60", file=track)

    print("\t".join(
        [str(ucsc_track["query_snp"][i]) for i in [0, 1, 1, 3]]), file=track)
    if len(ucsc_track["0.8-1.0"]) > 0:
        for var in ucsc_track["0.8-1.0"]:
            print("\t".join([str(var[i]) for i in [0, 1, 1, 3]]), file=track)
    if len(ucsc_track["0.6-0.8"]) > 0:
        for var in ucsc_track["0.6-0.8"]:
            print("\t".join([str(var[i]) for i in [0, 1, 1, 3]]), file=track)
    if len(ucsc_track["0.4-0.6"]) > 0:
        for var in ucsc_track["0.4-0.6"]:
            print("\t".join([str(var[i]) for i in [0, 1, 1, 3]]), file=track)
    if len(ucsc_track["0.2-0.4"]) > 0:
        for var in ucsc_track["0.2-0.4"]:
            print("\t".join([str(var[i]) for i in [0, 1, 1, 3]]), file=track)
    if len(ucsc_track["0.0-0.2"]) > 0:
        for var in ucsc_track["0.0-0.2"]:
            print("\t".join([str(var[i]) for i in [0, 1, 1, 3]]), file=track)
    print("", file=track)

    print("track type=bed name=\"" + snp + \
        "\" description=\"Query Variant: " + snp + "\" color=108,108,255", file=track)
    print("\t".join([ucsc_track["query_snp"][i]
                               for i in [0, 1, 1, 2]]), file=track)
    print("", file=track)

    if len(ucsc_track["0.8-1.0"]) > 0:
        if r2_d == "r2":
            print("track type=bed name=\"0.8<R2<=1.0\" description=\"Proxy Variants with 0.8<R2<=1.0\" color=198,129,0", file=track)
        else:
            print("track type=bed name=\"0.8<D'<=1.0\" description=\"Proxy Variants with 0.8<D'<=1.0\" color=198,129,0", file=track)
        for var in ucsc_track["0.8-1.0"]:
            print("\t".join([var[i] for i in [0, 1, 1, 2]]), file=track)
        print("", file=track)

    if len(ucsc_track["0.6-0.8"]) > 0:
        if r2_d == "r2":
            print("track type=bed name=\"0.6<R2<=0.8\" description=\"Proxy Variants with 0.6<R2<=0.8\" color=198,129,0", file=track)
        else:
            print("track type=bed name=\"0.6<D'<=0.8\" description=\"Proxy Variants with 0.6<D'<=0.8\" color=198,129,0", file=track)
        for var in ucsc_track["0.6-0.8"]:
            print("\t".join([var[i] for i in [0, 1, 1, 2]]), file=track)
        print("", file=track)

    if len(ucsc_track["0.4-0.6"]) > 0:
        if r2_d == "r2":
            print("track type=bed name=\"0.4<R2<=0.6\" description=\"Proxy Variants with 0.4<R2<=0.6\" color=198,129,0", file=track)
        else:
            print("track type=bed name=\"0.4<D'<=0.6\" description=\"Proxy Variants with 0.4<D'<=0.6\" color=198,129,0", file=track)
        for var in ucsc_track["0.4-0.6"]:
            print("\t".join([var[i] for i in [0, 1, 1, 2]]), file=track)
        print("", file=track)

    if len(ucsc_track["0.2-0.4"]) > 0:
        if r2_d == "r2":
            print("track type=bed name=\"0.2<R2<=0.4\" description=\"Proxy Variants with 0.2<R2<=0.4\" color=198,129,0", file=track)
        else:
            print("track type=bed name=\"0.2<D'<=0.4\" description=\"Proxy Variants with 0.2<D'<=0.4\" color=198,129,0", file=track)
        for var in ucsc_track["0.2-0.4"]:
            print("\t".join([var[i] for i in [0, 1, 1, 2]]), file=track)
        print("", file=track)

    if len(ucsc_track["0.0-0.2"]) > 0:
        if r2_d == "r2":
            print("track type=bed name=\"0.0<R2<=0.2\" description=\"Proxy Variants with 0.0<R2<=0.2\" color=198,129,0", file=track)
        else:
            print("track type=bed name=\"0.0<D'<=0.2\" description=\"Proxy Variants with 0.0<D'<=0.2\" color=198,129,0", file=track)
        for var in ucsc_track["0.0-0.2"]:
            print("\t".join([var[i] for i in [0, 1, 1, 2]]), file=track)
        print("", file=track)

    output["aaData"] = rows
    output["proxy_snps"] = proxies

    # Output JSON and text file
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()

    outfile.close()
    track.close()

    out_script = ""
    out_div = ""
    
    if web:
        # Organize scatter plot data
        q_rs = []
        q_allele = []
        q_coord = []
        q_maf = []
        p_rs = []
        p_allele = []
        p_coord = []
        p_maf = []
        dist = []
        d_prime = []
        d_prime_round = []
        r2 = []
        r2_round = []
        corr_alleles = []
        regdb = []
        funct = []
        color = []
        size = []
        for i in range(len(out_ld_sort)):
            q_rs_i, q_allele_i, q_coord_i, p_rs_i, p_allele_i, p_coord_i, dist_i, d_prime_i, r2_i, corr_alleles_i, regdb_i, q_maf_i, p_maf_i, funct_i, dist_abs = out_ld_sort[
                i]

            if float(r2_i) > 0.01:
                q_rs.append(q_rs_i)
                q_allele.append(q_allele_i)
                q_coord.append(float(q_coord_i.split(":")[1]) / 1000000)
                q_maf.append(str(round(float(q_maf_i), 4)))
                if p_rs_i == ".":
                    p_rs_i = p_coord_i
                p_rs.append(p_rs_i)
                p_allele.append(p_allele_i)
                p_coord.append(float(p_coord_i.split(":")[1]) / 1000000)
                p_maf.append(str(round(float(p_maf_i), 4)))
                dist.append(str(round(dist_i / 1000000.0, 4)))
                d_prime.append(float(d_prime_i))
                d_prime_round.append(str(round(float(d_prime_i), 4)))
                r2.append(float(r2_i))
                r2_round.append(str(round(float(r2_i), 4)))
                corr_alleles.append(corr_alleles_i)

                # Correct Missing Annotations
                if regdb_i == ".":
                    regdb_i = ""
                regdb.append(regdb_i)
                if funct_i == ".":
                    funct_i = ""
                if funct_i == "NA":
                    funct_i = "none"
                funct.append(funct_i)

                # Set Color
                if i == 0:
                    color_i = "blue"
                elif funct_i != "none" and funct_i != "":
                    color_i = "red"
                else:
                    color_i = "orange"
                color.append(color_i)

                # Set Size
                size_i = 9 + float(p_maf_i) * 14.0
                size.append(size_i)

        # Begin Bokeh Plotting
        from collections import OrderedDict
        from bokeh.embed import components, file_html
        from bokeh.layouts import gridplot
        from bokeh.models import HoverTool, LinearAxis, Range1d
        from bokeh.plotting import ColumnDataSource, curdoc, figure, output_file, reset_output, save
        from bokeh.resources import CDN

        reset_output()

        # Proxy Plot
        x = p_coord
        if r2_d == "r2":
            y = r2
        else:
            y = d_prime
        whitespace = 0.01
        xr = Range1d(start=coord1 / 1000000.0 - whitespace,
                    end=coord2 / 1000000.0 + whitespace)
        yr = Range1d(start=-0.03, end=1.03)
        sup_2 = "\u00B2"

        proxy_plot = figure(
            title="Proxies for " + snp + " in " + pop,
            min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
            plot_width=900,
            plot_height=600,
            x_range=xr, y_range=yr,
            tools="hover,tap,pan,box_zoom,box_select,undo,redo,reset,previewsave", logo=None,
            toolbar_location="above")

        proxy_plot.title.align = "center"

        # Add recombination rate
        recomb_file = tmp_dir + "recomb_" + request + ".json"
        recomb_json = getRecomb(db, recomb_file, snp_coord['chromosome'], coord1 - whitespace, coord2 + whitespace, genome_build)

        recomb_x = []
        recomb_y = []

        for recomb_obj in recomb_json:
            recomb_x.append(int(recomb_obj[genome_build_vars[genome_build]['position']]) / 1000000.0)
            recomb_y.append(float(recomb_obj['rate']) / 100.0)

        data = {
            'x': x,
            'y': y,
            'qrs': q_rs,
            'q_alle': q_allele,
            'q_maf': q_maf,
            'prs': p_rs,
            'p_alle': p_allele,
            'p_maf': p_maf,
            'dist': dist,
            'r': r2_round,
            'd': d_prime_round,
            'alleles': corr_alleles,
            'regdb': regdb,
            'funct': funct,
            'size': size,
            'color': color
        }
        source = ColumnDataSource(data)

        proxy_plot.line(recomb_x, recomb_y, line_width=1, color="black", alpha=0.5)

        proxy_plot.circle(x='x', y='y', size='size',
                        color='color', alpha=0.5, source=source)

        hover = proxy_plot.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ("Query Variant", "@qrs @q_alle"),
            ("Proxy Variant", "@prs @p_alle"),
            ("Distance (Mb)", "@dist"),
            ("MAF (Query,Proxy)", "@q_maf,@p_maf"),
            ("R" + sup_2, "@r"),
            ("D\'", "@d"),
            ("Correlated Alleles", "@alleles"),
            ("RegulomeDB", "@regdb"),
            ("Functional Class", "@funct"),
        ])

        proxy_plot.text(x, y, text=regdb, alpha=1, text_font_size="7pt",
                        text_baseline="middle", text_align="center", angle=0)

        if r2_d == "r2":
            proxy_plot.yaxis.axis_label = "R" + sup_2
        else:
            proxy_plot.yaxis.axis_label = "D\'"

        proxy_plot.extra_y_ranges = {"y2_axis": Range1d(start=-3, end=103)}
        proxy_plot.add_layout(LinearAxis(y_range_name="y2_axis",
                                        axis_label="Combined Recombination Rate (cM/Mb)"), "right")

        # Rug Plot
        y2_ll = [-0.03] * len(x)
        y2_ul = [1.03] * len(x)
        yr_rug = Range1d(start=-0.03, end=1.03)

        data_rug = {
            'x': x,
            'y': y,
            'y2_ll': y2_ll,
            'y2_ul': y2_ul,
            'qrs': q_rs,
            'q_alle': q_allele,
            'q_maf': q_maf,
            'prs': p_rs,
            'p_alle': p_allele,
            'p_maf': p_maf,
            'dist': dist,
            'r': r2_round,
            'd': d_prime_round,
            'alleles': corr_alleles,
            'regdb': regdb,
            'funct': funct,
            'size': size,
            'color': color
        }
        source_rug = ColumnDataSource(data_rug)

        rug = figure(
            x_range=xr, y_range=yr_rug, border_fill_color='white', y_axis_type=None,
            title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
            plot_width=900, plot_height=50, tools="xpan,tap", logo=None)

        rug.segment(x0='x', y0='y2_ll', x1='x', y1='y2_ul', source=source_rug,
                    color='color', alpha=0.5, line_width=1)
        rug.toolbar_location = None

        if collapseTranscript == "false":
            # Gene Plot (All Transcripts)
            genes_file = tmp_dir + "genes_" + request + ".json"
            genes_json = getRefGene(db, genes_file, snp_coord['chromosome'], int(coord1), int(coord2), genome_build, False)

            genes_plot_start = []
            genes_plot_end = []
            genes_plot_y = []
            genes_plot_name = []
            exons_plot_x = []
            exons_plot_y = []
            exons_plot_w = []
            exons_plot_h = []
            exons_plot_name = []
            exons_plot_id = []
            exons_plot_exon = []
            lines = [0]
            gap = 80000
            tall = 0.75
            if genes_json != None and len(genes_json) > 0:
                for gene_obj in genes_json:
                    bin = gene_obj["bin"]
                    name_id = gene_obj["name"]
                    chrom = gene_obj["chrom"]
                    strand = gene_obj["strand"]
                    txStart = gene_obj["txStart"]
                    txEnd = gene_obj["txEnd"]
                    cdsStart = gene_obj["cdsStart"]
                    cdsEnd = gene_obj["cdsEnd"]
                    exonCount = gene_obj["exonCount"]
                    exonStarts = gene_obj["exonStarts"]
                    exonEnds = gene_obj["exonEnds"]
                    score = gene_obj["score"]
                    name2 = gene_obj["name2"]
                    cdsStartStat = gene_obj["cdsStartStat"]
                    cdsEndStat = gene_obj["cdsEndStat"] 
                    exonFrames = gene_obj["exonFrames"]
                    name = name2
                    id = name_id
                    e_start = exonStarts.split(",")
                    e_end = exonEnds.split(",")

                    # Determine Y Coordinate
                    i = 0
                    y_coord = None
                    while y_coord == None:
                        if i > len(lines) - 1:
                            y_coord = i + 1
                            lines.append(int(txEnd))
                        elif int(txStart) > (gap + lines[i]):
                            y_coord = i + 1
                            lines[i] = int(txEnd)
                        else:
                            i += 1

                    genes_plot_start.append(int(txStart) / 1000000.0)
                    genes_plot_end.append(int(txEnd) / 1000000.0)
                    genes_plot_y.append(y_coord)
                    genes_plot_name.append(name + "  ")

                    for i in range(len(e_start) - 1):
                        if strand == "+":
                            exon = i + 1
                        else:
                            exon = len(e_start) - 1 - i

                        width = (int(e_end[i]) - int(e_start[i])) / 1000000.0
                        x_coord = int(e_start[i]) / 1000000.0 + (width / 2)

                        exons_plot_x.append(x_coord)
                        exons_plot_y.append(y_coord)
                        exons_plot_w.append(width)
                        exons_plot_h.append(tall)
                        exons_plot_name.append(name)
                        exons_plot_id.append(id)
                        exons_plot_exon.append(exon)

            n_rows = len(lines)
            genes_plot_yn = [n_rows - x + 0.5 for x in genes_plot_y]
            exons_plot_yn = [n_rows - x + 0.5 for x in exons_plot_y]
            yr2 = Range1d(start=0, end=n_rows)

            data_gene_plot = {
                'exons_plot_x': exons_plot_x,
                'exons_plot_yn': exons_plot_yn,
                'exons_plot_w': exons_plot_w,
                'exons_plot_h': exons_plot_h,
                'exons_plot_name': exons_plot_name,
                'exons_plot_id': exons_plot_id,
                'exons_plot_exon': exons_plot_exon
            }

            source_gene_plot = ColumnDataSource(data_gene_plot)

            if len(lines) < 3:
                plot_h_pix = 250
            else:
                plot_h_pix = 250 + (len(lines) - 2) * 50

            gene_plot = figure(
                x_range=xr, y_range=yr2, border_fill_color='white',
                title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
                plot_width=900, plot_height=plot_h_pix, tools="hover,tap,xpan,box_zoom,undo,redo,reset,previewsave", logo=None)

            gene_plot.segment(genes_plot_start, genes_plot_yn, genes_plot_end,
                            genes_plot_yn, color="black", alpha=1, line_width=2)

            gene_plot.rect(x='exons_plot_x', y='exons_plot_yn', width='exons_plot_w', height='exons_plot_h',
                        source=source_gene_plot, fill_color="grey", line_color="grey")
            gene_plot.xaxis.axis_label = "Chromosome " + snp_coord['chromosome'] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
            gene_plot.yaxis.axis_label = "Genes (All Transcripts)"
            gene_plot.ygrid.grid_line_color = None
            gene_plot.yaxis.axis_line_color = None
            gene_plot.yaxis.minor_tick_line_color = None
            gene_plot.yaxis.major_tick_line_color = None
            gene_plot.yaxis.major_label_text_color = None

            hover = gene_plot.select(dict(type=HoverTool))
            hover.tooltips = OrderedDict([
                ("Gene", "@exons_plot_name"),
                ("ID", "@exons_plot_id"),
                ("Exon", "@exons_plot_exon"),
            ])

            gene_plot.text(genes_plot_start, genes_plot_yn, text=genes_plot_name, alpha=1, text_font_size="7pt",
                        text_font_style="bold", text_baseline="middle", text_align="right", angle=0)

            gene_plot.toolbar_location = "below"

            # Combine plots into a grid
            out_grid = gridplot(proxy_plot, rug, gene_plot, ncols=1,
                                toolbar_options=dict(logo=None))
        # Gene Plot (Collapsed)                        
        else:
            genes_c_file = tmp_dir + "genes_c_" + request + ".json"
            genes_c_json = getRefGene(db, genes_c_file, snp_coord['chromosome'], int(coord1), int(coord2), genome_build, True)

            genes_c_plot_start=[]
            genes_c_plot_end=[]
            genes_c_plot_y=[]
            genes_c_plot_name=[]
            exons_c_plot_x=[]
            exons_c_plot_y=[]
            exons_c_plot_w=[]
            exons_c_plot_h=[]
            exons_c_plot_name=[]
            exons_c_plot_id=[]
            message_c = ["Too many genes to plot."]
            lines_c=[0]
            gap=80000
            tall=0.75
            if genes_c_json != None and len(genes_c_json) > 0:
                for gene_c_obj in genes_c_json:
                    chrom = gene_c_obj["chrom"]
                    txStart = gene_c_obj["txStart"]
                    txEnd = gene_c_obj["txEnd"]
                    exonStarts = gene_c_obj["exonStarts"]
                    exonEnds = gene_c_obj["exonEnds"]
                    name2 = gene_c_obj["name2"]
                    transcripts = gene_c_obj["transcripts"]
                    name = name2
                    e_start = exonStarts.split(",")
                    e_end = exonEnds.split(",")
                    e_transcripts=transcripts.split(",")

                    # Determine Y Coordinate
                    i=0
                    y_coord=None
                    while y_coord==None:
                        if i>len(lines_c)-1:
                            y_coord=i+1
                            lines_c.append(int(txEnd))
                        elif int(txStart)>(gap+lines_c[i]):
                            y_coord=i+1
                            lines_c[i]=int(txEnd)
                        else:
                            i+=1

                    genes_c_plot_start.append(int(txStart)/1000000.0)
                    genes_c_plot_end.append(int(txEnd)/1000000.0)
                    genes_c_plot_y.append(y_coord)
                    genes_c_plot_name.append(name+"  ")

                    # for i in range(len(e_start)):
                    for i in range(len(e_start)-1):
                        width=(int(e_end[i])-int(e_start[i]))/1000000.0
                        x_coord=int(e_start[i])/1000000.0+(width/2)

                        exons_c_plot_x.append(x_coord)
                        exons_c_plot_y.append(y_coord)
                        exons_c_plot_w.append(width)
                        exons_c_plot_h.append(tall)
                        exons_c_plot_name.append(name)
                        exons_c_plot_id.append(e_transcripts[i].replace("-",","))


            n_rows_c=len(lines_c)
            genes_c_plot_yn=[n_rows_c-x+0.5 for x in genes_c_plot_y]
            exons_c_plot_yn=[n_rows_c-x+0.5 for x in exons_c_plot_y]
            yr2_c=Range1d(start=0, end=n_rows_c)

            data_gene_c_plot = {'exons_c_plot_x': exons_c_plot_x, 'exons_c_plot_yn': exons_c_plot_yn, 'exons_c_plot_w': exons_c_plot_w, 'exons_c_plot_h': exons_c_plot_h, 'exons_c_plot_name': exons_c_plot_name, 'exons_c_plot_id': exons_c_plot_id}
            source_gene_c_plot=ColumnDataSource(data_gene_c_plot)

            max_genes_c = 40
            # if len(lines_c) < 3 or len(genes_c_raw) > max_genes_c:
            if len(lines_c) < 3:
                plot_c_h_pix = 250
            else:
                plot_c_h_pix = 250 + (len(lines_c) - 2) * 50

            gene_c_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
                            x_range=xr, y_range=yr2_c, border_fill_color='white',
                            title="", h_symmetry=False, v_symmetry=False, logo=None,
                            plot_width=900, plot_height=plot_c_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,previewsave")

            # if len(genes_c_raw) <= max_genes_c:
            gene_c_plot.segment(genes_c_plot_start, genes_c_plot_yn, genes_c_plot_end,
                                genes_c_plot_yn, color="black", alpha=1, line_width=2)
            gene_c_plot.rect(x='exons_c_plot_x', y='exons_c_plot_yn', width='exons_c_plot_w', height='exons_c_plot_h',
                            source=source_gene_c_plot, fill_color="grey", line_color="grey")
            gene_c_plot.text(genes_c_plot_start, genes_c_plot_yn, text=genes_c_plot_name, alpha=1, text_font_size="7pt",
                            text_font_style="bold", text_baseline="middle", text_align="right", angle=0)
            hover = gene_c_plot.select(dict(type=HoverTool))
            hover.tooltips = OrderedDict([
                ("Gene", "@exons_c_plot_name"),
                ("Transcript IDs", "@exons_c_plot_id"),
            ])

            # else:
            # 	x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
            # 	gene_c_plot.text(x_coord_text, n_rows_c / 2.0, text=message_c, alpha=1,
            # 				   text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

            gene_c_plot.xaxis.axis_label = "Chromosome " + snp_coord['chromosome'] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
            gene_c_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
            gene_c_plot.ygrid.grid_line_color = None
            gene_c_plot.yaxis.axis_line_color = None
            gene_c_plot.yaxis.minor_tick_line_color = None
            gene_c_plot.yaxis.major_tick_line_color = None
            gene_c_plot.yaxis.major_label_text_color = None

            gene_c_plot.toolbar_location = "below"
            
            out_grid = gridplot(proxy_plot, rug, gene_c_plot,
                        ncols=1, toolbar_options=dict(logo=None))

        # Generate high quality images only if accessed via web instance
        
        # Open thread for high quality image exports
        command = "python3 LDproxy_plot_sub.py " + snp + " " + pop + " " + request + " " + genome_build + " " + r2_d + " " + str(window) + " " + collapseTranscript
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        ###########################
        # Html output for testing #
        ###########################
        #html=file_html(out_grid, CDN, "Test Plot")
        # out_html=open("LDproxy.html","w")
        #print >> out_html, html
        # out_html.close()

        out_script, out_div = components(out_grid, CDN)
        reset_output()

        # Print run time statistics
        pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
        print("\nNumber of Individuals: " + str(len(pop_list)))

        print("SNPs in Region: " + str(len(out_prox)))

        duration = time.time() - start_time
        print("Run time: " + str(duration) + " seconds\n")

    # Return plot output
    return(out_script, out_div)

def main():
    tmp_dir = "./tmp/"

    # Import LDproxy options
    if len(sys.argv) == 5:
        snp = sys.argv[1]
        pop = sys.argv[2]
        request = False
        web = sys.argv[4]
        r2_d = "r2"
        window = 500000
        collapseTranscript = True
    elif len(sys.argv) == 6:
        snp = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        web = sys.argv[4]
        r2_d = sys.argv[5]
        window = 500000
        collapseTranscript = True
    else:
        print("Correct useage is: LDproxy.py snp populations request (optional: r2_d)")
        sys.exit()

    # Run function
    out_script, out_div, error_msg = calculate_proxy(snp, pop, request, web, r2_d, window, collapseTranscript)

    # Print output
    with open(tmp_dir + "proxy" + request + ".json") as f:
        json_dict = json.load(f)
    try:
        json_dict["error"]

    except KeyError:
        head = ["RS_Number", "Coord", "Alleles", "MAF", "Distance", "Dprime",
                "R2", "Correlated_Alleles", "RegulomeDB", "Functional_Class"]
        print("\t".join(head))
        temp = [json_dict["query_snp"]["RS"], json_dict["query_snp"]["Coord"], json_dict["query_snp"]["Alleles"], json_dict["query_snp"]["MAF"], str(json_dict["query_snp"]["Dist"]), str(
                json_dict["query_snp"]["Dprime"]), str(json_dict["query_snp"]["R2"]), json_dict["query_snp"]["Corr_Alleles"], json_dict["query_snp"]["RegulomeDB"], json_dict["query_snp"]["Function"]]
        print("\t".join(temp))
        for k in sorted(json_dict["proxy_snps"].keys())[0:10]:
            temp = [json_dict["proxy_snps"][k]["RS"], json_dict["proxy_snps"][k]["Coord"], json_dict["proxy_snps"][k]["Alleles"], json_dict["proxy_snps"][k]["MAF"], str(json_dict["proxy_snps"][k]["Dist"]), str(
                    json_dict["proxy_snps"][k]["Dprime"]), str(json_dict["proxy_snps"][k]["R2"]), json_dict["proxy_snps"][k]["Corr_Alleles"], json_dict["proxy_snps"][k]["RegulomeDB"], json_dict["proxy_snps"][k]["Function"]]
            print("\t".join(temp))
        print("")

    else:
        print("")
        print(json_dict["error"])
        print("")

    try:
        json_dict["warning"]
    except KeyError:
        print("")
    else:
        print("WARNING: " + json_dict["warning"] + "!")
        print("")


if __name__ == "__main__":
    main()
