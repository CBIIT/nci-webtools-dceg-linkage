#!/usr/bin/env python3
import json
import math
import os
import subprocess
import sys
from LDcommon import retrieveAWSCredentials, genome_build_vars, getRefGene,connectMongoDBReadOnly
from LDcommon import get_coords,replace_coords_rsid_list,validsnp,get_population
from LDcommon import set_alleles
from LDutilites import get_config
from LDcommon import get_1000g_data,parse_vcf,check_same_chromosome,get_forgeDB

# Create LDmatrix function
def calculate_matrix(snplst, pop, request, web, request_method, genome_build, r2_d="r2", collapseTranscript=True,annotate="forge"):
    # Set data directories using config.yml
    param_list = get_config()
    dbsnp_version = param_list['dbsnp_version']
    population_samples_dir = param_list['population_samples_dir']
    data_dir = param_list['data_dir']
    tmp_dir = param_list['tmp_dir']
    genotypes_dir = param_list['genotypes_dir']
    aws_info = param_list['aws_info']
    
    export_s3_keys = retrieveAWSCredentials()
    
    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Create JSON output
    out_json = open(tmp_dir + "matrix" + request + ".json", "w")
    output = {}

    if web or request_method == "GET":
        snp_limit = 300
    else:
        snp_limit = 3000
    snps = validsnp(snplst,genome_build,snp_limit)
    #if return value is string, then it is error message and need to return the message
    if isinstance(snps, str):
        print(snps, file=out_json)
        out_json.close()
        return("", "")

    # Select desired ancestral populations
    pop_ids = get_population(pop,request,output)
    if isinstance(pop_ids,str):
        print(pop_ids, file=out_json)
        out_json.close()
        return("","")
  
    # Connect to Mongo snp database
    db = connectMongoDBReadOnly(web)

    snps = replace_coords_rsid_list(db, snps,genome_build,output)

    # Find RS numbers in snp database
    rs_nums = []
    snp_pos = []
    snp_coords = []
    warn = []
    tabix_coords = ""
    for snp_i in snps:
        if len(snp_i) > 0:
            if len(snp_i[0]) > 2:
                if (snp_i[0][0:2] == "rs" or snp_i[0][0:3] == "chr") and snp_i[0][-1].isdigit():
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

    # Check RS numbers were found
    if warn != []:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)
        else:
            output["warning"] = "The following RS number(s) or coordinate(s) inputs have warnings: " + ", ".join(warn)

    if len(rs_nums) == 0:
        output["error"] = "Input variant list does not contain any valid RS numbers or coordinates."
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    # Check SNPs are all on the same chromosome
    check_same_chromosome(snp_coords,output)
    # Check max distance between SNPs
    distance_bp = []
    for i in range(len(snp_coords)):
        distance_bp.append(int(snp_coords[i][2]))
    distance_max = max(distance_bp) - min(distance_bp)
    if distance_max > 1000000:
        if "warning" in output:
            output["warning"] = output["warning"] + \
                ". Switch rate errors become more common as distance between query variants increases (Query range = " + str(
                    distance_max) + " bp)"
        else:
            output[
                "warning"] = "Switch rate errors become more common as distance between query variants increases (Query range = " + str(distance_max) + " bp)"

    vcf,head = get_1000g_data(snp_pos, snp_coords,genome_build, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])

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
   
       # parse vcf
    snp_dict,missing_snp,output = parse_vcf(vcf,snp_coords,output,genome_build,True)
     # all lists does not contain data which is returned from 1000G
 
    if "error" in output:
        json_output = json.dumps(output, sort_keys=True, indent=2)
        print(json_output, file=out_json)
        out_json.close()
        return("", "")

    rsnum_lst = []
    allele_lst = []
    pos_lst = []
    #print(snp_dict)
    for s_key in snp_dict:
        # parse snp_key such as chr7:pos_rs4
        snp_keys = s_key.split("_")
        snp_key = snp_keys[0].split(':')[1]
        rs_input = snp_keys[1]
        geno_list = snp_dict[s_key]
        for geno in geno_list:
            geno = geno.strip().split()
            geno[0] = geno[0].lstrip('chr')
            #print(geno)
            # if 1000G position does not match dbSNP position for variant, use dbSNP position
            if geno[1] != snp_key:
                mismatch_msg = "Genomic position ("+geno[1]+") in 1000G data does not match dbSNP" + \
                        dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ") search coordinates for query variant " + \
                         rs_input + ". "
                if "warning" in output:
                    output["warning"] = output["warning"] + mismatch_msg
                else:
                    output["warning"] = mismatch_msg
                # throw an error in the event of missing query SNPs in 1000G data
                geno[1] = snp_key
           
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

                rsnum_lst.append(rs_input)

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

    # Generate D' and R2 output matrices
    d_out = open(tmp_dir + "d_prime_" + request + ".txt", "w")
    r_out = open(tmp_dir + "r2_" + request + ".txt", "w")

    print("RS_number" + "\t" + "\t".join(rsnum_lst), file=d_out)
    print("RS_number" + "\t" + "\t".join(rsnum_lst), file=r_out)

    dim = len(ld_matrix)
    for i in range(dim):
        temp_d = [rsnum_lst[i]]
        temp_r = [rsnum_lst[i]]
        for j in range(dim):
            temp_d.append(str(ld_matrix[i][j][7]))
            temp_r.append(str(ld_matrix[i][j][8]))
        print("\t".join(temp_d), file=d_out)
        print("\t".join(temp_r), file=r_out)

    out_script = ""
    out_div = ""

    if web:
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
            if "warning" in output:
                output["warning"] = output["warning"] + ". " + r2_d + \
                    " is not an acceptable value for r2_d (r2 or d required). r2 is used by default"
            else:
                output["warning"] = r2_d + \
                    " is not an acceptable value for r2_d (r2 or d required). r2 is used by default"
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
            

        #print("early x", x)
        #print("snp", rsnum_lst)
        rs_forge_score = []
        if annotate == "forge":
            for rs_forge in rsnum_lst:
                rs_forge_score.append(get_forgeDB(db,rs_forge))
        else:
            rs_forge_score = []
        # Generate error if less than two SNPs
        if len(x) < 2:
            output["error"] = "Less than two variants to plot. " + str(output["warning"] if "warning" in output else "")
            json_output = json.dumps(output, sort_keys=True, indent=2)
            print(json_output, file=out_json)
            out_json.close()
            return("", "")

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

        # Delete redundant data
        # startidx = []
        # Isolate indices of elements in y=x
        # for xidx, xn in enumerate(data['xname']):
        # for yidx, yn in enumerate(data['yname']):
        # if xn == yn and xidx == yidx:
        # startidx.append(xidx)
        # Flatten list snps
        # flat_snps = [item for sublist in snps for item in sublist]
        # Reverse flattend snp list
        # rev_snps = list(reversed(flat_snps))
        # get index of every appearance of last snp in snplst
        # recsnp = rev_snps[-1]
        # print "snps", rev_snps
        # print "recsnp", recsnp
        # print "data[yname]", data['yname']
        # recsnp_idx = [rid for rid, xval in enumerate(data['yname']) if xval == recsnp]
        # print "recsnp_idx", recsnp_idx
        # Add range of indices between y=x and height of y at x
        # newidx = []
        # print "startidx", startidx
        # print "recsnp_idx", recsnp_idx
        # for i in range(0, len(startidx)):
        #     if startidx[i] != recsnp_idx[i]:
        #         newidx.append(range(startidx[i], recsnp_idx[i]))
        #         newidx.append([recsnp_idx[i]])
        #     else:
        #         newidx.append([startidx[i]])
        # Flatten list indices
        # flat_newidx = [item for sublist in newidx for item in sublist]
        # Add only whitelisted indices to new data dict
        # new_data = {}
        # for key in data:
        #     new_data[key] = []
        #     for idx, val in enumerate(data[key]):
        #         if idx in flat_newidx:
        #             new_data[key].append(val)

        # debug prints for 45 degree rotation
        # print "###################################"
        # print "START - debug prints for 45 degree rotation"
        # for i in data:
        #     print (i, data[i])
        # print "###################################"
        # for i in new_data:
        #     print (i, new_data[i])
        # print "END   - debug prints for 45 degree rotation"
        # print "###################################"

        # source = ColumnDataSource(new_data)
        source = ColumnDataSource(data)
        threshold = 70
        if len(snps) < threshold:
            matrix_plot = figure(outline_line_color="white", min_border_top=0, min_border_bottom=2, min_border_left=100, min_border_right=5,
                                x_range=xr, y_range=list(reversed(rsnum_lst)),
                                h_symmetry=False, v_symmetry=False, border_fill_color='white', x_axis_type=None, logo=None,
                                tools="hover,undo,redo,reset,pan,box_zoom,previewsave", title=" ", plot_width=800, plot_height=700)
            # CHANGE AXIS LABELS & LINE COLOR:
            # matrix_plot = figure(outline_line_color="white", min_border_top=0, min_border_right=5,
            #                     x_range=xr, y_range=list(rsnum_lst),
            #                     h_symmetry=False, v_symmetry=False, border_fill_color='white', background_fill_color="beige", logo=None,
            #                     tools="hover,undo,redo,reset,pan,box_zoom,previewsave", title=" ", plot_width=800, plot_height=700)

        else:
            matrix_plot = figure(outline_line_color="white", min_border_top=0, min_border_bottom=2, min_border_left=100, min_border_right=5,
                                x_range=xr, y_range=list(reversed(rsnum_lst)),
                                h_symmetry=False, v_symmetry=False, border_fill_color='white', x_axis_type=None, y_axis_type=None, logo=None,
                                tools="hover,undo,redo,reset,pan,box_zoom,previewsave", title=" ", plot_width=800, plot_height=700)
            # CHANGE AXIS LABELS & LINE COLOR:
            # matrix_plot = figure(outline_line_color="white", min_border_top=0, min_border_right=5,
            #                     x_range=xr, y_range=list(rsnum_lst),
            #                     h_symmetry=False, v_symmetry=False, border_fill_color='white', background_fill_color="beige", logo=None,
            #                     tools="hover,undo,redo,reset,pan,box_zoom,previewsave", title=" ", plot_width=800, plot_height=700)

        matrix_plot.rect(x='xname_pos', y='yname', width=0.95 * spacing, height=0.95, source=source,
                        color="box_color", alpha="box_trans", line_color=None)
        # Rotate LDmatrix 45 degrees
        # matrix_plot.rect(x='xname_pos', y='yname', width=0.95 * spacing, height=0.95, angle=0.785398, source=source,
        #                 color="box_color", alpha="box_trans", line_color=None)
        # print "spacing"
        # print spacing
        # matrix_plot.square(x='xname_pos', y='yname', size=4 * spacing, angle=0.785398, source=source,
        #                 color="box_color", alpha="box_trans", line_color=None)

        matrix_plot.grid.grid_line_color = None
        matrix_plot.axis.axis_line_color = None
        matrix_plot.axis.major_tick_line_color = None
        if len(snps) < threshold:
            matrix_plot.axis.major_label_text_font_size = "8pt"
            matrix_plot.xaxis.major_label_orientation = "vertical"

        matrix_plot.axis.major_label_text_font_style = "normal"
        matrix_plot.xaxis.major_label_standoff = 0
        
        y_text = []
        x_text = []
        start_x = x[0] - buffer+spacing/2
        ycount = 0
        total_y=len(y)
        font_divider = 0
        if total_y < 20:
            font_divider= 1.25*total_y
        elif total_y>=20 and total_y < 50:
            font_divider = 0.7*total_y
        else:
            font_divider = 0.5*total_y
        #num_font = total_y if total_y < 40 else int(total_y/3)
        #print("####", total_y, font_divider)
        for y_y in y:
            y_text.append(total_y - y_y-ycount)
            x_text.append(start_x+spacing*ycount)
            ycount += 1        
        text_font = str(int(20*10/font_divider))+'pt'
        matrix_plot.text(x_text, y_text, text=rs_forge_score, alpha=1, text_font_size=text_font, text_baseline="middle", text_align="center", angle=0,text_color="white")
        
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
            genes_json = getRefGene(db, genes_file, snp_coords[1][1], int((x[0] - buffer) * 1000000), int((x[-1] + buffer) * 1000000), genome_build, False)

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

            out_grid = gridplot(matrix_plot, connector, rug, gene_plot,
                                ncols=1, toolbar_options=dict(logo=None))

        # Gene Plot (Collapsed)
        else:
            genes_c_file = tmp_dir + "genes_c_" + request + ".json"
            genes_c_json = getRefGene(db, genes_c_file, snp_coords[1][1], int((x[0] - buffer) * 1000000), int((x[-1] + buffer) * 1000000), genome_build, True)

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

            gene_c_plot.xaxis.axis_label = "Chromosome " + snp_coords[1][1] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
            gene_c_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
            gene_c_plot.ygrid.grid_line_color = None
            gene_c_plot.yaxis.axis_line_color = None
            gene_c_plot.yaxis.minor_tick_line_color = None
            gene_c_plot.yaxis.major_tick_line_color = None
            gene_c_plot.yaxis.major_label_text_color = None

            gene_c_plot.toolbar_location = "below"
            
            out_grid = gridplot(matrix_plot, rug, gene_c_plot,
                        ncols=1, toolbar_options=dict(logo=None))

        # Generate high quality images only if accessed via web instance
        
        # Open thread for high quality image exports
        command = "python3 LDmatrix_plot_sub.py " + snplst + " " + pop + " " + request + " " + genome_build + " " + r2_d + " " + collapseTranscript + " "+ annotate
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        ###########################
        # Html output for testing #
        ###########################
        # html=file_html(out_grid, CDN, "Test Plot")
        # out_html=open("LDmatrix.html","w")
        # print >> out_html, html
        # out_html.close()

        out_script, out_div = components(out_grid, CDN)
        reset_output()

    # Return output
    json_output = json.dumps(output, sort_keys=True, indent=2)
    print(json_output, file=out_json)
    out_json.close()
    return(out_script, out_div)

def main():
    tmp_dir = "./tmp/"

    # Import LDmatrix options
    if len(sys.argv) == 6:
        snplst = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        web = sys.argv[4]
        genome_build = sys.argv[5]
        r2_d = "r2"
        collapseTranscript = True
    elif len(sys.argv) == 8:
        snplst = sys.argv[1]
        pop = sys.argv[2]
        request = sys.argv[3]
        web = sys.argv[4]
        genome_build = sys.argv[5]
        r2_d = sys.argv[6]
        collapseTranscript = sys.argv[7]
    else:
        print("Correct useage is: LDmatrix.py snplst populations request (optional: r2_d)")
        sys.exit()

    # Run function
    out_script, out_div = calculate_matrix(snplst, pop, request, web, "GET", genome_build, r2_d, collapseTranscript)

    # Print output
    with open(tmp_dir + "matrix" + request + ".json") as f:
        json_dict = json.load(f)

    try:
        json_dict["error"]

    except KeyError:
        print("\nOutput saved as: d_prime_" + request + ".txt and r2_" + request + ".txt")

        try:
            json_dict["warning"]

        except KeyError:
            print("")
        else:
            print("")
            print("WARNING: " + json_dict["warning"] + "!")
            print("")

    else:
        print("")
        print(json_dict["error"])
        print("")


if __name__ == "__main__":
    main()


