#!/usr/bin/env python

# Create LDmatrix function
def calculate_matrix(snplst,pop,request):
	import json,math,operator,os,sqlite3,subprocess,sys

	# Set data directories
	data_dir="/local/content/ldlink/data/"
	gene_dir=data_dir+"refGene/sorted_refGene.txt.gz"
	snp_dir=data_dir+"snp141/snp141.db"
	pop_dir=data_dir+"1000G/Phase3/samples/"
	vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"
	tmp_dir="./tmp/"


	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)


	# Create JSON output
	out_json=open(tmp_dir+"matrix"+request+".json","w")
	output={}


	# Open SNP list file
	snps_raw=open(snplst).readlines()
	if len(snps_raw)>300:
		output["error"]="Maximum SNP list is 300 RS numbers. Your list contains "+str(len(snps_raw))+" entries."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("","")
		raise
	
	# Remove duplicate RS numbers
	snps=[]
	for snp_raw in snps_raw:
		snp=snp_raw.strip().split()
		if snp not in snps:
			snps.append(snp)


	# Select desired ancestral populations
	pops=pop.split("+")
	pop_dirs=[]
	for pop_i in pops:
		if pop_i in ["ALL","AFR","AMR","EAS","EUR","SAS","ACB","ASW","BEB","CDX","CEU","CHB","CHS","CLM","ESN","FIN","GBR","GIH","GWD","IBS","ITU","JPT","KHV","LWK","MSL","MXL","PEL","PJL","PUR","STU","TSI","YRI"]:
			pop_dirs.append(pop_dir+pop_i+".txt")
		else:
			output["error"]=pop_i+" is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			raise
	
	get_pops="cat "+ " ".join(pop_dirs)
	proc=subprocess.Popen(get_pops, shell=True, stdout=subprocess.PIPE)
	pop_list=proc.stdout.readlines()
	
	ids=[i.strip() for i in pop_list]
	pop_ids=list(set(ids))


	# Connect to snp141 database
	conn=sqlite3.connect(snp_dir)
	conn.text_factory=str
	cur=conn.cursor()


	# Find RS numbers in snp141 database
	rs_nums=[]
	snp_pos=[]
	snp_coords=[]
	warn=[]
	tabix_coords=""
	for snp_i in snps:
		if len(snp_i)>0:
			if len(snp_i[0])>2:
				if snp_i[0][0:2]=="rs":
					id="99"+(13-len(snp_i[0]))*"0"+snp_i[0].strip("rs")
					cur.execute('SELECT * FROM snps WHERE id=?', (id,))
					snp_coord=cur.fetchone()
					if snp_coord!=None:
						rs_nums.append(snp_i[0])
						snp_pos.append(snp_coord[3])
						temp=[snp_coord[1],snp_coord[2],snp_coord[3]]
						snp_coords.append(temp)
					else:
						warn.append(snp_i[0])

	if warn!=[]:
		output["warning"]="The following RS numbers were not found in dbSNP 141: "+",".join(warn)
	
	if len(rs_nums)==0:
		output["error"]="Input SNP list does not contain any valid RS numbers that are in dbSNP 141."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("","")
		raise		


	# Check SNPs are all on the same chromosome
	for i in range(len(snp_coords)):
		if snp_coords[0][1]!=snp_coords[i][1]:
			output["error"]="Not all input SNPs are on the same chromosome."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			raise
	
	chr_lst=[str(i) for i in range(1,22+1)]
	for i in range(len(snp_coords)):
		if snp_coords[i][1] not in chr_lst:
			output["error"]="Not all input SNPs are autosomal."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			raise
	
	
	# Sort coordinates and make tabix formatted coordinates
	snp_pos_int=[int(i) for i in snp_pos]
	snp_pos_int.sort()
	snp_coord_str=[snp_coords[0][1]+":"+str(i)+"-"+str(i) for i in snp_pos_int]
	tabix_coords=" "+" ".join(snp_coord_str)
	

	# Extract 1000 Genomes phased genotypes
	vcf_file=vcf_dir+snp_coords[0][1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
	tabix_snps="tabix -fh {0}{1} | grep -v -e END".format(vcf_file, tabix_coords)
	proc=subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE)
	
	
	# Import SNP VCF files
	vcf=proc.stdout.readlines()
	h=0
	while vcf[h][0:2]=="##":
		h+=1

	head=vcf[h].strip().split()

	# Extract haplotypes
	index=[]
	for i in range(9,len(head)):
		if head[i] in pop_ids:
			index.append(i)

	hap1=[""]*len(index)
	hap2=[""]*len(index)
	rsnum_lst=[]
	allele_lst=[]
	pos_lst=[]
	for g in range(h+1,len(vcf)):
		geno=vcf[g].strip().split()
		count0=0
		count1=0
		if geno[3] in ["A","C","G","T"] and geno[4] in ["A","C","G","T"]:
			for i in range(len(index)):
				if geno[index[i]]=="0|0":
					hap1[i]=hap1[i]+geno[3]
					hap2[i]=hap2[i]+geno[3]
					count0+=2
				elif geno[index[i]]=="0|1":
					hap1[i]=hap1[i]+geno[3]
					hap2[i]=hap2[i]+geno[4]
					count0+=1
					count1+=1
				elif geno[index[i]]=="1|0":
					hap1[i]=hap1[i]+geno[4]
					hap2[i]=hap2[i]+geno[3]
					count0+=1
					count1+=1
				elif geno[index[i]]=="1|1":
					hap1[i]=hap1[i]+geno[4]
					hap2[i]=hap2[i]+geno[4]
					count1+=2
				elif geno[index[i]]=="./.":
					hap1[i]=hap1[i]+"."
					hap2[i]=hap2[i]+"."
				else:
					hap1[i]=hap1[i]+"?"
					hap2[i]=hap2[i]+"?"

			if geno[1] in snp_pos:
				rsnum=rs_nums[snp_pos.index(geno[1])]
			else:
				rsnum=str(g)+"?"
			rsnum_lst.append(rsnum)

			position="chr"+geno[0]+":"+geno[1]+"-"+geno[1]
			pos_lst.append(position)
			alleles=geno[3]+"/"+geno[4]
			allele_lst.append(alleles)

	# Calculate Pairwise LD Statistics
	all_haps=hap1+hap2
	ld_matrix=[[[None for v in range(2)] for i in range(len(all_haps[0]))] for j in range(len(all_haps[0]))]

	for i in range(len(all_haps[0])):
		for j in range(i,len(all_haps[0])):
			hap={}
			for k in range(len(all_haps)):
				# Extract haplotypes
				hap_k=all_haps[k][i]+all_haps[k][j]
				if hap_k in hap:
					hap[hap_k]+=1
				else:
					hap[hap_k]=1

			# Check all haplotypes are present
			if len(hap)!=4:
				snp_i_a=allele_lst[i].split("/")
				snp_j_a=allele_lst[j].split("/")
				haps=[snp_i_a[0]+snp_j_a[0],snp_i_a[0]+snp_j_a[1],snp_i_a[1]+snp_j_a[0],snp_i_a[1]+snp_j_a[1]]
				for h in haps:
					if h not in hap:
						hap[h]=0

			# Perform LD calculations
			A=hap[sorted(hap)[0]]
			B=hap[sorted(hap)[1]]
			C=hap[sorted(hap)[2]]
			D=hap[sorted(hap)[3]]
			delta=float(A*D-B*C)
			Ms=float((A+C)*(B+D)*(A+B)*(C+D))
			if Ms!=0:
				# D prime
				if delta<0:
					D_prime=round(delta/min((A+C)*(A+B),(B+D)*(C+D)),3)
				else:
					D_prime=round(delta/min((A+C)*(C+D),(A+B)*(B+D)),3)

				# R2
				r2=round((delta**2)/Ms,3)

				# Find Correlated Alleles
				if r2>0.1:
					N=A+B+C+D
					# Expected Cell Counts
					eA=(A+B)*(A+C)/N
					eB=(B+A)*(B+D)/N
					eC=(C+A)*(C+D)/N
					eD=(D+C)*(D+B)/N

					# Calculate Deltas
					dA=(A-eA)**2
					dB=(B-eB)**2
					dC=(C-eC)**2
					dD=(D-eD)**2
					dmax=max(dA,dB,dC,dD)

					if dmax==dA or dmax==dD:
						match=sorted(hap)[0][0]+"-"+sorted(hap)[0][1]+","+sorted(hap)[2][0]+"-"+sorted(hap)[1][1]
					else:
						match=sorted(hap)[0][0]+"-"+sorted(hap)[1][1]+","+sorted(hap)[2][0]+"-"+sorted(hap)[0][1]
				else:
					match="  -  ,  -  "
			else:
				D_prime="NA"
				r2="NA"
				match="  -  ,  -  "

			snp1=rsnum_lst[i]
			snp2=rsnum_lst[j]
			pos1=pos_lst[i].split("-")[0]
			pos2=pos_lst[j].split("-")[0]
			allele1=allele_lst[i]
			allele2=allele_lst[j]
			corr=match.split(",")[0].split("-")[1]+"-"+match.split(",")[0].split("-")[0]+","+match.split(",")[1].split("-")[1]+"-"+match.split(",")[1].split("-")[0]
			corr_f=match

			
			ld_matrix[i][j]=[snp1,snp2,allele1,allele2,corr,pos1,pos2,D_prime,r2]
			ld_matrix[j][i]=[snp2,snp1,allele2,allele1,corr_f,pos2,pos1,D_prime,r2]


	# Generate D' and R2 output matrices
	d_out=open(tmp_dir+"d_prime_"+request+".txt", "w")
	r_out=open(tmp_dir+"r2_"+request+".txt", "w")

	print >> d_out, "RS_number"+"\t"+"\t".join(rsnum_lst)
	print >> r_out, "RS_number"+"\t"+"\t".join(rsnum_lst)

	dim=len(ld_matrix)
	for i in range(dim):
		temp_d=[rsnum_lst[i]]
		temp_r=[rsnum_lst[i]]
		for j in range(dim):
			temp_d.append(str(ld_matrix[i][j][7]))
			temp_r.append(str(ld_matrix[i][j][8]))
		print >> d_out, "\t".join(temp_d)
		print >> r_out, "\t".join(temp_r)


	# Generate Plot Variables
	out=[j for i in ld_matrix for j in i]
	xnames=[]
	ynames=[]
	xA=[]
	yA=[]
	corA=[]
	xpos=[]
	ypos=[]
	D=[]
	R=[]
	box_color=[]
	box_trans=[]

	for i in range(len(out)):
		snp1,snp2,allele1,allele2,corr,pos1,pos2,D_prime,r2=out[i]
		xnames.append(snp1)
		ynames.append(snp2)
		xA.append(allele1)
		yA.append(allele2)
		corA.append(corr)
		xpos.append(pos1)
		ypos.append(pos2)
		if r2!="NA":
			D.append(str(round(float(D_prime),4)))
			R.append(str(round(float(r2),4)))
			box_color.append("red")
			box_trans.append(r2)
		else:
			D.append("NA")
			R.append("NA")
			box_color.append("blue")
			box_trans.append(0.1)
	
	# Import plotting modules
	import bokeh.embed as embed
	from bokeh.objects import HoverTool, Range1d
	from bokeh.plotting import axis,ColumnDataSource,curdoc,curplot,figure,grid,GridPlot,hold,output_file,rect,reset_output,save,segment,text,xaxis,yaxis,ygrid
	from bokeh.resources import CDN
	from collections import OrderedDict
	from math import pi
	
	reset_output()
		
	# Aggregate Plotting Data
	x=[]
	y=[]
	w=[]
	h=[]
	coord_snps_plot=[]
	snp_id_plot=[]
	alleles_snp_plot=[]
	for i in range(0,len(xpos),int(len(xpos)**0.5)):
		x.append(int(xpos[i].split(":")[1])/1000000.0)
		y.append(0.5)
		w.append(0.0001)
		h.append(1.06)
		coord_snps_plot.append(xpos[i])
		snp_id_plot.append(xnames[i])
		alleles_snp_plot.append(xA[i])
	
	
	# Generate error if less than two SNPs
	if len(x)<2:
		output["error"]="Less than two SNPs to plot."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("","")
		raise
	
	source2=ColumnDataSource(
		data=dict(
			x=x,
			y=y,
			w=w,
			h=h,
			coord_snps_plot=coord_snps_plot,
			snp_id_plot=snp_id_plot,
			alleles_snp_plot=alleles_snp_plot,
		)
	)
	
	buffer=(x[-1]-x[0])*0.025
	xr=Range1d(start=x[0]-buffer, end=x[-1]+buffer)
	yr=Range1d(start=-0.03, end=1.03)
	y2_ll=[-0.03]*len(x)
	y2_ul=[1.03]*len(x)
	
	
	yr0=Range1d(start=0, end=1)
	yr2=Range1d(start=0, end=3.8)
	yr3=Range1d(start=0, end=1)
	
	spacing=(x[-1]-x[0]+buffer+buffer)/(len(x)*1.0)
	x2=[]
	y0=[]
	y1=[]
	y2=[]
	y3=[]
	y4=[]
	for i in range(len(x)):
		x2.append(x[0]-buffer+spacing*(i+0.5))
		y0.append(0)
		y1.append(0.20)
		y2.append(0.80)
		y3.append(1)
		y4.append(1.15)
	
	xname_pos=[]
	for i in x2:
		for j in range(len(x2)):
			xname_pos.append(i)
	
	# R2 Matrix
	source = ColumnDataSource(
		data=dict(
			xname=xnames,
			xname_pos=xname_pos,
			yname=ynames,
			xA=xA,
			yA=yA,
			xpos=xpos,
			ypos=ypos,
			R2=R,
			Dp=D,
			corA=corA,
			box_color=box_color,
			box_trans=box_trans,
		)
	)
	
	threshold=70
	if len(snps)<threshold:
		figure(outline_line_color="white", min_border_top=0, min_border_bottom=2, min_border_left=100, min_border_right=5, 
	       h_symmetry=False, v_symmetry=False, border_fill='white', x_axis_type=None)
	else:
		figure(outline_line_color="white", min_border_top=0, min_border_bottom=2, min_border_left=100, min_border_right=5, 
	       h_symmetry=False, v_symmetry=False, border_fill='white', x_axis_type=None, y_axis_type=None)

	rect('xname_pos', 'yname', spacing*0.95, 0.95, source=source,
		 x_axis_location="above",
		 x_range=xr, y_range=list(reversed(rsnum_lst)),
		 color="box_color", alpha="box_trans", line_color=None,
		 tools="hover,reset,previewsave", title=" ",
		 plot_width=800, plot_height=800)

	grid().grid_line_color=None
	axis().axis_line_color=None
	axis().major_tick_line_color=None
	if len(snps)<threshold:
		axis().major_label_text_font_size="8pt"
		xaxis().major_label_orientation="vertical"

	axis().major_label_text_font_style="normal"
	xaxis().major_label_standoff=0
	
	
	sup_2=u"\u00B2"
	
	hover=curplot().select(dict(type=HoverTool))
	hover.tooltips=OrderedDict([
		("SNP 1", " "+"@yname (@yA)"),
		("SNP 2", " "+"@xname (@xA)"),
		("D\'", " "+"@Dp"),
		("R"+sup_2, " "+"@R2"),
		("Correlated Alleles", " "+"@corA"),
	])
	R2_plot=curplot()
	
	
	
	# Connecting and Rug Plots
	# Connector Plot
	if len(snps)<threshold:
		figure(outline_line_color="white", y_axis_type=None, x_axis_type=None,
			x_range=xr, y_range=yr2, border_fill='white',
			title="", min_border_left=100, min_border_right=5, min_border_top=0, min_border_bottom=0, h_symmetry=False, v_symmetry=False,
			plot_width=800, plot_height=90, tools="")
		hold()
		segment(x, y0, x, y1, color="black")
		segment(x, y1, x2, y2, color="black")
		segment(x2, y2, x2, y3, color="black")
		text(x2,y4,text=snp_id_plot,alpha=1, angle=pi/2, text_font_size="8pt",text_baseline="middle", text_align="left")
	else:
		figure(outline_line_color="white", y_axis_type=None, x_axis_type=None,
			x_range=xr, y_range=yr3, border_fill='white',
			title="", min_border_left=100, min_border_right=5, min_border_top=0, min_border_bottom=0, h_symmetry=False, v_symmetry=False,
			plot_width=800, plot_height=30, tools="")
		hold()
		segment(x, y0, x, y1, color="black")
		segment(x, y1, x2, y2, color="black")
		segment(x2, y2, x2, y3, color="black")

	
	
	yaxis().major_label_text_color=None
	yaxis().minor_tick_line_alpha=0  ## Option does not work
	yaxis().axis_label=" "
	grid().grid_line_color=None
	axis().axis_line_color=None
	axis().major_tick_line_color=None
	axis().minor_tick_line_color=None
	
	connector=curplot()
	connector.toolbar_location=None
	
	# Rug Plot
	figure(
	x_range=xr, y_range=yr, border_fill='white', y_axis_type=None,
        title="", min_border_top=0, min_border_bottom=0, min_border_left=100, min_border_right=5, h_symmetry=False, v_symmetry=False,
        plot_width=800, plot_height=50, tools="hover,pan")
	hold()
	rect(x, y, w, h, source=source2, fill_color="red", dilate=True, line_color=None, fill_alpha=0.6)
	yaxis().axis_line_color="black"
	yaxis().major_tick_line_color=None
	yaxis().major_label_text_color=None
	yaxis().minor_tick_line_alpha=0  ## Option does not work
	yaxis().axis_label="SNPs"
	ygrid().axis_line_color="white"
	
	hover=curplot().select(dict(type=HoverTool))
	hover.tooltips=OrderedDict([
		("SNP", "@snp_id_plot (@alleles_snp_plot)"),
		("Coord", "@coord_snps_plot"),
	])
	
	rug=curplot()
	rug.toolbar_location=None
	
	
		
	# Gene Plot
	tabix_gene="tabix -fh {0} {1}:{2}-{3} > {4}".format(gene_dir, snp_coord[2], (x[0]-buffer)*1000000, (x[0]+buffer)*1000000, tmp_dir+"genes_"+request+".txt")
	subprocess.call(tabix_gene, shell=True)
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
			genes_plot_name.append(name)
			
			for i in range(len(e_start)-1):
				if strand=="+":
					exon=i+1
				else:
					exon=len(e_start)-1-i
				
				width=(int(e_end[i])-int(e_start[i]))/1000000.0
				x_coord=(int(e_start[i])+(width/2))/1000000.0
				
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
	
	source2=ColumnDataSource(
		data=dict(
			exons_plot_name=exons_plot_name,
			exons_plot_id=exons_plot_id,
			exons_plot_exon=exons_plot_exon,
		)
	)
	
	if len(lines)<3:
	    plot_h_pix=150
	else:
	    plot_h_pix=150+(len(lines)-2)*50
	
	figure(min_border_top=0, min_border_bottom=0, min_border_left=100, min_border_right=5,
        x_range=xr, y_range=yr2, border_fill='white', y_axis_type=None,
        title="", h_symmetry=False, v_symmetry=False,
        plot_width=800, plot_height=plot_h_pix, tools="hover,pan,box_zoom,wheel_zoom,reset,previewsave")
	hold()
	segment(genes_plot_start, genes_plot_yn, genes_plot_end, genes_plot_yn, color="black", alpha=1, line_width=2)
	rect(exons_plot_x, exons_plot_yn, exons_plot_w, exons_plot_h, source=source2, fill_color="grey", line_color="grey")
	xaxis().axis_label="Chromosome "+snp_coord[2]+" Coordinate (Mb)"
	yaxis().axis_label="Genes"
	yaxis().major_tick_line_color=None
	yaxis().major_label_text_color=None
	
	hover=curplot().select(dict(type=HoverTool))
	hover.tooltips=OrderedDict([
		("Gene", "@exons_plot_name"),
		("ID", "@exons_plot_id"),
		("Exon", "@exons_plot_exon"),
	])
	
	genes_plot_start_n=[x-0.001000 for x in genes_plot_start]
	text(genes_plot_start_n, genes_plot_yn, text=genes_plot_name, alpha=1, text_font_size="7pt",
		 text_font_style="bold", text_baseline="middle", text_align="right", angle=0)
	
	gene_plot=curplot()
	gene_plot.toolbar_location="below"
	
	
	
	#output_file("LDmatrix.html")
	out_plots=[[R2_plot],[connector],[rug],[gene_plot]]
	GridPlot(children=out_plots)
	#save()
	
	out_script,out_div=embed.components(curdoc(), CDN)
	reset_output()
	
	
	
	# Return output
	json_output=json.dumps(output, sort_keys=True, indent=2)
	print >> out_json, json_output
	out_json.close()
	return(out_script,out_div)


def main():
	import json,sys
	tmp_dir="./tmp/"

	# Import LDmatrix options
	if len(sys.argv)==4:
		snplst=sys.argv[1]
		pop=sys.argv[2]
		request=sys.argv[3]
	else:
		print "Correct useage is: LDmatrix.py snplst populations request"
		sys.exit()


	# Run function
	out_script,out_div=calculate_matrix(snplst,pop,request)


	# Print output
	with open(tmp_dir+"matrix"+request+".json") as f:
		json_dict=json.load(f)

	try:
		json_dict["error"]

	except KeyError:
		print "\nOutput saved as: d_prime_"+request+".txt and r2_"+request+".txt"

		try:
			json_dict["warning"]

		except KeyError:
			print ""
		else:
			print ""
			print "WARNING: "+json_dict["warning"]+"!"
			print ""

	else:
		print ""
		print json_dict["error"]
		print ""

if __name__ == "__main__":
	main()
