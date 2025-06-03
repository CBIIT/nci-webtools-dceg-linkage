import json
import sys
import operator
import os
import subprocess
from multiprocessing.dummy import Pool
from math import log10
from LDcommon import retrieveAWSCredentials, get_coords_gene,genome_build_vars, connectMongoDBReadOnly,get_coords,get_output
from LDutilites import get_config, array_split

# LDassoc subprocess to export bokeh to high quality images in the background
def calculate_assoc_svg(file, region, pop, request, genome_build, myargs, myargsName, myargsOrigin):

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

    chrs=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y"]

    # Define parameters for --variant option
    if region=="variant":
        if myargsOrigin=="None":
            return None
            

    if myargsOrigin!="None":
        # Find coordinates (GRCh37/hg19) or (GRCh38/hg38) for SNP RS number
        if myargsOrigin[0:2]=="rs":
            snp=myargsOrigin

            # Connect to Mongo snp database
            db = connectMongoDBReadOnly(True)

            # Find RS number in snp database
            var_coord=get_coords(db, snp)

            if var_coord==None:
                return None
                

        elif myargsOrigin.split(":")[0].strip("chr") in chrs and len(myargsOrigin.split(":"))==2:
            snp=myargsOrigin
            #var_coord=[None,myargsOrigin.split(":")[0].strip("chr"),myargsOrigin.split(":")[1]]
            var_coord = {'chromosome':myargsOrigin.split(":")[0].strip("chr"), 'position':myargsOrigin.split(":")[1]}
        else:
            return None
            

        chromosome = var_coord['chromosome']
        org_coord = var_coord[genome_build_vars[genome_build]['position']]


    # Open Association Data
    header_list=[]
    header_list.append(myargs['chr'])
    header_list.append(myargs['bp'])
    header_list.append(myargs['pval'])

    # Load input file
    with open(file) as fp:
        header = fp.readline().strip().split()
        first = fp.readline().strip().split()

    if len(header)!=len(first):
        return None
        

    # Check header
    for item in header_list:
        if item not in header:
            return None
            

    len_head=len(header)

    chr_index=header.index(myargs['chr'])
    pos_index=header.index(myargs['bp'])
    p_index=header.index(myargs['pval'])


    # Define window of interest around query SNP
    if myargs['window']==None:
        if region=="variant":
            window=500000
        elif region=="gene":
            window=100000
        else:
            window=0
    else:
        window=myargs['window']

    if region=="variant":
        coord1=int(org_coord)-window
        if coord1<0:
            coord1=0
        coord2=int(org_coord)+window

    elif region=="gene":
        if myargsName=="None":
            return None

        # Find RS number in snp database
        db = connectMongoDBReadOnly(True)
        gene_coord = get_coords_gene(myargsName, db,genome_build)

        if gene_coord == None or gene_coord[2] == 'NA' or gene_coord == 'NA':
            return None
            
        # Define search coordinates
        coord1=int(gene_coord[2])-window
        if coord1<0:
            coord1=0
        coord2=int(gene_coord[3])+window

        # Run with --origin option
        if myargsOrigin!="None":
            if gene_coord[1]!=chromosome:
                return None
                
            if coord1>int(org_coord) or int(org_coord)>coord2:
                return None
                
        else:
            chromosome=gene_coord[1]

    elif region=="region":
        if myargs['start']==None:
            return None
            
        if myargs['end']==None:
            return None
            

        # Parse out chr and positions for --region option
        if len(myargs['start'].split(":"))!=2:
            return None
            
        if len(myargs['end'].split(":"))!=2:
            return None
            

        chr_s=myargs['start'].strip("chr").split(":")[0]
        coord_s=myargs['start'].split(":")[1]
        chr_e=myargs['end'].strip("chr").split(":")[0]
        coord_e=myargs['end'].split(":")[1]

        if chr_s not in chrs:
            return None
            
        if chr_e not in chrs:
            return None
            
        if chr_s!=chr_e:
            return None
            
        if coord_s>=coord_e:
            return None
            

        coord1=int(coord_s)-window
        if coord1<0:
            coord1=0
        coord2=int(coord_e)+window

        # Run with --origin option
        if myargsOrigin!="None":
            if chr_s!=chromosome:
                return None
                
            if coord1>int(org_coord) or int(org_coord)>coord2:
                return None
                
        else:
            chromosome=chr_s

    # Generate coordinate list and P-value dictionary
    max_window=3000000
    if coord2-coord1>max_window:
            return None
            

    assoc_coords=[]
    a_pos=[]
    assoc_dict={}
    assoc_list=[]
    with open(file) as fp:
        for line in fp:
            col=line.strip().split()
            if len(col)==len_head:
                if col[chr_index].strip("chr")==chromosome:
                    try:
                        int(col[pos_index])
                    except ValueError:
                        continue
                    else:
                        if coord1<=int(col[pos_index])<=coord2:
                            try:
                                float(col[p_index])
                            except ValueError:
                                continue
                            else:
                                coord_i = genome_build_vars[genome_build]['1000G_chr_prefix'] + col[chr_index].strip("chr") + ":" + col[pos_index] + "-" + col[pos_index]
                                assoc_coords.append(coord_i)
                                a_pos.append(col[pos_index])
                                assoc_dict[coord_i]=[col[p_index]]
                                assoc_list.append([coord_i,float(col[p_index])])


    # Coordinate list checks
    if len(assoc_coords)==0:
        return None


    # Get population ids from population output file from LDassoc.py
    pop_list=open(tmp_dir+"pops_"+request+".txt").readlines()
    ids=[]
    for i in range(len(pop_list)):
        ids.append(pop_list[i].strip())

    pop_ids=list(set(ids))


    # Define LD origin coordinate
    try:
        org_coord
    except NameError:
        for var_p in sorted(assoc_list, key=operator.itemgetter(1)):
            snp="chr"+var_p[0].split("-")[0]
       
    else:
        if genome_build_vars[genome_build]['1000G_chr_prefix'] + chromosome+":"+org_coord+"-"+org_coord not in assoc_coords:
            return None
  
    # Calculate proxy LD statistics in parallel
    if len(assoc_coords) < 60:
        num_subprocesses = 1
    # else:
    #     threads=4

    # assoc_coords_subset_chunks = np.array_split(assoc_coords, num_subprocesses)
    assoc_coords_subset_chunks = array_split(assoc_coords, num_subprocesses)

    # block=len(assoc_coords) // num_subprocesses
    commands=[]
    # for i in range(num_subprocesses):
    #     if i==min(range(num_subprocesses)) and i==max(range(num_subprocesses)):
    #         command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords)+" "+request+" "+str(i)
    #     elif i==min(range(num_subprocesses)):
    #         command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[:block])+" "+request+" "+str(i)
    #     elif i==max(range(num_subprocesses)):
    #         command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[(block*i)+1:])+" "+request+" "+str(i)
    #     else:
    #         command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[(block*i)+1:block*(i+1)])+" "+request+" "+str(i)
    #     commands.append(command)

    for subprocess_id in range(num_subprocesses):
        subprocessArgs = " ".join([str(snp), str(chromosome), str("_".join(assoc_coords_subset_chunks[subprocess_id])), str(request), str(genome_build), str(subprocess_id)])
        commands.append("python3 LDassoc_sub.py " + subprocessArgs)
     
    processes=[subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in commands]

    pool = Pool(len(processes))
    out_raw=pool.map(get_output, processes)
    pool.close()
    pool.join()


    # Aggregate output
    out_prox=[]
    for i in range(len(out_raw)):
        for j in range(len(out_raw[i])):
            col=out_raw[i][j].decode('utf-8').strip().split("\t")
            col[6]=int(col[6])
            col[7]=float(col[7])
            col[8]=float(col[8])
            col.append(abs(int(col[6])))
            pos_i_j=col[5].split(":")[1]
            coord_i_j=genome_build_vars[genome_build]['1000G_chr_prefix'] + chromosome+":"+pos_i_j+"-"+pos_i_j
            if coord_i_j in assoc_dict:
                col.append(float(assoc_dict[coord_i_j][0]))
                out_prox.append(col)


    out_dist_sort=sorted(out_prox, key=operator.itemgetter(14))
    out_p_sort=sorted(out_dist_sort, key=operator.itemgetter(15), reverse=False)

    # Organize scatter plot data
    q_rs=[]
    q_allele=[]
    q_coord=[]
    q_maf=[]
    p_rs=[]
    p_allele=[]
    p_coord=[]
    p_pos=[]
    p_maf=[]
    dist=[]
    d_prime=[]
    d_prime_round=[]
    r2=[]
    r2_round=[]
    corr_alleles=[]
    forgedb=[]
    regdb=[]
    funct=[]
    color=[]
    alpha=[]
    size=[]
    p_val=[]
    neg_log_p=[]
    for i in range(len(out_p_sort)):
        q_rs_i,q_allele_i,q_coord_i,p_rs_i,p_allele_i,p_coord_i,dist_i,d_prime_i,r2_i,corr_alleles_i,forgedb_i,regdb_i,q_maf_i,p_maf_i,funct_i,dist_abs,p_val_i=out_p_sort[i]

        q_rs.append(q_rs_i)
        q_allele.append(q_allele_i)
        q_coord.append(float(q_coord_i.split(":")[1])/1000000)
        q_maf.append(str(round(float(q_maf_i),4)))
        if p_rs_i==".":
            p_rs_i=p_coord_i
        p_rs.append(p_rs_i)
        p_allele.append(p_allele_i)
        p_coord.append(float(p_coord_i.split(":")[1])/1000000)
        p_pos.append(p_coord_i.split(":")[1])
        p_maf.append(str(round(float(p_maf_i),4)))
        dist.append(str(round(dist_i/1000000.0,4)))
        d_prime.append(float(d_prime_i))
        d_prime_round.append(str(round(float(d_prime_i),4)))
        r2.append(float(r2_i))
        r2_round.append(str(round(float(r2_i),4)))
        corr_alleles.append(corr_alleles_i)

        # P-value
        p_val.append(p_val_i)
        neg_log_p.append(-log10(p_val_i))

        # Correct Missing Annotations
        if regdb_i==".":
            regdb_i=""
        regdb.append(regdb_i)
        forgedb.append(forgedb_i)
        if funct_i==".":
            funct_i=""
        if funct_i=="NA":
            funct_i="none"
        funct.append(funct_i)

        # Set Color
        reds=["#FFCCCC","#FFCACA","#FFC8C8","#FFC6C6","#FFC4C4","#FFC2C2","#FFC0C0","#FFBEBE","#FFBCBC","#FFBABA","#FFB8B8","#FFB6B6","#FFB4B4","#FFB1B1","#FFAFAF","#FFADAD","#FFABAB","#FFA9A9","#FFA7A7","#FFA5A5","#FFA3A3","#FFA1A1","#FF9F9F","#FF9D9D","#FF9B9B","#FF9999","#FF9797","#FF9595","#FF9393","#FF9191","#FF8F8F","#FF8D8D","#FF8B8B","#FF8989","#FF8787","#FF8585","#FF8383","#FF8181","#FF7E7E","#FF7C7C","#FF7A7A","#FF7878","#FF7676","#FF7474","#FF7272","#FF7070","#FF6E6E","#FF6C6C","#FF6A6A","#FF6868","#FF6666","#FF6464","#FF6262","#FF6060","#FF5E5E","#FF5C5C","#FF5A5A","#FF5858","#FF5656","#FF5454","#FF5252","#FF5050","#FF4E4E","#FF4B4B","#FF4949","#FF4747","#FF4545","#FF4343","#FF4141","#FF3F3F","#FF3D3D","#FF3B3B","#FF3939","#FF3737","#FF3535","#FF3333","#FF3131","#FF2F2F","#FF2D2D","#FF2B2B","#FF2929","#FF2727","#FF2525","#FF2323","#FF2121","#FF1F1F","#FF1D1D","#FF1B1B","#FF1818","#FF1616","#FF1414","#FF1212","#FF1010","#FF0E0E","#FF0C0C","#FF0A0A","#FF0808","#FF0606","#FF0404","#FF0202","#FF0000"]
        if q_coord_i==p_coord_i:
            color_i="#0000FF"
            alpha_i=0.7
        else:
            if myargs['dprime']==True:
                color_i=reds[int(d_prime_i*100.0)]
                alpha_i=0.7
            elif myargs['dprime']==False:
                color_i=reds[int(r2_i*100.0)]
                alpha_i=0.7
        color.append(color_i)
        alpha.append(alpha_i)

        # Set Size
        size_i=9+float(p_maf_i)*14.0
        size.append(size_i)


    # Pull out SNPs from association file not found in 1000G
    p_plot_pos=[]
    p_plot_pval=[]
    p_plot_pos2=[]
    p_plot_pval2=[]
    p_plot_dist=[]
    index_var_pos=float(q_coord_i.split(":")[1])/1000000
    for input_pos in a_pos:
        if input_pos not in p_pos:
            p_plot_pos.append(float(input_pos)/1000000)
            p_plot_pval.append(-log10(float(assoc_dict[chromosome+":"+input_pos+"-"+input_pos][0])))
            p_plot_pos2.append("chr"+chromosome+":"+input_pos)
            p_plot_pval2.append(float(assoc_dict[chromosome+":"+input_pos+"-"+input_pos][0]))
            p_plot_dist.append(str(round(float(input_pos)/1000000-index_var_pos,4)))


    # Begin Bokeh Plotting
    from collections import OrderedDict
    from bokeh.embed import components,file_html
    from bokeh.layouts import gridplot
    from bokeh.models import HoverTool,LinearAxis,Range1d
    from bokeh.plotting import ColumnDataSource,curdoc,figure,output_file,reset_output,save
    from bokeh.resources import CDN
    from bokeh.io import export_svgs
    import svgutils.compose as sg

    reset_output()

    data_p = {'p_plot_posX': p_plot_pos, 'p_plot_pvalY': p_plot_pval, 'p_plot_pos2': p_plot_pos2, 'p_plot_pval2': p_plot_pval2, 'p_plot_dist': p_plot_dist}
    source_p = ColumnDataSource(data_p)

    # Assoc Plot
    x=p_coord
    y=neg_log_p

    data = {'x': x, 'y': y, 'qrs': q_rs, 'q_alle': q_allele, 'q_maf': q_maf, 'prs': p_rs, 'p_alle': p_allele, 'p_maf': p_maf, 'dist': dist, 'r': r2_round, 'd': d_prime_round, 'alleles': corr_alleles, 'forgedb':forgedb,'regdb': regdb, 'funct': funct, 'p_val': p_val, 'size': size, 'color': color, 'alpha': alpha}
    source = ColumnDataSource(data)

    whitespace=0.01
    xr=Range1d(start=coord1/1000000.0-whitespace, end=coord2/1000000.0+whitespace)
    yr=Range1d(start=-0.03, end=max(y)*1.03)
    sup_2="\u00B2"

    assoc_plot=figure(
                title="P-values and Regional LD for "+snp+" in "+pop,
                min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, 
                width=900,
                height=600,
                x_range=xr, y_range=yr,
                tools="tap,pan,box_zoom,wheel_zoom,box_select,undo,redo,reset,save", 
                toolbar_location="above")

    assoc_plot.title.align="center"

    # Add recombination rate from LDassoc.py output file
    recomb_file = tmp_dir + "recomb_" + request + ".json"
    recomb_raw = open(recomb_file).readlines()

    recomb_x=[]
    recomb_y=[]

    for recomb_raw_obj in recomb_raw:
        recomb_obj = json.loads(recomb_raw_obj)
        recomb_x.append(int(recomb_obj[genome_build_vars[genome_build]['position']])/1000000.0)
        recomb_y.append(float(recomb_obj['rate'])/100*max(y))

    assoc_plot.line(recomb_x, recomb_y, line_width=1, color="black", alpha=0.5)

    # Add genome-wide significance
    a = [coord1/1000000.0-whitespace,coord2/1000000.0+whitespace]
    b = [-log10(0.00000005),-log10(0.00000005)]
    assoc_plot.line(a, b, color="blue", alpha=0.5)

    assoc_points_not1000G=assoc_plot.scatter(x='p_plot_posX', y='p_plot_pvalY', size=9+float("0.25")*14.0, source=source_p, line_color="gray", fill_color="white")
    assoc_points=assoc_plot.scatter(x='x', y='y', size='size', color='color', alpha='alpha', source=source)
    assoc_plot.add_tools(HoverTool(renderers=[assoc_points_not1000G], tooltips=OrderedDict([("Variant", "@p_plot_pos2"), ("P-value", "@p_plot_pval2"), ("Distance (Mb)", "@p_plot_dist")])))

    hover=HoverTool(renderers=[assoc_points])
    hover.tooltips=OrderedDict([
        ("Variant", "@prs @p_alle"),
        ("P-value", "@p_val"),
        ("Distance (Mb)", "@dist"),
        ("MAF", "@p_maf"),
        ("R"+sup_2+" ("+q_rs[0]+")", "@r"),
        ("D\' ("+q_rs[0]+")", "@d"),
        ("Correlated Alleles", "@alleles"),
        ("ForgeDB Score", "@forgedb"),
        ("RegulomeDB", "@regdb"),
        ("Functional Class", "@funct"),
    ])

    assoc_plot.add_tools(hover)

    # Annotate RebulomeDB scores
    if myargs['annotate']=="forge":
        assoc_plot.text(x, y, text=forgedb, alpha=1, text_font_size="7pt", text_baseline="middle", text_align="center", angle=0)
    elif myargs['annotate']=="regulome":
        assoc_plot.text(x, y, text=regdb, alpha=1, text_font_size="7pt", text_baseline="middle", text_align="center", angle=0)

    assoc_plot.yaxis.axis_label="-log10 P-value"

    assoc_plot.extra_y_ranges = {"y2_axis": Range1d(start=-3, end=103)}
    assoc_plot.add_layout(LinearAxis(y_range_name="y2_axis", axis_label="Combined Recombination Rate (cM/Mb)"), "right")  ## Need to confirm units


    # Rug Plot
    y2_ll=[-0.03]*len(x)
    y2_ul=[1.03]*len(x)
    yr_rug=Range1d(start=-0.03, end=1.03)

    data_rug = {'x': x, 'y': y, 'y2_ll': y2_ll, 'y2_ul': y2_ul,'qrs': q_rs, 'q_alle': q_allele, 'q_maf': q_maf, 'prs': p_rs, 'p_alle': p_allele, 'p_maf': p_maf, 'dist': dist, 'r': r2_round, 'd': d_prime_round, 'alleles': corr_alleles,'forgedb':forgedb, 'regdb': regdb, 'funct': funct, 'p_val': p_val, 'size': size, 'color': color, 'alpha': alpha}
    source_rug = ColumnDataSource(data_rug)

    rug=figure(
            x_range=xr, y_range=yr_rug, border_fill_color='white', y_axis_type=None,
            title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, 
            width=900, height=50, tools="xpan,tap,wheel_zoom")

    rug.segment(x0='x', y0='y2_ll', x1='x', y1='y2_ul', source=source_rug, color='color', alpha='alpha', line_width=1)
    rug.toolbar_location=None


    # Gene Plot (All Transcripts)
    if myargs['transcript']==True:
        # Get genes from LDassoc.py output file
        genes_file = tmp_dir + "genes_" + request + ".json"
        genes_raw = open(genes_file).readlines()

        genes_plot_start=[]
        genes_plot_end=[]
        genes_plot_y=[]
        genes_plot_name=[]
        exons_plot_x=[]
        exons_plot_y=[]
        exons_plot_w=[]
        exons_plot_h=[]
        exons_plot_name=[]
        exons_plot_id=[]
        exons_plot_exon=[]
        message = ["Too many genes to plot."]
        lines=[0]
        gap=80000
        tall=0.75
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
                i=0
                y_coord=None
                while y_coord==None:
                    if i>len(lines)-1:
                        y_coord=i+1
                        lines.append(int(txEnd))
                    elif int(txStart)>(gap+lines[i]):
                        y_coord=i+1
                        lines[i]=int(txEnd)
                    else:
                        i+=1

                genes_plot_start.append(int(txStart)/1000000.0)
                genes_plot_end.append(int(txEnd)/1000000.0)
                genes_plot_y.append(y_coord)
                genes_plot_name.append(name+"  ")

                for i in range(len(e_start)-1):
                    if strand=="+":
                        exon=i+1
                    else:
                        exon=len(e_start)-1-i

                    width=(int(e_end[i])-int(e_start[i]))/1000000.0
                    x_coord=int(e_start[i])/1000000.0+(width/2)

                    exons_plot_x.append(x_coord)
                    exons_plot_y.append(y_coord)
                    exons_plot_w.append(width)
                    exons_plot_h.append(tall)
                    exons_plot_name.append(name)
                    exons_plot_id.append(id)
                    exons_plot_exon.append(exon)


        n_rows=len(lines)
        genes_plot_yn=[n_rows-x+0.5 for x in genes_plot_y]
        exons_plot_yn=[n_rows-x+0.5 for x in exons_plot_y]
        yr2=Range1d(start=0, end=n_rows)

        data_gene_plot = {'exons_plot_x': exons_plot_x, 'exons_plot_yn': exons_plot_yn, 'exons_plot_w': exons_plot_w, 'exons_plot_h': exons_plot_h,'exons_plot_name': exons_plot_name, 'exons_plot_id': exons_plot_id, 'exons_plot_exon': exons_plot_exon}
        source_gene_plot=ColumnDataSource(data_gene_plot)

        max_genes = 40
        # if len(lines) < 3 or len(genes_raw) > max_genes:
        if len(lines) < 3:
            plot_h_pix = 250
        else:
            plot_h_pix = 250 + (len(lines) - 2) * 50

        gene_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
                            x_range=xr, y_range=yr2, border_fill_color='white',
                            title="",  
                            width=900, height=plot_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,save")

        # if len(genes_raw) <= max_genes:
        gene_plot.segment(genes_plot_start, genes_plot_yn, genes_plot_end,
                            genes_plot_yn, color="black", alpha=1, line_width=2)
        gene_plot.rect(x='exons_plot_x', y='exons_plot_yn', width='exons_plot_w', height='exons_plot_h',
                        source=source_gene_plot, fill_color="grey", line_color="grey")
        gene_plot.text(genes_plot_start, genes_plot_yn, text=genes_plot_name, alpha=1, text_font_size="7pt",
                        text_font_style="bold", text_baseline="middle", text_align="right", angle=0)
        hover = gene_plot.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ("Gene", "@exons_plot_name"),
            ("Transcript ID", "@exons_plot_id"),
            ("Exon", "@exons_plot_exon"),
        ])

        # else:
        #     x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
        #     gene_plot.text(x_coord_text, n_rows / 2.0, text=message, alpha=1,
        #                     text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

        gene_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_plot.yaxis.axis_label = "Genes (All Transcripts)"
        gene_plot.ygrid.grid_line_color = None
        gene_plot.yaxis.axis_line_color = None
        gene_plot.yaxis.minor_tick_line_color = None
        gene_plot.yaxis.major_tick_line_color = None
        gene_plot.yaxis.major_label_text_color = None

        gene_plot.toolbar_location = "below"

        # Change output backend to SVG temporarily for headless export
        assoc_plot.output_backend = "svg"
        rug.output_backend = "svg"
        gene_plot.output_backend = "svg"
        export_svgs(assoc_plot, filename=tmp_dir + "assoc_plot_1_" + request + ".svg")
        export_svgs(gene_plot, filename=tmp_dir + "gene_plot_1_" + request + ".svg")

        # 1 pixel = 0.0264583333 cm
        svg_height = str(20.00 + (0.0264583333 * plot_h_pix)) + "cm"
        svg_height_scaled = str(100.00 + (0.1322916665 * plot_h_pix)) + "cm"
        
        # Concatenate svgs
        sg.Figure("24.59cm", svg_height,
            sg.SVG(tmp_dir + "assoc_plot_1_" + request + ".svg"),
            sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").move(-40, 630)
            ).save(tmp_dir + "assoc_plot_" + request + ".svg")

        sg.Figure("122.95cm", svg_height_scaled,
            sg.SVG(tmp_dir + "assoc_plot_1_" + request + ".svg").scale(5),
            sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").scale(5).move(-200, 3150)
            ).save(tmp_dir + "assoc_plot_scaled_" + request + ".svg")

        # Export to PDF
        subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "assoc_plot_" + request + ".svg " + tmp_dir + "assoc_plot_" + request + ".pdf", shell=True)
        # Export to PNG
        subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "assoc_plot_scaled_" + request + ".svg " + tmp_dir + "assoc_plot_" + request + ".png", shell=True)
        # Export to JPEG
        subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "assoc_plot_scaled_" + request + ".svg " + tmp_dir + "assoc_plot_" + request + ".jpeg", shell=True)    
        # Remove individual SVG files after they are combined
        subprocess.call("rm " + tmp_dir + "assoc_plot_1_" + request + ".svg", shell=True)
        subprocess.call("rm " + tmp_dir + "gene_plot_1_" + request + ".svg", shell=True)
        # Remove scaled SVG file after it is converted to png and jpeg
        subprocess.call("rm " + tmp_dir + "assoc_plot_scaled_" + request + ".svg", shell=True)



    # Gene Plot (Collapsed)
    else:
        # Get genes from LDassoc.py output file
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
            for gene_raw_obj in genes_c_raw:
                gene_c_obj = json.loads(gene_raw_obj)
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
                            title="",  
                            width=900, height=plot_c_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,save")

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
        #     x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
        #     gene_c_plot.text(x_coord_text, n_rows_c / 2.0, text=message_c, alpha=1,
        #                     text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

        gene_c_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_c_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
        gene_c_plot.ygrid.grid_line_color = None
        gene_c_plot.yaxis.axis_line_color = None
        gene_c_plot.yaxis.minor_tick_line_color = None
        gene_c_plot.yaxis.major_tick_line_color = None
        gene_c_plot.yaxis.major_label_text_color = None

        gene_c_plot.toolbar_location = "below"
        
        # Change output backend to SVG temporarily for headless export
        assoc_plot.output_backend = "svg"
        rug.output_backend = "svg"
        gene_c_plot.output_backend = "svg"
        export_svgs(assoc_plot, filename=tmp_dir + "assoc_plot_1_" + request + ".svg")
        export_svgs(gene_c_plot, filename=tmp_dir + "gene_plot_1_" + request + ".svg")

        # 1 pixel = 0.0264583333 cm
        svg_height = str(20.00 + (0.0264583333 * plot_c_h_pix)) + "cm"
        svg_height_scaled = str(100.00 + (0.1322916665 * plot_c_h_pix)) + "cm"

        # Concatenate svgs
        sg.Figure("24.59cm", svg_height,
            sg.SVG(tmp_dir + "assoc_plot_1_" + request + ".svg"),
            sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").move(-40, 630)
            ).save(tmp_dir + "assoc_plot_" + request + ".svg")

        sg.Figure("122.95cm", svg_height_scaled,
            sg.SVG(tmp_dir + "assoc_plot_1_" + request + ".svg").scale(5),
            sg.SVG(tmp_dir + "gene_plot_1_" + request + ".svg").scale(5).move(-200, 3150)
            ).save(tmp_dir + "assoc_plot_scaled_" + request + ".svg")

        # Export to PDF
        subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "assoc_plot_" + request + ".svg " + tmp_dir + "assoc_plot_" + request + ".pdf", shell=True)
        # Export to PNG
        subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "assoc_plot_scaled_" + request + ".svg " + tmp_dir + "assoc_plot_" + request + ".png", shell=True)
        # Export to JPEG
        subprocess.call("phantomjs ./rasterize.js " + tmp_dir + "assoc_plot_scaled_" + request + ".svg " + tmp_dir + "assoc_plot_" + request + ".jpeg", shell=True)    
        # Remove individual SVG files after they are combined
        subprocess.call("rm " + tmp_dir + "assoc_plot_1_" + request + ".svg", shell=True)
        subprocess.call("rm " + tmp_dir + "gene_plot_1_" + request + ".svg", shell=True)
        # Remove scaled SVG file after it is converted to png and jpeg
        subprocess.call("rm " + tmp_dir + "assoc_plot_scaled_" + request + ".svg", shell=True)

    reset_output()

    # Remove temporary files
    subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
    subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
    subprocess.call("rm "+tmp_dir+"genes_*"+request+"*.json", shell=True)
    subprocess.call("rm "+tmp_dir+"recomb_"+request+".json", shell=True)
    subprocess.call("rm "+tmp_dir+"assoc_args"+request+".json", shell=True)

    print("Bokeh high quality image export complete!")

    # Return plot output
    return None

def main():

    # Import LDassoc options
    if len(sys.argv) == 9:
        filename = sys.argv[1]
        file = sys.argv[2]
        region = sys.argv[3]
        pop = sys.argv[4]
        request = sys.argv[5]
        genome_build = sys.argv[6]
        myargsName = sys.argv[7]
        myargsOrigin = sys.argv[8]
    else:
        sys.exit()
    # Load args parameters passed from LDassoc.py
    with open(filename) as f:
        args = json.load(f)

    # Run function
    calculate_assoc_svg(file, region, pop, request, genome_build, args, myargsName, myargsOrigin)


if __name__ == "__main__":
    main()