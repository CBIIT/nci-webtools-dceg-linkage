#!/usr/bin/env python
import json
import math
import operator
import os
import sqlite3
import subprocess
import sys
import yaml

# SNPtip
# Locate genomic location and SNP annotation

# Create SNPtip function


def calculate_tip(snplst, request):

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    dbsnp_version = config['data']['dbsnp_version']
    gene_dir = config['data']['gene_dir']
    snp_dir = config['data']['snp_dir']
    snp_pos_offset = config['data']['snp_pos_offset']
    pop_dir = config['data']['pop_dir']
    vcf_dir = config['data']['vcf_dir']

    tmp_dir = "./tmp/"

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    out_json = open(tmp_dir+"matrix"+request+".json", "w")
    output = {}

    # Open SNP list file
    snps_raw = open(snplst).readlines()
    max_list = 5000
    if len(snps_raw) > max_list:
        output["error"] = "Maximum SNP list is " + \
            str(max_list)+" RS numbers. Your list contains " + \
            str(len(snps_raw))+" entries."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print >> out_json, json_output
        out_json.close()
        return("")

    # Remove duplicate RS numbers
    snps = []
    for snp_raw in snps_raw:
        snp = snp_raw.strip().split()
        if snp not in snps:
            snps.append(snp)

    # Connect to snp database
    conn = sqlite3.connect(snp_dir)
    conn.text_factory = str
    cur = conn.cursor()

    # Connect to snp chr database for genomic coordinates queries
    conn_chr = sqlite3.connect(snp_chr_dir)
    conn_chr.text_factory = str
    cur_chr = conn_chr.cursor()

    def get_coords(rs):
        id = rs.strip("rs")
        t = (id,)
        cur.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
        return cur.fetchone()

    # Query genomic coordinates
    def get_rsnum(coord):
        temp_coord = coord.strip("chr").split(":")
        chro = temp_coord[0]
        pos = str(int(temp_coord[1]) - 1)
        t = (pos,)
        cur_chr.execute("SELECT * FROM chr_"+chro+" WHERE position=?", t)
        return cur_chr.fetchone()

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coord_rsid(snp_lst):
        new_snp_lst = []
        for snp_raw_i in snp_lst:
            if snp_raw_i[0][0:2] == "rs":
                new_snp_lst.append(snp_raw_i)
            else:
                snp_info = get_rsnum(snp_raw_i[0])
                if snp_info != None:
                    var_id = "rs" + str(snp_info[0])
                    new_snp_lst.append([var_id])
                else:
                    new_snp_lst.append(snp_raw_i)
        return new_snp_lst

    snps = replace_coord_rsid(snps)

    # Find RS numbers in snp database
    snp_coords = []
    warn = []
    for snp_i in snps:
        if len(snp_i) > 0:
            if len(snp_i[0]) > 2:
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                    snp_coord = get_coords(snp_i[0])
                    if snp_coord != None:
                        chr = snp_coord[1]
                        if chr == "X":
                            chr = "23"
                        if chr == "Y":
                            chr = "24"
                        # if new dbSNP151 position is 1 off
                        temp = [snp_i[0], int(chr), int(
                            snp_coord[2]) + snp_pos_offset]
                        snp_coords.append(temp)
                    else:
                        warn.append(snp_i[0])
                else:
                    warn.append(snp_i[0])
            else:
                warn.append(snp_i[0])

    # Close snp connection
    cur.close()

    # Close snp chr connection
    cur_chr.close()
    conn_chr.close()

    if warn != []:
        output["warning"] = "The following RS number(s) or coordinate(s) were not found in dbSNP " + \
            dbsnp_version + ": " + ", ".join(warn)

    if len(snp_coords) == 0:
        output["error"] = "Input SNP list does not contain any valid RS numbers that are in dbSNP " + \
            dbsnp_version + "."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print >> out_json, json_output
        out_json.close()
        return("")

    # Sort by chromosome and position
    from operator import itemgetter
    snp_sorted = sorted(snp_coords, key=itemgetter(1, 2))

    # Convert back to X and Y
    snp_sorted_chr = []
    for i in snp_sorted:
        if i[1] == 23:
            chr = "X"
        elif i[1] == 24:
            chr = "Y"
        else:
            chr = i[1]
        temp = [i[0], str(chr), str(i[2])]
        snp_sorted_chr.append(temp)

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print >> out_json, json_output
    out_json.close()
    return(snp_sorted_chr)


def main():
    import json
    import sys
    tmp_dir = "./tmp/"

    # Import LDmatrix options
    if len(sys.argv) == 3:
        snplst = sys.argv[1]
        request = sys.argv[2]
    else:
        print "Correct useage is: SNPtip.py snplst request"
        sys.exit()

    # Run function
    out_info = calculate_tip(snplst, request)

    # Print output
    with open(tmp_dir+"matrix"+request+".json") as f:
        json_dict = json.load(f)

    try:
        json_dict["error"]

    except KeyError:
        print ""
        header = "RS Number\tChromosome\tPosition(GRCh37)"
        print header
        for i in out_info:
            print "\t".join(i)

        try:
            json_dict["warning"]

        except KeyError:
            print ""
        else:
            print ""
            print "WARNING: "+json_dict["warning"]+"."
            print ""

    else:
        print ""
        print json_dict["error"]
        print ""


if __name__ == "__main__":
    main()
