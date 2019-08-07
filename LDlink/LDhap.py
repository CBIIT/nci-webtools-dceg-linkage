#!/usr/bin/env python
import yaml
import json
import math
import operator
import os
# import sqlite3
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = contents[0].split('=')[1]
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])


# Create LDhap function
def calculate_hap(snplst, pop, request, web):

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    # snp_dir = config['data']['snp_dir']
    # snp_chr_dir = config['data']['snp_chr_dir']
    # snp_pos_offset = config['data']['snp_pos_offset']
    dbsnp_version = config['data']['dbsnp_version']
    pop_dir = config['data']['pop_dir']
    vcf_dir = config['data']['vcf_dir']

    tmp_dir = "./tmp/"

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    output = {}

    # Open SNP list file
    snps_raw = open(snplst).readlines()
    if len(snps_raw) > 30:
        output["error"] = "Maximum variant list is 30 RS numbers or coordinates. Your list contains " + \
            str(len(snps_raw))+" entries."
        return(json.dumps(output, sort_keys=True, indent=2))

    print "PRINT SNP LIST RAW ##########################"
    print "snps raw", snps_raw

    # Remove duplicate RS numbers and cast to lower case
    snps = []
    for snp_raw in snps_raw:
        snp = snp_raw.lower().strip().split()
        if snp not in snps:
            snps.append(snp)

    print "PRINT SNP LIST ##########################"
    print "snps", snps

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(pop_dir+pop_i+".txt")
        else:
            output["error"] = pop_i+" is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            return(json.dumps(output, sort_keys=True, indent=2))

    get_pops = "cat " + " ".join(pop_dirs)
    proc = subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE)
    pop_list = proc.stdout.readlines()

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    # # Connect to snp database
    # conn = sqlite3.connect(snp_dir)
    # conn.text_factory = str
    # cur = conn.cursor()

    # # Connect to snp chr database for genomic coordinates queries
    # conn_chr = sqlite3.connect(snp_chr_dir)
    # conn_chr.text_factory = str
    # cur_chr = conn_chr.cursor()

    # Connect to Mongo snp database
    if web:
        client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
    else:
        client = MongoClient('localhost', port)
    db = client["LDLink"]

    def get_coords(db, rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp151.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized
        # rsid = rsid.strip("rs")
        # t = (rsid,)
        # cur.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
        # return cur.fetchone()

    # Query genomic coordinates
    def get_rsnum(db, coord):
        temp_coord = coord.strip("chr").split(":")
        chro = temp_coord[0]
        pos = temp_coord[1]
        query_results = db.dbsnp151.find({"chromosome": chro.upper() if chro == 'x' or chro == 'y' else chro, "position": pos})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized
        # t = (pos,)
        # cur_chr.execute("SELECT * FROM chr_"+chro+" WHERE position=?", t)
        # return cur_chr.fetchone()

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coords_rsid(db, snp_lst):
        new_snp_lst = []
        for snp_raw_i in snp_lst:
            if snp_raw_i[0][0:2] == "rs":
                new_snp_lst.append(snp_raw_i)
            else:
                snp_info_lst = get_rsnum(db, snp_raw_i[0])
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

    snps = replace_coords_rsid(db, snps)
    print "SNP INPUT LIST AFTER replace_coords_rsid(db, snps)"
    print str(snps)
    # Find RS numbers and genomic coords in snp database
    rs_nums = []
    snp_pos = []
    snp_coords = []
    warn = []
    tabix_coords = ""
    for snp_i in snps:
        if len(snp_i) > 0:  # Length entire list of snps
            if len(snp_i[0]) > 2:  # Length of each snp in snps
                # Check first two charcters are rs and last charcter of each snp
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                    snp_coord = get_coords(db, snp_i[0])
                    print "SNP_COORD"
                    print snp_coord
                    if snp_coord != None:
                        rs_nums.append(snp_i[0])
                        snp_pos.append(snp_coord['position'])
                        temp = [snp_i[0], snp_coord['chromosome'], snp_coord['position']]
                        snp_coords.append(temp)
                    else:
                        warn.append(snp_i[0])
                else:
                    warn.append(snp_i[0])
            else:
                warn.append(snp_i[0])

    # # Close snp connection
    # cur.close()
    # conn.close()

    # # Close snp chr connection
    # cur_chr.close()
    # conn_chr.close()

    if warn != []:
        output["warning"] = "The following RS number(s) or coordinate(s) were not found in dbSNP " + \
            dbsnp_version + ": " + ", ".join(warn)

    if len(rs_nums) == 0:
        output["error"] = "Input variant list does not contain any valid RS numbers that are in dbSNP " + \
            dbsnp_version + "."
        return(json.dumps(output, sort_keys=True, indent=2))

    # Check SNPs are all on the same chromosome
    for i in range(len(snp_coords)):
        if snp_coords[0][1] != snp_coords[i][1]:
            output["error"] = "Not all input variants are on the same chromosome: "+snp_coords[i-1][0]+"=chr" + \
                str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0] + \
                "=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+"."
            return(json.dumps(output, sort_keys=True, indent=2))

    # Check max distance between SNPs
    distance_bp = []
    for i in range(len(snp_coords)):
        distance_bp.append(int(snp_coords[i][2]))
    distance_max = max(distance_bp)-min(distance_bp)
    if distance_max > 1000000:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". Switch rate errors become more common as distance between query variants increases (Query range = "+str(
                    distance_max)+" bp)"
        else:
            output["warning"] = "Switch rate errors become more common as distance between query variants increases (Query range = "+str(
                distance_max)+" bp)"

    # Sort coordinates and make tabix formatted coordinates
    snp_pos_int = [int(i) for i in snp_pos]
    snp_pos_int.sort()
    snp_coord_str = [snp_coords[0][1]+":" +
                     str(i)+"-"+str(i) for i in snp_pos_int]
    tabix_coords = " "+" ".join(snp_coord_str)

    # Extract 1000 Genomes phased genotypes
    vcf_file = vcf_dir + \
        snp_coords[0][1] + \
        ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
    tabix_snps = "tabix -fh {0}{1} | grep -v -e END".format(
        vcf_file, tabix_coords)
    proc = subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE)

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

    # Import SNP VCF files
    vcf = proc.stdout.readlines()

    # Make sure there are genotype data in VCF file
    if vcf[-1][0:6] == "#CHROM":
        output["error"] = "No query variants were found in 1000G VCF file"
        return(json.dumps(output, sort_keys=True, indent=2))

    h = 0
    while vcf[h][0:2] == "##":
        h += 1

    head = vcf[h].strip().split()

    # Extract haplotypes
    index = []
    for i in range(9, len(head)):
        if head[i] in pop_ids:
            index.append(i)

    hap1 = [[]]
    for i in range(len(index)-1):
        hap1.append([])
    hap2 = [[]]
    for i in range(len(index)-1):
        hap2.append([])

    rsnum_lst = []
    allele_lst = []
    pos_lst = []

    for g in range(h+1, len(vcf)):
        geno = vcf[g].strip().split()
        if geno[1] not in snp_pos:
            if "warning" in output:
                output["warning"] = output["warning"]+". Genomic position ("+geno[1]+") in VCF file does not match db" + \
                    dbsnp_version + " search coordinates for query variant"
            else:
                output["warning"] = "Genomic position ("+geno[1]+") in VCF file does not match db" + \
                    dbsnp_version + " search coordinates for query variant"
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
                print "geno_next", geno_next
                if rs_query == geno_next[2]:
                    found = "true"
                    break
                count += 1

            if found == "false":
                if "warning" in output:
                    output["warning"] = output["warning"] + \
                        ". Genomic position for query variant ("+rs_query + \
                        ") does not match RS number at 1000G position (chr" + \
                        geno[0]+":"+geno[1]+")"
                else:
                    output["warning"] = "Genomic position for query variant ("+rs_query + \
                        ") does not match RS number at 1000G position (chr" + \
                        geno[0]+":"+geno[1]+")"

                indx = [i[0] for i in snps].index(rs_query)
                # snps[indx][0]=geno[2]
                # rsnum=geno[2]
                snps[indx][0] = rs_query
                rsnum = rs_query
            else:
                continue

        if "," not in geno[3] and "," not in geno[4]:
            a1, a2 = set_alleles(geno[3], geno[4])
            count0 = 0
            count1 = 0
            for i in range(len(index)):
                if geno[index[i]] == "0|0":
                    hap1[i].append(a1)
                    hap2[i].append(a1)
                    count0 += 2
                elif geno[index[i]] == "0|1":
                    hap1[i].append(a1)
                    hap2[i].append(a2)
                    count0 += 1
                    count1 += 1
                elif geno[index[i]] == "1|0":
                    hap1[i].append(a2)
                    hap2[i].append(a1)
                    count0 += 1
                    count1 += 1
                elif geno[index[i]] == "1|1":
                    hap1[i].append(a2)
                    hap2[i].append(a2)
                    count1 += 2
                elif geno[index[i]] == "0":
                    hap1[i].append(a1)
                    hap2[i].append(".")
                    count0 += 1
                elif geno[index[i]] == "1":
                    hap1[i].append(a2)
                    hap2[i].append(".")
                    count1 += 1
                else:
                    hap1[i].append(".")
                    hap2[i].append(".")

            rsnum_lst.append(rsnum)

            position = "chr"+geno[0]+":"+geno[1]
            pos_lst.append(position)

            f0 = round(float(count0)/(count0+count1), 4)
            f1 = round(float(count1)/(count0+count1), 4)
            if f0 >= f1:
                alleles = a1+"="+str(round(f0, 3))+", " + \
                    a2+"="+str(round(f1, 3))
            else:
                alleles = a2+"="+str(round(f1, 3))+", " + \
                    a1+"="+str(round(f0, 3))
            allele_lst.append(alleles)

    haps = {}
    for i in range(len(index)):
        h1 = "_".join(hap1[i])
        h2 = "_".join(hap2[i])
        if h1 in haps:
            haps[h1] += 1
        else:
            haps[h1] = 1

        if h2 in haps:
            haps[h2] += 1
        else:
            haps[h2] = 1

    # Remove Missing Haplotypes
    keys = haps.keys()
    for key in keys:
        if "." in key:
            haps.pop(key, None)

    # Sort results
    results = []
    for hap in haps:
        temp = [hap, haps[hap]]
        results.append(temp)

    total_haps = sum(haps.values())

    results_sort1 = sorted(results, key=operator.itemgetter(0))
    results_sort2 = sorted(
        results_sort1, key=operator.itemgetter(1), reverse=True)

    # Generate JSON output
    digits = len(str(len(results_sort2)))
    haps_out = {}
    for i in range(len(results_sort2)):
        hap_info = {}
        hap_info["Haplotype"] = results_sort2[i][0]
        hap_info["Count"] = results_sort2[i][1]
        hap_info["Frequency"] = round(float(results_sort2[i][1])/total_haps, 4)
        haps_out["haplotype_"+(digits-len(str(i+1)))*"0"+str(i+1)] = hap_info
    output["haplotypes"] = haps_out

    digits = len(str(len(rsnum_lst)))
    snps_out = {}
    for i in range(len(rsnum_lst)):
        snp_info = {}
        snp_info["RS"] = rsnum_lst[i]
        snp_info["Alleles"] = allele_lst[i]
        snp_info["Coord"] = pos_lst[i]
        snps_out["snp_"+(digits-len(str(i+1)))*"0"+str(i+1)] = snp_info
    output["snps"] = snps_out

    # Create SNP File
    snp_out = open(tmp_dir+"snps_"+request+".txt", "w")
    print >> snp_out, "RS_Number\tPosition (hg19)\tAllele Frequency"
    for k in sorted(output["snps"].keys()):
        rs_k = output["snps"][k]["RS"]
        coord_k = output["snps"][k]["Coord"]
        alleles_k0 = output["snps"][k]["Alleles"].strip(" ").split(",")
        alleles_k1 = alleles_k0[0]+"0"*(7-len(str(alleles_k0[0]))) + \
            ","+alleles_k0[1]+"0"*(8-len(str(alleles_k0[1])))
        temp_k = [rs_k, coord_k, alleles_k1]
        print >> snp_out, "\t".join(temp_k)
    snp_out.close()

    # Create Haplotype File
    hap_out = open(tmp_dir+"haplotypes_"+request+".txt", "w")
    print >> hap_out, "Haplotype\tCount\tFrequency"
    for k in sorted(output["haplotypes"].keys()):
        hap_k = output["haplotypes"][k]["Haplotype"]
        count_k = str(output["haplotypes"][k]["Count"])
        freq_k = str(output["haplotypes"][k]["Frequency"])
        temp_k = [hap_k, count_k, freq_k]
        print >> hap_out, "\t".join(temp_k)
    hap_out.close()

    # Return JSON output
    return(json.dumps(output, sort_keys=True, indent=2))


def main():
    import json
    import sys

    # Import LDLink options
    if len(sys.argv) == 4:
        snplst = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        web = sys.argv[4]
    else:
        print "Correct useage is: LDLink.py snplst populations request false"
        sys.exit()

    # Run function
    out_json = calculate_hap(snplst, pop, request, web)

    # Print output
    json_dict = json.loads(out_json)

    try:
        json_dict["error"]

    except KeyError:
        hap_lst = []
        hap_count = []
        hap_freq = []
        for k in sorted(json_dict["haplotypes"].keys()):
            hap_lst.append(json_dict["haplotypes"][k]["Haplotype"])
            hap_count.append(
                " "*(6-len(str(json_dict["haplotypes"][k]["Count"])))+str(json_dict["haplotypes"][k]["Count"]))
            hap_freq.append(str(json_dict["haplotypes"][k]["Frequency"])+"0"*(
                6-len(str(json_dict["haplotypes"][k]["Frequency"]))))

        # Only print haplotypes >1 percent frequency
        freq_count = 0
        for i in range(len(hap_freq)):
            if float(hap_freq[i]) >= 0.01:
                freq_count += 1

        hap_snp = []
        for i in range(len(hap_lst[0].split("_"))):
            temp = []
            for j in range(freq_count):  # use "len(hap_lst)" for all haplotypes
                temp.append(hap_lst[j].split("_")[i])
            hap_snp.append(temp)

        print ""
        print "RS Number     Coordinates      Allele Frequency      Common Haplotypes (>1%)"
        print ""
        counter = 0
        for k in sorted(json_dict["snps"].keys()):
            rs_k = json_dict["snps"][k]["RS"]+" " * \
                (11-len(str(json_dict["snps"][k]["RS"])))
            coord_k = json_dict["snps"][k]["Coord"]+" " * \
                (14-len(str(json_dict["snps"][k]["Coord"])))
            alleles_k0 = json_dict["snps"][k]["Alleles"].strip(" ").split(",")
            alleles_k1 = alleles_k0[0]+"0"*(7-len(str(alleles_k0[0]))) + \
                ","+alleles_k0[1]+"0"*(8-len(str(alleles_k0[1])))
            temp_k = [rs_k, coord_k, alleles_k1,
                      "   "+"      ".join(hap_snp[counter])]
            print "   ".join(temp_k)
            counter += 1

        print ""
        print "                                         Count: " + \
            " ".join(hap_count[0:freq_count])
        print "                                     Frequency: " + \
            " ".join(hap_freq[0:freq_count])

        try:
            json_dict["warning"]
        except KeyError:
            print ""
        else:
            print ""
            print "WARNING: "+json_dict["warning"]+"!"
            print ""

    else:
        print ""
        print json_dict["error"]
        print ""


if __name__ == "__main__":
    main()
