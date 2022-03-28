import yaml
import json
import sys
import json
import math
import operator
import os
import boto3
import botocore
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars,connectMongoDBReadOnly
from LDcommon import get_coords,replace_coord_rsid,validsnp

# LDmatrix subprocess to export bokeh to high quality images in the background
def calculate_matrix_svg(snplst, pop, request, genome_build, r2_d="r2", collapseTranscript=True):

    # Set data directories using config.yml
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    population_samples_dir = config['data']['population_samples_dir']
    data_dir = config['data']['data_dir']
    tmp_dir = config['data']['tmp_dir']
    genotypes_dir = config['data']['genotypes_dir']
    aws_info = config['aws']
 
    export_s3_keys = retrieveAWSCredentials()

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    snps = validsnp(snplst,genome_build,None)
    #if return value is string, then it is error message and need to return the message
    if isinstance(snps, str):
        return snps
    
    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(data_dir + population_samples_dir + pop_i + ".txt")

    get_pops = "cat " + " ".join(pop_dirs)
    pop_list = [x.decode('utf-8') for x in subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(True)
  
    snps = replace_coords_rsid(db, snps,None)

    # Find RS numbers in snp database
    rs_nums = []
    snp_pos = []
    snp_coords = []
    tabix_coords = ""
    for snp_i in snps:
        if len(snp_i) > 0:
            if len(snp_i[0]) > 2:
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
                    snp_coord = get_coords(db, snp_i[0])
                    if snp_coord != None and snp_coord[genome_build_vars[genome_build]['position']] != "NA":
                        # check if variant is on chrY for genome build = GRCh38
                        if not (snp_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage")):
                            rs_nums.append(snp_i[0])
                            snp_pos.append(snp_coord[genome_build_vars[genome_build]['position']])
                            temp = [snp_i[0], snp_coord['chromosome'], snp_coord[genome_build_vars[genome_build]['position']]]
                            snp_coords.append(temp)

    # Check max distance between SNPs
    distance_bp = []
    for i in range(len(snp_coords)):
        distance_bp.append(int(snp_coords[i][2]))

    # Sort coordinates and make tabix formatted coordinates
    snp_pos_int = [int(i) for i in snp_pos]
    snp_pos_int.sort()
    snp_coord_str = [genome_build_vars[genome_build]['1000G_chr_prefix'] + snp_coords[0][1] + ":" + str(i) + "-" + str(i) for i in snp_pos_int]
    tabix_coords = " " + " ".join(snp_coord_str)

    # Extract 1000 Genomes phased genotypes
    vcf_filePath = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (snp_coords[0][1]))
    vcf_query_snp_file = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath)

    checkS3File(aws_info, config['aws']['bucket'], vcf_filePath)

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
    tabix_snps = export_s3_keys + " cd {2}; tabix -fhD {0}{1} | grep -v -e END".format(vcf_query_snp_file, tabix_coords, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
    vcf = [x.decode('utf-8') for x in subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE).stdout.readlines()]

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
    for i in range(len(index) - 1):
        hap1.append([])
    hap2 = [[]]
    for i in range(len(index) - 1):
        hap2.append([])

    rsnum_lst = []
    allele_lst = []
    pos_lst = []

    for g in range(h + 1, len(vcf)):
        geno = vcf[g].strip().split()
        geno[0] = geno[0].lstrip('chr')
        if geno[1] not in snp_pos:
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
            while count <= 2 and count + g < len(vcf):
                geno_next = vcf[g + count].strip().split()
                geno_next[0] = geno_next[0].lstrip('chr')
                if len(geno_next) >= 3 and rs_query == geno_next[2]:
                    found = "true"
                    break
                count += 1

            if found == "false":
                indx = [i[0] for i in snps].index(rs_query)
                # snps[indx][0] = geno[2]
                # rsnum = geno[2]
                snps[indx][0] = rs_query
                rsnum = rs_query
            else:
                continue

        if "," not in geno[3] and "," not in geno[4]:
            a1, a2 = set_alleles(geno[3], geno[4])
            for i in range(len(index)):
                if geno[index[i]] == "0|0":
                    hap1[i].append(a1)
                    hap2[i].append(a1)
                elif geno[index[i]] == "0|1":
                    hap1[i].append(a1)
                    hap2[i].append(a2)
                elif geno[index[i]] == "1|0":
                    hap1[i].append(a2)
                    hap2[i].append(a1)
                elif geno[index[i]] == "1|1":
                    hap1[i].append(a2)
                    hap2[i].append(a2)
                elif geno[index[i]] == "0":
                    hap1[i].append(a1)
                    hap2[i].append(".")
                elif geno[index[i]] == "1":
                    hap1[i].append(a2)
                    hap2[i].append(".")
                else:
                    hap1[i].append(".")
                    hap2[i].append(".")

            rsnum_lst.append(rsnum)

            position = "chr" + geno[0] + ":" + geno[1] + "-" + geno[1]
            pos_lst.append(position)
            alleles = a1 + "/" + a2
            allele_lst.append(alleles)

    # Calculate Pairwise LD Statistics
    all_haps = hap1 + hap2
    ld_matrix = [[[None for v in range(2)] for i in range(
        len(all_haps[0]))] for j in range(len(all_haps[0]))]

    for i in range(len(all_haps[0])):
        for j in range(i, len(all_haps[0])):
            hap = {}
            for k in range(len(all_haps)):
                # Extract haplotypes
                hap_k = all_haps[k][i] + all_haps[k][j]
                if hap_k in hap:
                    hap[hap_k] += 1
                else:
                    hap[hap_k] = 1

            # Remove Missing Haplotypes
            keys = list(hap.keys())
            for key in keys:
                if "." in key:
                    hap.pop(key, None)

            # Check all haplotypes are present
            if len(hap) != 4:
                snp_i_a = allele_lst[i].split("/")
                snp_j_a = allele_lst[j].split("/")
                haps = [snp_i_a[0] + snp_j_a[0], snp_i_a[0] + snp_j_a[1],
                        snp_i_a[1] + snp_j_a[0], snp_i_a[1] + snp_j_a[1]]
                for h in haps:
                    if h not in hap:
                        hap[h] = 0

            # Perform LD calculations
            A = hap[sorted(hap)[0]]
            B = hap[sorted(hap)[1]]
            C = hap[sorted(hap)[2]]
            D = hap[sorted(hap)[3]]
            tmax = max(A, B, C, D)
            delta = float(A * D - B * C)
            Ms = float((A + C) * (B + D) * (A + B) * (C + D))
            if Ms != 0:
                # D prime
                if delta < 0:
                    D_prime = round(
                        abs(delta / min((A + C) * (A + B), (B + D) * (C + D))), 3)
                else:
                    D_prime = round(
                        abs(delta / min((A + C) * (C + D), (A + B) * (B + D))), 3)

                # R2
                r2 = round((delta**2) / Ms, 3)

                # Find Correlated Alleles
                if str(r2) != "NA" and float(r2) > 0.1:
                    Ac=hap[sorted(hap)[0]]
                    Bc=hap[sorted(hap)[1]]
                    Cc=hap[sorted(hap)[2]]
                    Dc=hap[sorted(hap)[3]]

                    if ((Ac*Dc) / max((Bc*Cc), 0.01) > 1):
                        match = sorted(hap)[0][0] + "=" + sorted(hap)[0][1] + "," + sorted(hap)[3][0] + "=" + sorted(hap)[3][1]
                    else:
                        match = sorted(hap)[1][0] + "=" + sorted(hap)[1][1] + "," + sorted(hap)[2][0] + "=" + sorted(hap)[2][1]
                else:
                    match = "  =  ,  =  "
            else:
                D_prime = "NA"
                r2 = "NA"
                match = "  =  ,  =  "

            snp1 = rsnum_lst[i]
            snp2 = rsnum_lst[j]
            pos1 = pos_lst[i].split("-")[0]
            pos2 = pos_lst[j].split("-")[0]
            allele1 = allele_lst[i]
            allele2 = allele_lst[j]
            corr = match.split(",")[0].split("=")[1] + "=" + match.split(",")[0].split("=")[
                0] + "," + match.split(",")[1].split("=")[1] + "=" + match.split(",")[1].split("=")[0]
            corr_f = match

            ld_matrix[i][j] = [snp1, snp2, allele1,
                            allele2, corr, pos1, pos2, D_prime, r2]
            ld_matrix[j][i] = [snp2, snp1, allele2,
                            allele1, corr_f, pos2, pos1, D_prime, r2]

    # Generate Plot Variables
    out = [j for i in ld_matrix for j in i]
    xnames = []
    ynames = []
    xA = []
    yA = []
    corA = []
    xpos = []
    ypos = []
    D = []
    R = []
    box_color = []
    box_trans = []

    if r2_d not in ["r2", "d"]:
        r2_d = "r2"

    for i in range(len(out)):
        snp1, snp2, allele1, allele2, corr, pos1, pos2, D_prime, r2 = out[i]
        xnames.append(snp1)
        ynames.append(snp2)
        xA.append(allele1)
        yA.append(allele2)
        corA.append(corr)
        xpos.append(pos1)
        ypos.append(pos2)
        sqrti = math.floor(math.sqrt(len(out)))
        if sqrti == 0:
            D.append(str(round(float(D_prime), 4)))
            R.append(str(round(float(r2), 4)))
            box_color.append("red")
            box_trans.append(r2)
        elif i%sqrti < i//sqrti and r2 != "NA":
            D.append(str(round(float(D_prime), 4)))
            R.append(str(round(float(r2), 4)))
            box_color.append("blue")
            box_trans.append(abs(D_prime))
        elif i%sqrti > i//sqrti and D_prime != "NA":
            D.append(str(round(float(D_prime), 4)))
            R.append(str(round(float(r2), 4)))
            box_color.append("red")
            box_trans.append(r2)
        elif i%sqrti == i//sqrti and D_prime != "NA":
            D.append(str(round(float(D_prime), 4)))
            R.append(str(round(float(r2), 4)))
            box_color.append("purple")
            box_trans.append(r2)
        else:
            D.append("NA")
            R.append("NA")
            box_color.append("gray")
            box_trans.append(0.1)
    # Import plotting modules
    from collections import OrderedDict
    from bokeh.embed import components, file_html
    from bokeh.layouts import gridplot
    from bokeh.models import HoverTool, LinearAxis, Range1d
    from bokeh.plotting import ColumnDataSource, curdoc, figure, output_file, reset_output, save
    from bokeh.resources import CDN
    from bokeh.io import export_svgs
    import svgutils.compose as sg
    from math import pi

    reset_output()

    # Aggregate Plotting Data
    x = []
    y = []
    w = []
    h = []
    coord_snps_plot = []
    snp_id_plot = []
    alleles_snp_plot = []
    for i in range(0, len(xpos), int(len(xpos)**0.5)):
        x.append(int(xpos[i].split(":")[1]) / 1000000.0)
        y.append(0.5)
        w.append(0.00003)
        h.append(1.06)
        coord_snps_plot.append(xpos[i])
        snp_id_plot.append(xnames[i])
        alleles_snp_plot.append(xA[i])

    buffer = (x[-1] - x[0]) * 0.025
    xr = Range1d(start=x[0] - buffer, end=x[-1] + buffer)
    yr = Range1d(start=-0.03, end=1.03)
    y2_ll = [-0.03] * len(x)
    y2_ul = [1.03] * len(x)

    yr_pos = Range1d(start=(x[-1] + buffer) * -1, end=(x[0] - buffer) * -1)
    yr0 = Range1d(start=0, end=1)
    yr2 = Range1d(start=0, end=3.8)
    yr3 = Range1d(start=0, end=1)

    spacing = (x[-1] - x[0] + buffer + buffer) / (len(x) * 1.0)
    x2 = []
    y0 = []
    y1 = []
    y2 = []
    y3 = []
    y4 = []
    for i in range(len(x)):
        x2.append(x[0] - buffer + spacing * (i + 0.5))
        y0.append(0)
        y1.append(0.20)
        y2.append(0.80)
        y3.append(1)
        y4.append(1.15)

    xname_pos = []
    for i in x2:
        for j in range(len(x2)):
            xname_pos.append(i)

    data = {
        'xname': xnames,
        'xname_pos': xname_pos,
        'yname': ynames,
        'xA': xA,
        'yA': yA,
        'xpos': xpos,
        'ypos': ypos,
        'R2': R,
        'Dp': D,
        'corA': corA,
        'box_color': box_color,
        'box_trans': box_trans
    }

    source = ColumnDataSource(data)

    threshold = 70
    if len(snps) < threshold:
        matrix_plot = figure(outline_line_color="white", min_border_top=0, min_border_bottom=2, min_border_left=100, min_border_right=5,
                            x_range=xr, y_range=list(reversed(rsnum_lst)),
                            h_symmetry=False, v_symmetry=False, border_fill_color='white', x_axis_type=None, logo=None,
                            tools="hover,undo,redo,reset,pan,box_zoom,previewsave", title=" ", plot_width=800, plot_height=700)

    else:
        matrix_plot = figure(outline_line_color="white", min_border_top=0, min_border_bottom=2, min_border_left=100, min_border_right=5,
                            x_range=xr, y_range=list(reversed(rsnum_lst)),
                            h_symmetry=False, v_symmetry=False, border_fill_color='white', x_axis_type=None, y_axis_type=None, logo=None,
                            tools="hover,undo,redo,reset,pan,box_zoom,previewsave", title=" ", plot_width=800, plot_height=700)

    matrix_plot.rect(x='xname_pos', y='yname', width=0.95 * spacing, height=0.95, source=source,
                    color="box_color", alpha="box_trans", line_color=None)

    matrix_plot.grid.grid_line_color = None
    matrix_plot.axis.axis_line_color = None
    matrix_plot.axis.major_tick_line_color = None
    if len(snps) < threshold:
        matrix_plot.axis.major_label_text_font_size = "8pt"
        matrix_plot.xaxis.major_label_orientation = "vertical"

    matrix_plot.axis.major_label_text_font_style = "normal"
    matrix_plot.xaxis.major_label_standoff = 0

    sup_2 = "\u00B2"

    hover = matrix_plot.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ("Variant 1", " " + "@yname (@yA)"),
        ("Variant 2", " " + "@xname (@xA)"),
        ("D\'", " " + "@Dp"),
        ("R" + sup_2, " " + "@R2"),
        ("Correlated Alleles", " " + "@corA"),
    ])

    # Connecting and Rug Plots
    # Connector Plot
    if len(snps) < threshold:
        connector = figure(outline_line_color="white", y_axis_type=None, x_axis_type=None,
                        x_range=xr, y_range=yr2, border_fill_color='white',
                        title="", min_border_left=100, min_border_right=5, min_border_top=0, min_border_bottom=0, h_symmetry=False, v_symmetry=False,
                        plot_width=800, plot_height=90, tools="xpan,tap")
        connector.segment(x, y0, x, y1, color="black")
        connector.segment(x, y1, x2, y2, color="black")
        connector.segment(x2, y2, x2, y3, color="black")
        connector.text(x2, y4, text=snp_id_plot, alpha=1, angle=pi / 2,
                    text_font_size="8pt", text_baseline="middle", text_align="left")
    else:
        connector = figure(outline_line_color="white", y_axis_type=None, x_axis_type=None,
                        x_range=xr, y_range=yr3, border_fill_color='white',
                        title="", min_border_left=100, min_border_right=5, min_border_top=0, min_border_bottom=0, h_symmetry=False, v_symmetry=False,
                        plot_width=800, plot_height=30, tools="xpan,tap")
        connector.segment(x, y0, x, y1, color="black")
        connector.segment(x, y1, x2, y2, color="black")
        connector.segment(x2, y2, x2, y3, color="black")

    connector.yaxis.major_label_text_color = None
    connector.yaxis.minor_tick_line_alpha = 0  # Option does not work
    connector.yaxis.axis_label = " "
    connector.grid.grid_line_color = None
    connector.axis.axis_line_color = None
    connector.axis.major_tick_line_color = None
    connector.axis.minor_tick_line_color = None

    connector.toolbar_location = None

    data_rug = {
        'x': x,
        'y': y,
        'w': w,
        'h': h,
        'coord_snps_plot': coord_snps_plot,
        'snp_id_plot': snp_id_plot,
        'alleles_snp_plot': alleles_snp_plot
    }

    source_rug = ColumnDataSource(data_rug)

    # Rug Plot
    rug = figure(x_range=xr, y_range=yr, y_axis_type=None,
                title="", min_border_top=1, min_border_bottom=0, min_border_left=100, min_border_right=5, h_symmetry=False, v_symmetry=False,
                plot_width=800, plot_height=50, tools="hover,xpan,tap")
    rug.rect(x='x', y='y', width='w', height='h', fill_color='red',
            dilate=True, line_color=None, fill_alpha=0.6, source=source_rug)

    hover = rug.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ("SNP", "@snp_id_plot (@alleles_snp_plot)"),
        ("Coord", "@coord_snps_plot"),
    ])

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
        message = ["Too many genes to plot."]
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
        genes_plot_yn = [n_rows - w + 0.5 for w in genes_plot_y]
        exons_plot_yn = [n_rows - w + 0.5 for w in exons_plot_y]
        yr2 = Range1d(start=0, end=n_rows)

        data_gene_plot = {
            'exons_plot_x': exons_plot_x,
            'exons_plot_yn': exons_plot_yn,
            'exons_plot_w': exons_plot_w,
            'exons_plot_h': exons_plot_h,
            'exons_plot_name': exons_plot_name,
            'exons_plot_id': exons_plot_id,
            'exons_plot_exon': exons_plot_exon,
            'coord_snps_plot': coord_snps_plot,
            'snp_id_plot': snp_id_plot,
            'alleles_snp_plot': alleles_snp_plot
        }

        source_gene_plot = ColumnDataSource(data_gene_plot)

        max_genes = 40
        # if len(lines) < 3 or len(genes_raw) > max_genes:
        if len(lines) < 3:
            plot_h_pix = 250
        else:
            plot_h_pix = 250 + (len(lines) - 2) * 50

        gene_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
                        x_range=xr, y_range=yr2, border_fill_color='white',
                        title="", h_symmetry=False, v_symmetry=False, logo=None,
                        plot_width=800, plot_height=plot_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,previewsave")

        # if len(genes_raw) <= max_genes:
        gene_plot.segment(genes_plot_start, genes_plot_yn, genes_plot_end,
                            genes_plot_yn, color="black", alpha=1, line_width=2)
        gene_plot.rect(x='exons_plot_x', y='exons_plot_yn', width='exons_plot_w', height='exons_plot_h',
                        source=source_gene_plot, fill_color='grey', line_color="grey")
        gene_plot.text(genes_plot_start, genes_plot_yn, text=genes_plot_name, alpha=1, text_font_size="7pt",
                        text_font_style="bold", text_baseline="middle", text_align="right", angle=0)
        hover = gene_plot.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ("Gene", "@exons_plot_name"),
            ("ID", "@exons_plot_id"),
            ("Exon", "@exons_plot_exon"),
        ])

        # else:
        #     x_coord_text = x[0] + (x[-1] - x[0]) / 2.0
        #     gene_plot.text(x_coord_text, n_rows / 2.0, text=message, alpha=1,
        #                    text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

        gene_plot.xaxis.axis_label = "Chromosome " + \
            snp_coords[1][1] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_plot.yaxis.axis_label = "Genes (All Transcripts)"
        gene_plot.ygrid.grid_line_color = None
        gene_plot.yaxis.axis_line_color = None
        gene_plot.yaxis.minor_tick_line_color = None
        gene_plot.yaxis.major_tick_line_color = None
        gene_plot.yaxis.major_label_text_color = None

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

        gene_plot.xaxis.axis_label = "Chromosome " + snp_coords[1][1] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
        gene_plot.ygrid.grid_line_color = None
        gene_plot.yaxis.axis_line_color = None
        gene_plot.yaxis.minor_tick_line_color = None
        gene_plot.yaxis.major_tick_line_color = None
        gene_plot.yaxis.major_label_text_color = None

        gene_plot.toolbar_location = "below"

    # Change output backend to SVG temporarily for headless export
    # Will be changed back to canvas in LDlink.js
    matrix_plot.output_backend = "svg"
    connector.output_backend = "svg"
    rug.output_backend = "svg"
    gene_plot.output_backend = "svg"
    export_svgs(matrix_plot, filename=tmp_dir +
                "matrix_plot_1_" + request + ".svg")
    export_svgs(connector, filename=tmp_dir +
                "connector_1_" + request + ".svg")
    export_svgs(rug, filename=tmp_dir +
                "rug_1_" + request + ".svg")
    export_svgs(gene_plot, filename=tmp_dir +
                "gene_plot_1_" + request + ".svg")

    # 1 pixel = 0.0264583333 cm
    svg_height = str(25.00 + (0.0264583333 * plot_h_pix)) + "cm"
    svg_height_scaled = str(110.00 + (0.1322916665 * plot_h_pix)) + "cm"

    # Concatenate svgs
    sg.Figure("21.59cm", svg_height,
            sg.SVG(tmp_dir + "matrix_plot_1_" + request + ".svg"),
            sg.SVG(tmp_dir + "connector_1_" + request + ".svg").scale(.97).move(0, 700),
            sg.SVG(tmp_dir + "rug_1_" + request + ".svg").scale(.97).move(0, 790),
            sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").scale(.97).move(0, 840)
            ).save(tmp_dir + "matrix_plot_" + request + ".svg")

    sg.Figure("107.95cm", svg_height_scaled,
            sg.SVG(tmp_dir + "matrix_plot_1_" + request + ".svg").scale(5),
            sg.SVG(tmp_dir + "connector_1_" + request + ".svg").scale(4.85).move(0, 3500),
            sg.SVG(tmp_dir + "rug_1_" + request + ".svg").scale(4.85).move(0, 3930),
            sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").scale(4.85).move(0, 4160)
            ).save(tmp_dir + "matrix_plot_scaled_" + request + ".svg")

    # Export to PDF
    subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "matrix_plot_" +
                    request + ".svg " + tmp_dir + "matrix_plot_" + request + ".pdf", shell=True)
    # Export to PNG
    subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "matrix_plot_scaled_" +
                    request + ".svg " + tmp_dir + "matrix_plot_" + request + ".png", shell=True)
    # Export to JPEG
    subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "matrix_plot_scaled_" +
                    request + ".svg " + tmp_dir + "matrix_plot_" + request + ".jpeg", shell=True)
    # Remove individual SVG files after they are combined
    subprocess.call("rm " + tmp_dir + "matrix_plot_1_" +
                    request + ".svg", shell=True)
    subprocess.call("rm " + tmp_dir + "gene_plot_1_" +
                    request + ".svg", shell=True)
    subprocess.call("rm " + tmp_dir + "rug_1_" +
                    request + ".svg", shell=True)
    subprocess.call("rm " + tmp_dir + "connector_1_" +
                    request + ".svg", shell=True)
    # Remove scaled SVG file after it is converted to png and jpeg
    subprocess.call("rm " + tmp_dir + "matrix_plot_scaled_" +
                    request + ".svg", shell=True)
    # Remove temporary file(s)
    subprocess.call("rm " + tmp_dir + "genes_*" + 
                    request + "*.json", shell=True)


    reset_output()

    return None

def main():

    # Import LDmatrix options
    if len(sys.argv) == 5:
        snplst = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        genome_build = sys.argv[4]
        r2_d = "r2"
        collapseTranscript = True
    elif len(sys.argv) == 7:
        snplst = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        genome_build = sys.argv[4]
        r2_d = sys.argv[5]
        collapseTranscript = sys.argv[6]
    else:
        sys.exit()

    # Run function
    calculate_matrix_svg(snplst, pop, request, genome_build, r2_d, collapseTranscript)


if __name__ == "__main__":
    main()
