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
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars,connectMongoDBReadOnly
from LDcommon import get_coords,replace_coord_rsid

# LDproxy subprocess to export bokeh to high quality images in the background

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

def calculate_proxy_svg(snp, pop, request, genome_build, r2_d="r2", window=500000, collapseTranscript=True):

    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    data_dir = config['data']['data_dir']
    tmp_dir = config['data']['tmp_dir']
    genotypes_dir = config['data']['genotypes_dir']
    aws_info = config['aws']
    num_subprocesses = config['performance']['num_subprocesses']

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

    snp = replace_coord_rsid(db, snp,genome_build,output)

    # Find RS number in snp database
    snp_coord = get_coords(db, snp)

    # Get population ids from LDproxy.py tmp output files
    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
    ids = []
    for i in range(len(pop_list)):
        ids.append(pop_list[i].strip())

    pop_ids = list(set(ids))

    # Extract query SNP phased genotypes
    vcf_filePath = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (snp_coord['chromosome']))
    vcf_query_snp_file = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath)

    checkS3File(aws_info, config['aws']['bucket'], vcf_filePath)

    tabix_snp_h = export_s3_keys + " cd {1}; tabix -HD {0} | grep CHROM".format(vcf_query_snp_file, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
    head = [x.decode('utf-8') for x in subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE).stdout.readlines()][0].strip().split()

    tabix_snp =  export_s3_keys + " cd {4}; tabix -D {0} {1}:{2}-{2} | grep -v -e END > {3}".format(
        vcf_query_snp_file, genome_build_vars[genome_build]['1000G_chr_prefix'] + snp_coord['chromosome'], snp_coord[genome_build_vars[genome_build]['position']], tmp_dir + "snp_no_dups_" + request + ".vcf", data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
    subprocess.call(tabix_snp, shell=True)

    # Check SNP is in the 1000G population, has the correct RS number, and not
    # monoallelic
    vcf = open(tmp_dir + "snp_no_dups_" + request + ".vcf").readlines()

    if len(vcf) == 0:
        subprocess.call("rm " + tmp_dir + "pops_" +
                        request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return None
    elif len(vcf) > 1:
        geno = []
        for i in range(len(vcf)):
            if vcf[i].strip().split()[2] == snp:
                geno = vcf[i].strip().split()
                geno[0] = geno[0].lstrip('chr')
        if geno == []:
            subprocess.call("rm " + tmp_dir + "pops_" +
                            request + ".txt", shell=True)
            subprocess.call("rm " + tmp_dir + "*" +
                            request + "*.vcf", shell=True)
            return None
    else:
        geno = vcf[0].strip().split()
        geno[0] = geno[0].lstrip('chr')

    if geno[2] != snp and snp[0:2]=="rs" and "rs" in geno[2]:
            snp = geno[2]

    if "," in geno[3] or "," in geno[4]:
        subprocess.call("rm " + tmp_dir + "pops_" +
                        request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return None

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
        subprocess.call("rm " + tmp_dir + "pops_" +
                        request + ".txt", shell=True)
        subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return None

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
        r2_d = "r2"

    out_dist_sort = sorted(out_prox, key=operator.itemgetter(14))
    if r2_d == "r2":
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(8), reverse=True)
    else:
        out_ld_sort = sorted(
            out_dist_sort, key=operator.itemgetter(7), reverse=True)

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
    from bokeh.io import export_svgs
    import svgutils.compose as sg

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

    # Add recombination rate from LDproxy.py output file
    recomb_file = tmp_dir + "recomb_" + request + ".json"
    recomb_raw = open(recomb_file).readlines()

    recomb_x = []
    recomb_y = []

    for recomb_raw_obj in recomb_raw:
        recomb_obj = json.loads(recomb_raw_obj)
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
        genes_raw = open(genes_file).readlines()

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
        if genes_raw != None and len(genes_raw) > 0:
            for gene_raw_obj in genes_raw:
                gene_obj = json.loads(gene_raw_obj)
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

    # Gene Plot (Collapsed)
    else:
        genes_c_file = tmp_dir + "genes_c_" + request + ".json"
        genes_c_raw = open(genes_c_file).readlines()

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
        if genes_c_raw != None and len(genes_c_raw) > 0:
            for gene_c_raw_obj in genes_c_raw:
                gene_c_obj = json.loads(gene_c_raw_obj)
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
            plot_h_pix = 250
        else:
            plot_h_pix = 250 + (len(lines_c) - 2) * 50

        gene_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
                        x_range=xr, y_range=yr2_c, border_fill_color='white',
                        title="", h_symmetry=False, v_symmetry=False, logo=None,
                        plot_width=900, plot_height=plot_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,previewsave")

        # if len(genes_c_raw) <= max_genes_c:
        gene_plot.segment(genes_c_plot_start, genes_c_plot_yn, genes_c_plot_end,
                            genes_c_plot_yn, color="black", alpha=1, line_width=2)
        gene_plot.rect(x='exons_c_plot_x', y='exons_c_plot_yn', width='exons_c_plot_w', height='exons_c_plot_h',
                        source=source_gene_c_plot, fill_color="grey", line_color="grey")
        gene_plot.text(genes_c_plot_start, genes_c_plot_yn, text=genes_c_plot_name, alpha=1, text_font_size="7pt",
                        text_font_style="bold", text_baseline="middle", text_align="right", angle=0)
        hover = gene_plot.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ("Gene", "@exons_c_plot_name"),
            ("Transcript IDs", "@exons_c_plot_id"),
        ])

        # else:
        # 	x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
        # 	gene_c_plot.text(x_coord_text, n_rows_c / 2.0, text=message_c, alpha=1,
        # 				   text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

        gene_plot.xaxis.axis_label = "Chromosome " + snp_coord['chromosome'] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
        gene_plot.ygrid.grid_line_color = None
        gene_plot.yaxis.axis_line_color = None
        gene_plot.yaxis.minor_tick_line_color = None
        gene_plot.yaxis.major_tick_line_color = None
        gene_plot.yaxis.major_label_text_color = None

        gene_plot.toolbar_location = "below"

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

    reset_output()

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
