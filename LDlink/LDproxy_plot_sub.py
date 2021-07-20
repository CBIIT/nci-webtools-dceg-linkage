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
from multiprocessing.dummy import Pool
import math


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

def calculate_proxy_svg(snp, pop, request, r2_d="r2", window=500000):

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    env = config['env']
    api_mongo_addr = config['api']['api_mongo_addr']
    vcf_dir = config['data']['vcf_dir']
    mongo_username = config['database']['mongo_user_readonly']
    mongo_password = config['database']['mongo_password']
    mongo_port = config['database']['mongo_port']
    num_subprocesses = config['performance']['num_subprocesses']

    tmp_dir = "./tmp/"

    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    if request is False:
        request = str(time.strftime("%I%M%S"))

    # Create JSON output

    # Find coordinates (GRCh37/hg19) for SNP RS number
    
    # Connect to Mongo snp database
    if env == 'local':
        mongo_host = api_mongo_addr
    else: 
        mongo_host = 'localhost'
    client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
    db = client["LDLink"]

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
        query_results = db.dbsnp.find({"chromosome": chro.upper() if chro == 'x' or chro == 'y' else chro, "position_grch37": pos})
        query_results_sanitized = json.loads(json_util.dumps(query_results))
        return query_results_sanitized

    # Replace input genomic coordinates with variant ids (rsids)
    def replace_coord_rsid(db, snp):
        if snp[0:2] == "rs":
            return snp
        else:
            snp_info_lst = get_rsnum(db, snp)
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
                    elif len(ref_variants) == 0 and len(snp_info_lst) > 1:
                        var_id = "rs" + snp_info_lst[0]['id']
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

    snp = replace_coord_rsid(db, snp)

    # Find RS number in snp database
    snp_coord = get_coords(db, snp)

    # Get population ids from LDproxy.py tmp output files
    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
    ids = []
    for i in range(len(pop_list)):
        ids.append(pop_list[i].strip())

    pop_ids = list(set(ids))

    # Extract query SNP phased genotypes
    vcf_file = vcf_dir + \
        snp_coord['chromosome'] + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"

    tabix_snp_h = "tabix -H {0} | grep CHROM".format(vcf_file)
    proc_h = subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE)
    head = [x.decode('utf-8') for x in proc_h.stdout.readlines()][0].strip().split()

    tabix_snp = "tabix {0} {1}:{2}-{2} | grep -v -e END > {3}".format(
        vcf_file, snp_coord['chromosome'], snp_coord['position'], tmp_dir + "snp_no_dups_" + request + ".vcf")
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
        if geno == []:
            subprocess.call("rm " + tmp_dir + "pops_" +
                            request + ".txt", shell=True)
            subprocess.call("rm " + tmp_dir + "*" +
                            request + "*.vcf", shell=True)
            return None
    else:
        geno = vcf[0].strip().split()

    if geno[2] != snp:
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
    coord1 = int(snp_coord['position']) - window
    if coord1 < 0:
        coord1 = 0
    coord2 = int(snp_coord['position']) + window

    # Calculate proxy LD statistics in parallel
    # threads = 4
    # block = (2 * window) // 4
    # block = (2 * window) // num_subprocesses
    windowChunkRanges = chunkWindow(int(snp_coord['position']), window, num_subprocesses)

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
        getWindowVariantsArgs = " ".join(["True", str(snp), str(snp_coord['chromosome']), str(windowChunkRanges[subprocess_id][0]), str(windowChunkRanges[subprocess_id][1]), str(request), str(subprocess_id)])
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

    # Get recomb from LDproxy.py tmp output files
    filename = tmp_dir + "recomb_" + request + ".txt"
    recomb_raw = open(filename).readlines()
    recomb_x = []
    recomb_y = []
    for i in range(len(recomb_raw)):
        chr, pos, rate = recomb_raw[i].strip().split()
        recomb_x.append(int(pos) / 1000000.0)
        recomb_y.append(float(rate) / 100.0)

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

    # Gene Plot
    # Get genes from LDproxy.py tmp output files
    filename = tmp_dir + "genes_" + request + ".txt"
    genes_raw = open(filename).readlines()

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
    if genes_raw != None:
        for i in range(len(genes_raw)):
            bin, name_id, chrom, strand, txStart, txEnd, cdsStart, cdsEnd, exonCount, exonStarts, exonEnds, score, name2, cdsStartStat, cdsEndStat, exonFrames = genes_raw[
                i].strip().split()
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
        plot_h_pix = 150
    else:
        plot_h_pix = 150 + (len(lines) - 2) * 50

    gene_plot = figure(
        x_range=xr, y_range=yr2, border_fill_color='white',
        title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
        plot_width=900, plot_height=plot_h_pix, tools="hover,tap,xpan,box_zoom,undo,redo,reset,previewsave", logo=None)

    gene_plot.segment(genes_plot_start, genes_plot_yn, genes_plot_end,
                      genes_plot_yn, color="black", alpha=1, line_width=2)

    gene_plot.rect(x='exons_plot_x', y='exons_plot_yn', width='exons_plot_w', height='exons_plot_h',
                   source=source_gene_plot, fill_color="grey", line_color="grey")
    gene_plot.xaxis.axis_label = "Chromosome " + \
        snp_coord['chromosome'] + " Coordinate (Mb)(GRCh37)"
    gene_plot.yaxis.axis_label = "Genes"
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
    subprocess.call("rm " + tmp_dir + "genes_" + request + ".txt", shell=True)
    subprocess.call("rm " + tmp_dir + "recomb_" + request + ".txt", shell=True)

    # Return plot output
    return None


def main():

    # Import LDproxy options
    if len(sys.argv) == 5:
        snp = sys.argv[1]
        pop = sys.argv[2]
        request = False
        r2_d = "r2"
        window = sys.argv[3]
    elif len(sys.argv) == 6:
        snp = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        r2_d = sys.argv[4]
        window = sys.argv[5]
    else:
        sys.exit()

    # Run function
    calculate_proxy_svg(snp, pop, request, r2_d, int(window))


if __name__ == "__main__":
    main()
