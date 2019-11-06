import yaml
import argparse
import json
import sys
import csv
import operator
import os
import sqlite3
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
from multiprocessing.dummy import Pool
from math import log10
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
username = contents[0].split('=')[1]
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])


# LDassoc subprocess to export bokeh to high quality images in the background
def calculate_assoc_svg(file, region, pop, request, myargs, myargsName, myargsOrigin):

    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    gene_dir2 = config['data']['gene_dir2']
    vcf_dir = config['data']['vcf_dir']

    tmp_dir = "./tmp/"


    # Ensure tmp directory exists
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)


    chrs=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y"]

    # Define parameters for --variant option
    if region=="variant":
        if myargsOrigin=="None":
            return None
            

    if myargsOrigin!="None":
        # Find coordinates (GRCh37/hg19) for SNP RS number
        if myargsOrigin[0:2]=="rs":
            snp=myargsOrigin

            # Connect to Mongo snp database
            client = MongoClient('mongodb://'+username+':'+password+'@localhost/admin', port)
            db = client["LDLink"]


            def get_coords_var(db, rsid):
                rsid = rsid.strip("rs")
                query_results = db.dbsnp151.find_one({"id": rsid})
                query_results_sanitized = json.loads(json_util.dumps(query_results))
                return query_results_sanitized

            # Find RS number in snp database
            var_coord=get_coords_var(db, snp)

            if var_coord==None:
                return None
                

        elif myargsOrigin.split(":")[0].strip("chr") in chrs and len(myargsOrigin.split(":"))==2:
            snp=myargsOrigin
            var_coord=[None,myargsOrigin.split(":")[0].strip("chr"),myargsOrigin.split(":")[1]]

        else:
            return None
            

        chromosome = var_coord['chromosome']
        org_coord = var_coord['position']


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
            

        # Connect to gene database
        conn=sqlite3.connect(gene_dir2)
        conn.text_factory=str
        cur=conn.cursor()

        def get_coords_gene(gene_raw):
            gene=gene_raw.upper()
            t=(gene,)
            cur.execute("SELECT * FROM genes WHERE name=?", t)
            return cur.fetchone()

        # Find RS number in snp database
        gene_coord=get_coords_gene(myargsName)

        # Close snp connection
        cur.close()
        conn.close()

        if gene_coord==None:
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
                                coord_i=col[chr_index].strip("chr")+":"+col[pos_index]+"-"+col[pos_index]
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

            # Extract lowest P SNP phased genotypes
            vcf_file=vcf_dir+chromosome+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"

            tabix_snp_h="tabix -H {0} | grep CHROM".format(vcf_file)
            proc_h=subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE)
            head=[x.decode('utf-8') for x in proc_h.stdout.readlines()][0].strip().split()

            # Check lowest P SNP is in the 1000G population and not monoallelic from LDassoc.py output file
            vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()

            if len(vcf)==0:
                continue
            elif len(vcf)>1:
                geno=vcf[0].strip().split()

            else:
                geno=vcf[0].strip().split()

            if "," in geno[3] or "," in geno[4]:
                continue

            index=[]
            for i in range(9,len(head)):
                if head[i] in pop_ids:
                    index.append(i)

            genotypes={"0":0, "1":0}
            for i in index:
                sub_geno=geno[i].split("|")
                for j in sub_geno:
                    if j in genotypes:
                        genotypes[j]+=1
                    else:
                        genotypes[j]=1

            if genotypes["0"]==0 or genotypes["1"]==0:
                continue

            org_coord=var_p[0].split("-")[1]
            break


    else:
        if chromosome+":"+org_coord+"-"+org_coord not in assoc_coords:
            return None
            

        # Extract query SNP phased genotypes
        vcf_file=vcf_dir+chromosome+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"

        tabix_snp_h="tabix -H {0} | grep CHROM".format(vcf_file)
        proc_h=subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE)
        head=[x.decode('utf-8') for x in proc_h.stdout.readlines()][0].strip().split()

        tabix_snp="tabix {0} {1}:{2}-{2} | grep -v -e END > {3}".format(vcf_file, chromosome, org_coord, tmp_dir+"snp_no_dups_"+request+".vcf")
        subprocess.call(tabix_snp, shell=True)


        # Check query SNP is in the 1000G population, has the correct RS number, and not monoallelic
        vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()

        if len(vcf)==0:
            subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
            subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
            return None
            
        elif len(vcf)>1:
            geno=[]
            for i in range(len(vcf)):
                if vcf[i].strip().split()[2]==snp:
                    geno=vcf[i].strip().split()
            if geno==[]:
                subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
                subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
                return None
                
        else:
            geno=vcf[0].strip().split()

        if geno[2]!=snp and snp[0:2]=="rs":
            snp=geno[2]

        if "," in geno[3] or "," in geno[4]:
            subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
            subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
            return None
            


        index=[]
        for i in range(9,len(head)):
            if head[i] in pop_ids:
                index.append(i)

        genotypes={"0":0, "1":0}
        for i in index:
            sub_geno=geno[i].split("|")
            for j in sub_geno:
                if j in genotypes:
                    genotypes[j]+=1
                else:
                    genotypes[j]=1

        if genotypes["0"]==0 or genotypes["1"]==0:
            subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
            subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
            return None
            


    # Calculate proxy LD statistics in parallel
    if len(assoc_coords)<60:
        threads=1
    else:
        threads=4

    block=len(assoc_coords)/threads
    commands=[]
    for i in range(threads):
        if i==min(range(threads)) and i==max(range(threads)):
            command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords)+" "+request+" "+str(i)
        elif i==min(range(threads)):
            command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[:block])+" "+request+" "+str(i)
        elif i==max(range(threads)):
            command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[(block*i)+1:])+" "+request+" "+str(i)
        else:
            command="python3 LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[(block*i)+1:block*(i+1)])+" "+request+" "+str(i)
        commands.append(command)


    processes=[subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in commands]

    # collect output in parallel
    def get_output(process):
        return process.communicate()[0].splitlines()

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
            coord_i_j=chromosome+":"+pos_i_j+"-"+pos_i_j
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
    regdb=[]
    funct=[]
    color=[]
    alpha=[]
    size=[]
    p_val=[]
    neg_log_p=[]
    for i in range(len(out_p_sort)):
        q_rs_i,q_allele_i,q_coord_i,p_rs_i,p_allele_i,p_coord_i,dist_i,d_prime_i,r2_i,corr_alleles_i,regdb_i,q_maf_i,p_maf_i,funct_i,dist_abs,p_val_i=out_p_sort[i]

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

    data = {'x': x, 'y': y, 'qrs': q_rs, 'q_alle': q_allele, 'q_maf': q_maf, 'prs': p_rs, 'p_alle': p_allele, 'p_maf': p_maf, 'dist': dist, 'r': r2_round, 'd': d_prime_round, 'alleles': corr_alleles, 'regdb': regdb, 'funct': funct, 'p_val': p_val, 'size': size, 'color': color, 'alpha': alpha}
    source = ColumnDataSource(data)

    whitespace=0.01
    xr=Range1d(start=coord1/1000000.0-whitespace, end=coord2/1000000.0+whitespace)
    yr=Range1d(start=-0.03, end=max(y)*1.03)
    sup_2="\u00B2"

    assoc_plot=figure(
                title="P-values and Regional LD for "+snp+" in "+pop,
                min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
                plot_width=900,
                plot_height=600,
                x_range=xr, y_range=yr,
                tools="tap,pan,box_zoom,wheel_zoom,box_select,undo,redo,reset,previewsave", logo=None,
                toolbar_location="above")

    assoc_plot.title.align="center"

    # Add recombination rate from LDassoc.py output file
    filename=tmp_dir+"recomb_"+request+".txt"
    recomb_raw=open(filename).readlines()
    recomb_x=[]
    recomb_y=[]
    for i in range(len(recomb_raw)):
        chr,pos,rate=recomb_raw[i].strip().split()
        recomb_x.append(int(pos)/1000000.0)
        recomb_y.append(float(rate)/100*max(y))

    assoc_plot.line(recomb_x, recomb_y, line_width=1, color="black", alpha=0.5)

    # Add genome-wide significance
    a = [coord1/1000000.0-whitespace,coord2/1000000.0+whitespace]
    b = [-log10(0.00000005),-log10(0.00000005)]
    assoc_plot.line(a, b, color="blue", alpha=0.5)

    assoc_points_not1000G=assoc_plot.circle(x='p_plot_posX', y='p_plot_pvalY', size=9+float("0.25")*14.0, source=source_p, line_color="gray", fill_color="white")
    assoc_points=assoc_plot.circle(x='x', y='y', size='size', color='color', alpha='alpha', source=source)
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
        ("RegulomeDB", "@regdb"),
        ("Functional Class", "@funct"),
    ])

    assoc_plot.add_tools(hover)

    # Annotate RebulomeDB scores
    if myargs['annotate']==True:
        assoc_plot.text(x, y, text=regdb, alpha=1, text_font_size="7pt", text_baseline="middle", text_align="center", angle=0)

    assoc_plot.yaxis.axis_label="-log10 P-value"

    assoc_plot.extra_y_ranges = {"y2_axis": Range1d(start=-3, end=103)}
    assoc_plot.add_layout(LinearAxis(y_range_name="y2_axis", axis_label="Combined Recombination Rate (cM/Mb)"), "right")  ## Need to confirm units


    # Rug Plot
    y2_ll=[-0.03]*len(x)
    y2_ul=[1.03]*len(x)
    yr_rug=Range1d(start=-0.03, end=1.03)

    data_rug = {'x': x, 'y': y, 'y2_ll': y2_ll, 'y2_ul': y2_ul,'qrs': q_rs, 'q_alle': q_allele, 'q_maf': q_maf, 'prs': p_rs, 'p_alle': p_allele, 'p_maf': p_maf, 'dist': dist, 'r': r2_round, 'd': d_prime_round, 'alleles': corr_alleles, 'regdb': regdb, 'funct': funct, 'p_val': p_val, 'size': size, 'color': color, 'alpha': alpha}
    source_rug = ColumnDataSource(data_rug)

    rug=figure(
            x_range=xr, y_range=yr_rug, border_fill_color='white', y_axis_type=None,
            title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
            plot_width=900, plot_height=50, tools="xpan,tap,wheel_zoom", logo=None)

    rug.segment(x0='x', y0='y2_ll', x1='x', y1='y2_ul', source=source_rug, color='color', alpha='alpha', line_width=1)
    rug.toolbar_location=None


    # Gene Plot (All Transcripts)
    if myargs['transcript']==True:
        # Get genes from LDassoc.py output file
        filename=tmp_dir+"genes_"+request+".txt"
        genes_raw=open(filename).readlines()

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
        if genes_raw!=None:
            for i in range(len(genes_raw)):
                bin,name_id,chrom,strand,txStart,txEnd,cdsStart,cdsEnd,exonCount,exonStarts,exonEnds,score,name2,cdsStartStat,cdsEndStat,exonFrames=genes_raw[i].strip().split()
                name=name2
                id=name_id
                e_start=exonStarts.split(",")
                e_end=exonEnds.split(",")

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
            plot_h_pix = 150
        else:
            plot_h_pix = 150 + (len(lines) - 2) * 50

        gene_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
                            x_range=xr, y_range=yr2, border_fill_color='white',
                            title="", h_symmetry=False, v_symmetry=False, logo=None,
                            plot_width=900, plot_height=plot_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,previewsave")

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

        gene_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(GRCh37)"
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
        filename_c=tmp_dir+"genes_c_"+request+".txt"
        genes_c_raw=open(filename_c).readlines()

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
        if genes_c_raw!=None:
            for i in range(len(genes_c_raw)):
                chrom,txStart,txEnd,name,exonStarts,exonEnds,transcripts=genes_c_raw[i].strip().split()
                e_start=exonStarts.split(",")
                e_end=exonEnds.split(",")
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

                for i in range(len(e_start)):

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
            plot_c_h_pix = 150
        else:
            plot_c_h_pix = 150 + (len(lines_c) - 2) * 50

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
        #     x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
        #     gene_c_plot.text(x_coord_text, n_rows_c / 2.0, text=message_c, alpha=1,
        #                     text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

        gene_c_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(GRCh37)"
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
    subprocess.call("rm "+tmp_dir+"genes_*"+request+"*.txt", shell=True)
    subprocess.call("rm "+tmp_dir+"recomb_"+request+".txt", shell=True)
    subprocess.call("rm "+tmp_dir+"assoc_args"+request+".json", shell=True)

    print("Bokeh high quality image export complete!")

    # Return plot output
    return None


def main():

    # Import LDassoc options
    if len(sys.argv) == 8:
        filename = sys.argv[1]
        file = sys.argv[2]
        region = sys.argv[3]
        pop = sys.argv[4]
        request = sys.argv[5]
        myargsName = sys.argv[6]
        myargsOrigin = sys.argv[7]
    else:
        sys.exit()
    # Load args parameters passed from LDassoc.py
    with open(filename) as f:
        args = json.load(f)

    # Run function
    calculate_assoc_svg(file, region, pop, request, args, myargsName, myargsOrigin)


if __name__ == "__main__":
    main()