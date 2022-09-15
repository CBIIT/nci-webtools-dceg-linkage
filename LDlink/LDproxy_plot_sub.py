import yaml
import csv
import json
import operator
import os
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
import boto3
import botocore
import time
import threading
import weakref
from multiprocessing.dummy import Pool
import math
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars,connectMongoDBReadOnly,ldproxy_figure
from LDcommon import get_coords,replace_coord_rsid,get_query_variant_c,LD_calcs,chunkWindow,get_output
from LDutilites import get_config

# LDproxy subprocess to export bokeh to high quality images in the background

def calculate_proxy_svg(snp, pop, request, genome_build, r2_d="r2", window=500000, collapseTranscript=True):
    # Set data directories using config.yml
    param_list = get_config()
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

    # Find coordinates (GRCh37/hg19) or (GRCh38/hg38) for SNP RS number
    
    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(True)

    snp = replace_coord_rsid(db, snp,genome_build,None)

    # Find RS number in snp database
    snp_coord = get_coords(db, snp)

    # Get population ids from LDproxy.py tmp output files
    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
    ids = []
    for i in range(len(pop_list)):
        ids.append(pop_list[i].strip())

    pop_ids = list(set(ids))

    temp = [snp, str(snp_coord['chromosome']), int(snp_coord[genome_build_vars[genome_build]['position']])]
    #print(temp)
    (geno,tmp_dist, warningmsg) = get_query_variant_c(temp, pop_ids, str(request), genome_build, True)
    #print(geno,warningmsg)
    for msg in warningmsg:
        if msg[1] != "NA":
            snp = geno[2]

    # Define window of interest around query SNP
    # window = 500000
    coord1 = int(snp_coord[genome_build_vars[genome_build]['position']]) - window
    if coord1 < 0:
        coord1 = 0
    coord2 = int(snp_coord[genome_build_vars[genome_build]['position']]) + window

    # Calculate proxy LD statistics in parallel
    # threads = 4
    # block = (2 * window) // 4
    # block = (2 * window) // num_subprocesses
    windowChunkRanges = chunkWindow(int(snp_coord[genome_build_vars[genome_build]['position']]), window, num_subprocesses)

    commands = []
    # for i in range(num_subprocesses):
    #     if i == min(range(num_subprocesses)) and i == max(range(num_subprocesses)):
    #         command = "python3 LDproxy_sub.py " + "True " + snp + " " + \
    #             snp_coord['chromosome'] + " " + str(coord1) + " " + \
    #             str(coord2) + " " + request + " " + str(i)
    #     elif i == min(range(num_subprocesses)):
    #         command = "python3 LDproxy_sub.py " + "True " + snp + " " + \
    #             snp_coord['chromosome'] + " " + str(coord1) + " " + \
    #             str(coord1 + block) + " " + request + " " + str(i)
    #     elif i == max(range(num_subprocesses)):
    #         command = "python3 LDproxy_sub.py " + "True " + snp + " " + snp_coord['chromosome'] + " " + str(
    #             coord1 + (block * i) + 1) + " " + str(coord2) + " " + request + " " + str(i)
    #     else:
    #         command = "python3 LDproxy_sub.py " + "True " + snp + " " + snp_coord['chromosome'] + " " + str(coord1 + (
    #             block * i) + 1) + " " + str(coord1 + (block * (i + 1))) + " " + request + " " + str(i)
    #     commands.append(command)

    for subprocess_id in range(num_subprocesses):
        getWindowVariantsArgs = " ".join(["True", str(snp), str(snp_coord['chromosome']), str(windowChunkRanges[subprocess_id][0]), str(windowChunkRanges[subprocess_id][1]), str(request), genome_build, str(subprocess_id)])
        commands.append("python3 LDproxy_sub.py " + getWindowVariantsArgs)

    processes = [subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE) for command in commands]

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
        r2_d = "r2"

    out_dist_sort = sorted(out_prox, key=operator.itemgetter(14))
    if r2_d == "r2":
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(8), reverse=True)
    else:
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(7), reverse=True)


    out_grid,proxy_plot,gene_plot,rug,plot_h_pix = ldproxy_figure(out_ld_sort, r2_d,coord1,coord2,snp,pop,request,db,snp_coord,genome_build,collapseTranscript)
    import svgutils.compose as sg
    from bokeh.io import export_svgs
    # Change output backend to SVG temporarily for headless export
    # Will be changed back to canvas in LDlink.js
    proxy_plot.output_backend = "svg"
    rug.output_backend = "svg"
    gene_plot.output_backend = "svg"
    export_svgs(proxy_plot, filename=tmp_dir +
                "proxy_plot_1_" + request + ".svg")
    export_svgs(gene_plot, filename=tmp_dir +
                "gene_plot_1_" + request + ".svg")

    # 1 pixel = 0.0264583333 cm
    svg_height = str(20.00 + (0.0264583333 * plot_h_pix)) + "cm"
    svg_height_scaled = str(100.00 + (0.1322916665 * plot_h_pix)) + "cm"

    # Concatenate svgs
    sg.Figure("24.59cm", svg_height,
              sg.SVG(tmp_dir + "proxy_plot_1_" + request + ".svg"),
              sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").move(0, 630)
              ).save(tmp_dir + "proxy_plot_" + request + ".svg")

    sg.Figure("122.95cm", svg_height_scaled,
              sg.SVG(tmp_dir + "proxy_plot_1_" + request + ".svg").scale(5),
              sg.SVG(tmp_dir + "gene_plot_1_" + request +
                     ".svg").scale(5).move(0, 3150)
              ).save(tmp_dir + "proxy_plot_scaled_" + request + ".svg")

    # Export to PDF
    subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "proxy_plot_" +
                    request + ".svg " + tmp_dir + "proxy_plot_" + request + ".pdf", shell=True)
    # Export to PNG
    subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "proxy_plot_scaled_" +
                    request + ".svg " + tmp_dir + "proxy_plot_" + request + ".png", shell=True)
    # Export to JPEG
    subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "proxy_plot_scaled_" +
                    request + ".svg " + tmp_dir + "proxy_plot_" + request + ".jpeg", shell=True)
    # Remove individual SVG files after they are combined
    subprocess.call("rm " + tmp_dir + "proxy_plot_1_" +
                    request + ".svg", shell=True)
    subprocess.call("rm " + tmp_dir + "gene_plot_1_" +
                    request + ".svg", shell=True)
    # Remove scaled SVG file after it is converted to png and jpeg
    subprocess.call("rm " + tmp_dir + "proxy_plot_scaled_" +
                    request + ".svg", shell=True)

    #reset_output()

    # Remove temporary files
    subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
    subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
    subprocess.call("rm " + tmp_dir + "genes_*" + request + "*.json", shell=True)
    subprocess.call("rm " + tmp_dir + "recomb_" + request + ".txt", shell=True)

    # Return plot output
    return None

def main():

    # Import LDproxy options
    if len(sys.argv) == 8:
        snp = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        genome_build = sys.argv[4]
        r2_d = sys.argv[5]
        window = sys.argv[6]
        collapseTranscript = sys.argv[7]
    else:
        sys.exit()

    # Run function
    calculate_proxy_svg(snp, pop, request, genome_build, r2_d, int(window), collapseTranscript)


if __name__ == "__main__":
    main()
