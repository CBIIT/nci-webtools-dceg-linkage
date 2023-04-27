#!/usr/bin/env python3
import json
import operator
import os
import subprocess
import sys
import time
import threading
import weakref
import time
from multiprocessing.dummy import Pool
from LDcommon import retrieveAWSCredentials, genome_build_vars, connectMongoDBReadOnly
from LDcommon import validsnp,get_coords,replace_coord_rsid,get_population,get_query_variant_c,chunkWindow,get_output,ldproxy_figure
from LDutilites import get_config

# Create LDproxy function
def calculate_proxy(snp, pop, request, web, genome_build, r2_d="r2", window=500000, collapseTranscript=True, annotate="forge"):

    # trim any whitespace
    snp = snp.lower().strip()

    start_time = time.time()
    
    # Set data directories using config.yml
    param_list = get_config()
    dbsnp_version = param_list['dbsnp_version']
    population_samples_dir = param_list['population_samples_dir']
    data_dir = param_list['data_dir']
    tmp_dir = param_list['tmp_dir']
    genotypes_dir = param_list['genotypes_dir']
    aws_info = param_list['aws_info']
    num_subprocesses = param_list['num_subprocesses']

    export_s3_keys = retrieveAWSCredentials()

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    if request is False:
        request = str(time.strftime("%I%M%S"))

    # Create JSON output
    out_json = open(tmp_dir + 'proxy' + request + ".json", "w")
    output = {}

    validsnp(None,genome_build,None)

    if window < 0 or window > 1000000:
        output["error"] = "Window value must be a number between 0 and 1,000,000."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(web)
    snp = replace_coord_rsid(db,snp,genome_build,output)

    # Find RS number in snp database
    snp_coord = get_coords(db,snp)

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
    pop_ids = get_population(pop,request,output)
    if isinstance(pop_ids,str):
        print(pop_ids, file=out_json)
        out_json.close()
        return("","")

    temp = [snp, str(snp_coord['chromosome']), int(snp_coord[genome_build_vars[genome_build]['position']])]
    #print(temp)
    (geno,tmp_dist, warningmsg) = get_query_variant_c(temp, pop_ids, str(request), genome_build, True,output)
    #print(warningmsg)
    for msg in warningmsg:
        if msg[1] == "NA":
            if "biallelic" in msg[2] or "monoallelic" in msg[2]:
                output["error"] = str(output["error"] if "error" in output else "") + msg[2]
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
            subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
            return("", "")
        else:
            output["warning"] = str(output["warning"] if "warning" in output else "") + msg[2]
            snp = geno[2]
  
    # Define window of interest around query SNP
    # window = 500000
    coord1 = int(snp_coord[genome_build_vars[genome_build]['position']]) - window
    if coord1 < 0:
        coord1 = 0
    coord2 = int(snp_coord[genome_build_vars[genome_build]['position']]) + window
    #print("#########",coord1,coord2)
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
    # for subp in processes:
    #    for line in subp.stdout:
    #        print(line.decode().strip())
 
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
    #print(len(out_prox),(out_prox[0]))
    # Sort output
    if r2_d not in ["r2", "d"]:
        if "warning" in output:
            output["warning"] = output["warning"] + ". " + r2_d + \
                " is not an acceptable value for r2_d (r2 or d required). r2 is used by default"
        else:
            output["warning"] = r2_d + \
                " is not an acceptable value for r2_d (r2 or d required). r2 is used by default"
        r2_d = "r2"

    out_dist_sort = sorted(out_prox, key=operator.itemgetter(15))

    if r2_d == "r2":
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(8), reverse=True)
    else:
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(7), reverse=True)

    # Populate JSON and text output
    outfile = open(tmp_dir + "proxy" + request + ".txt", "w")
    header = ["RS_Number", "Coord", "Alleles", "MAF", "Distance",
              "Dprime", "R2", "Correlated_Alleles", "FORGEdb","RegulomeDB",  "Function"]
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
    query_snp["ForgeDB"] = out_ld_sort[0][10]
    query_snp["RegulomeDB"] = out_ld_sort[0][11]
    query_snp["MAF"] = str(round(float(out_ld_sort[0][13]), 4))
    query_snp["Function"] = out_ld_sort[0][14]

    output["query_snp"] = query_snp

    temp = [query_snp["RS"], query_snp["Coord"], query_snp["Alleles"], query_snp["MAF"], str(query_snp["Dist"]), str(
            query_snp["Dprime"]), str(query_snp["R2"]), query_snp["Corr_Alleles"], query_snp["ForgeDB"] if len(query_snp["ForgeDB"]) >0 else "NA",query_snp["RegulomeDB"], query_snp["Function"]]
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
            proxy_info["ForgeDB"] = out_ld_sort[i][10]
            proxy_info["RegulomeDB"] = out_ld_sort[i][11]
            proxy_info["MAF"] = str(round(float(out_ld_sort[i][13]), 4))
            proxy_info["Function"] = out_ld_sort[i][14]
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
            row.append(proxy_info["ForgeDB"])
            row.append(proxy_info["RegulomeDB"])
            row.append("HaploReg link")
            row.append(proxy_info["Function"])
            rows.append(row)
            
            temp = [proxy_info["RS"], proxy_info["Coord"], proxy_info["Alleles"], proxy_info["MAF"], str(proxy_info["Dist"]), str(
                    proxy_info["Dprime"]), str(proxy_info["R2"]), proxy_info["Corr_Alleles"], proxy_info["ForgeDB"] if len(proxy_info["ForgeDB"]) >0 else "NA",proxy_info["RegulomeDB"], proxy_info["Function"]]
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
        
        #out_grid = ldproxy_figue(out_ld_sort, r2_d,coord1,coord2,snp,pop,request,db,snp_coord,genome_build,collapseTranscript)
        out_grid,proxy_plot,gene_plot,rug,plot_h_pix = ldproxy_figure(out_ld_sort, r2_d,coord1,coord2,snp,pop,request,db,snp_coord,genome_build,collapseTranscript,annotate)

        # Generate high quality images only if accessed via web instance
        
        # Open thread for high quality image exports
        command = "python3 LDproxy_plot_sub.py " + snp + " " + pop + " " + request + " " + genome_build + " " + r2_d + " " + str(window) + " " + collapseTranscript+" "+annotate
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        ###########################
        # Html output for testing #
        ###########################
        #html=file_html(out_grid, CDN, "Test Plot")
        # out_html=open("LDproxy.html","w")
        #print >> out_html, html
        # out_html.close()
       
        from bokeh.embed import components
      
        from bokeh.resources import CDN
 
        out_script, out_div = components(out_grid, CDN)
        #reset_output()

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
