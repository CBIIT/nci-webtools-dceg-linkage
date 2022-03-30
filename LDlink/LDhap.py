#!/usr/bin/env python3

import yaml
import json
import operator
from bson import json_util
import subprocess
import sys
from LDcommon import checkS3File, connectMongoDBReadOnly, genome_build_vars, retrieveTabix1000GData

# Create LDhap function
def calculate_hap(snplst, pop, request, web, genome_build):
    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    dbsnp_version = config['data']['dbsnp_version']
    data_dir = config['data']['data_dir']
    tmp_dir = config['data']['tmp_dir']
    population_samples_dir = config['data']['population_samples_dir']
    genotypes_dir = config['data']['genotypes_dir']
    aws_info = config['aws']

    # Create JSON output
    output = {}

    # Validate genome build param
    if genome_build not in genome_build_vars['vars']:
        output["error"] = "Invalid genome build. Please specify either " + ", ".join(genome_build_vars['vars']) + ". " + str(output["warning"] if "warning" in output else "")
        return(json.dumps(output, sort_keys=True, indent=2))

    # Open Inputted SNPs list file
    snps_raw = open(snplst).readlines()
    if len(snps_raw) > 30:
        output["error"] = "Maximum variant list is 30 RS numbers or coordinates. Your list contains " + \
            str(len(snps_raw))+" entries. " + str(output["warning"] if "warning" in output else "")
        return(json.dumps(output, sort_keys=True, indent=2))

    # Remove duplicate RS numbers and cast to lower case
    snps = []
    for snp_raw in snps_raw:
        snp = snp_raw.lower().strip().split()
        if snp not in snps:
            snps.append(snp)

    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(data_dir + population_samples_dir + pop_i + ".txt")
        else:
            output["error"] = pop_i+" is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI. " + str(output["warning"] if "warning" in output else "")
            return(json.dumps(output, sort_keys=True, indent=2))

    get_pops = "cat " + " ".join(pop_dirs)
    pop_list = [x.decode('utf-8') for x in subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    db = connectMongoDBReadOnly(web)

    def get_coords(db, rsid):
        rsid = rsid.strip("rs")
        query_results = db.dbsnp.find_one({"id": rsid})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Query genomic coordinates
    def get_rsnum(db, coord):
        temp_coord = coord.strip("chr").split(":")
        chro = temp_coord[0]
        pos = temp_coord[1]
        query_results = db.dbsnp.find({"chromosome": chro.upper() if chro == 'x' or chro == 'y' else str(chro), genome_build_vars[genome_build]['position']: str(pos)})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coords_rsid(db, snp_lst):
        new_snp_lst = []
        for snp_raw_i in snp_lst:
            if snp_raw_i[0][0:2] == "rs":
                new_snp_lst.append(snp_raw_i)
            else:
                snp_info_lst = get_rsnum(db, snp_raw_i[0])
                # print("snp_info_lst")
                # print(snp_info_lst)
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
                                "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0] + ". "
                            else:
                                output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0] + ". "
                        elif len(ref_variants) == 0 and len(snp_info_lst) > 1:
                            var_id = "rs" + snp_info_lst[0]['id']
                            if "warning" in output:
                                output["warning"] = output["warning"] + \
                                "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0] + ". "
                            else:
                                output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp_raw_i[0] + ". "
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
    # print("Input SNPs (replace genomic coords with RSIDs)", str(snps))
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
                    if snp_coord != None and snp_coord[genome_build_vars[genome_build]['position']] != "NA":
                        # check if variant is on chrY for genome build = GRCh38
                        if snp_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
                            if "warning" in output:
                                output["warning"] = output["warning"] + \
                                    "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + "). "
                            else:
                                output["warning"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + snp_coord['id'] + " = chr" + snp_coord['chromosome'] + ":" + snp_coord[genome_build_vars[genome_build]['position']] + "). "
                            warn.append(snp_i[0])
                        else:
                            rs_nums.append(snp_i[0])
                            snp_pos.append(snp_coord[genome_build_vars[genome_build]['position']])
                            temp = [snp_i[0], snp_coord['chromosome'], snp_coord[genome_build_vars[genome_build]['position']]]
                            snp_coords.append(temp)
                    else:
                        warn.append(snp_i[0])
                else:
                    warn.append(snp_i[0])
            else:
                warn.append(snp_i[0])

    if warn != []:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn) + ". "
        else:
            output["warning"] = "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn) + ". "

    if len(rs_nums) == 0:
        output["error"] = "Input variant list does not contain any valid RS numbers or coordinates. " + str(output["warning"] if "warning" in output else "")
        return(json.dumps(output, sort_keys=True, indent=2))

    # Check SNPs are all on the same chromosome
    for i in range(len(snp_coords)):
        if snp_coords[0][1] != snp_coords[i][1]:
            output["error"] = "Not all input variants are on the same chromosome: "+snp_coords[i-1][0]+"=chr" + \
                str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0] + \
                "=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+". " + str(output["warning"] if "warning" in output else "")
            return(json.dumps(output, sort_keys=True, indent=2))

    # Check max distance between SNPs
    distance_bp = []
    for i in range(len(snp_coords)):
        distance_bp.append(int(snp_coords[i][2]))
    distance_max = max(distance_bp)-min(distance_bp)
    if distance_max > 1000000:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                "Switch rate errors become more common as distance between query variants increases (Query range = "+str(
                    distance_max)+" bp). "
        else:
            output["warning"] = "Switch rate errors become more common as distance between query variants increases (Query range = "+str(
                distance_max)+" bp). "

    # Sort coordinates and make tabix formatted coordinates
    snp_pos_int = [int(i) for i in snp_pos]
    snp_pos_int.sort()
    # keep track of rs and snp postion after sort
    rs_snp_pos = []
    for i in snp_pos_int:
        rs_snp_pos.append(snp_pos.index(str(i)))
    
    snp_coord_str = [genome_build_vars[genome_build]['1000G_chr_prefix'] + snp_coords[0][1] + ":" + str(i) + "-" + str(i) for i in snp_pos_int]
    tabix_coords = " " + " ".join(snp_coord_str)
    print("tabix_coords", tabix_coords)
    # # Extract 1000 Genomes phased genotypes
    vcf_filePath = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (snp_coords[0][1]))
    vcf_query_snp_file = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath)

    checkS3File(aws_info, config['aws']['bucket'], vcf_filePath)
    vcf = retrieveTabix1000GData(vcf_query_snp_file, tabix_coords, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])

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


    # Make sure there are genotype data in VCF file
    if vcf[-1][0:6] == "#CHROM":
        output["error"] = "No query variants were found in 1000G VCF file. " + str(output["warning"] if "warning" in output else "")
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


    unique_vcf = []
    dup_vcf = []

    for g in range(h+1, len(vcf)):
        geno = vcf[g].strip().split()
        geno[0] = geno[0].lstrip('chr')
        temp = geno[0]+geno[1]
        if temp not in unique_vcf:
            unique_vcf.append(temp)
        else:
            dup_vcf.append(temp)
            if snp_pos.count(geno[1]) == 1:
                rs_query = rs_nums[snp_pos.index(geno[1])]
                warningmsg = "Variant " + rs_query + " is not biallelic, variant removed. " 
                if "warning" in output and geno[1] not in output["warning"]:
                    output["warning"] = output["warning"]+warningmsg
                else:
                    output["warning"] = warningmsg
    
    counter_dups = 0
    for g in range(h+1, len(vcf)):
        geno = vcf[g - counter_dups].strip().split()
        geno[0] = geno[0].lstrip('chr')
        temp = geno[0]+geno[1]
        if temp in dup_vcf:
            counter_dups = counter_dups + 1
            vcf.pop(g - counter_dups)

    if len(vcf[h+1:]) == 0:
        output["error"] = "Input variant list does not contain any valid RS numbers or coordinates. " + str(output["warning"] if "warning" in output else "")
        return(json.dumps(output, sort_keys=True, indent=2))


    for g in range(h+1, len(vcf)): # 3 rows
        geno = vcf[g].strip().split()
        geno[0] = geno[0].lstrip('chr')
        
        if geno[1] not in snp_pos:
            # counter_dups/2 will be the numbers of dups before this geno[1] in snp_pos, 
            # g-h-1-counter_dups/2 will be the value as 0,1,2,... and will be the index to each snp_pos value  
            snp_pos_index = rs_snp_pos[g-h-1]
            if "warning" in output:
                output["warning"] = output["warning"] + "Genomic position ("+geno[1]+") in VCF file does not match dbSNP" + \
                    dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ") search coordinates for query variant. "
            else:
                output["warning"] = "Genomic position ("+geno[1]+") in VCF file does not match dbSNP" + \
                    dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ") search coordinates for query variant. "
            print("snp_pos[snp_pos_index]", snp_pos[snp_pos_index])
            print("snp_coords", snp_coords)
            # if 1000G position does not match dbSNP position for variant, use dbSNP position
            geno[1] = snp_pos[snp_pos_index]

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
                            "Genomic position for query variant ("+rs_query + \
                            ") does not match RS number at 1000G position (chr" + \
                            geno[0]+":"+geno[1]+" = "+rs_1000g+"). "
                    else:
                        output["warning"] = "Genomic position for query variant ("+rs_query + \
                            ") does not match RS number at 1000G position (chr" + \
                            geno[0]+":"+geno[1]+" = "+rs_1000g+"). "

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
    keys = list(haps.keys())
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
    print("RS_Number\tPosition (" + genome_build_vars[genome_build]['title_hg'] + ")\tAllele Frequency", file=snp_out)
    for k in sorted(output["snps"].keys()):
        rs_k = output["snps"][k]["RS"]
        coord_k = output["snps"][k]["Coord"]
        alleles_k0 = output["snps"][k]["Alleles"].strip(" ").split(",")
        alleles_k1 = alleles_k0[0]+"0"*(7-len(str(alleles_k0[0]))) + \
            ","+alleles_k0[1]+"0"*(8-len(str(alleles_k0[1])))
        temp_k = [rs_k, coord_k, alleles_k1]
        print("\t".join(temp_k), file=snp_out)
    snp_out.close()

    # Create Haplotype File
    hap_out = open(tmp_dir+"haplotypes_"+request+".txt", "w")
    print("Haplotype\tCount\tFrequency", file=hap_out)
    for k in sorted(output["haplotypes"].keys()):
        hap_k = output["haplotypes"][k]["Haplotype"]
        count_k = str(output["haplotypes"][k]["Count"])
        freq_k = str(output["haplotypes"][k]["Frequency"])
        temp_k = [hap_k, count_k, freq_k]
        print("\t".join(temp_k), file=hap_out)
    hap_out.close()

    # Return JSON output
    return(json.dumps(output, sort_keys=True, indent=2))

def main():
    # Import LDLink options
    if len(sys.argv) == 6:
        snplst = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        web = sys.argv[4]
        genome_build = sys.argv[5]
    else:
        print("Correct useage is: LDLink.py snplst populations request false")
        sys.exit()

    # Run function
    out_json = calculate_hap(snplst, pop, request, web, genome_build)

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

        print("")
        print("RS Number     Coordinates      Allele Frequency      Common Haplotypes (>1%)")
        print("")
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
            print("   ".join(temp_k))
            counter += 1

        print("")
        print("                                         Count: " + \
            " ".join(hap_count[0:freq_count]))
        print("                                     Frequency: " + \
            " ".join(hap_freq[0:freq_count]))

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
