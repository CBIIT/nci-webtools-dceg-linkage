import yaml
#!/usr/bin/env python

# Create LDproxy function
def calculate_assoc(file, region, pop, request, web, myargs):
	import csv,json,operator,os,sqlite3,subprocess,time
	from multiprocessing.dummy import Pool
	start_time=time.time()

	# Set data directories using config.yml
	with open('config.yml', 'r') as f:
		config = yaml.load(f)
	gene_dir=config['data']['gene_dir']
	gene_c_dir=config['data']['gene_c_dir']
	gene_dir2=config['data']['gene_dir2']
	recomb_dir=config['data']['recomb_dir']
	snp_dir=config['data']['snp_dir']
	pop_dir=config['data']['pop_dir']
	vcf_dir=config['data']['vcf_dir']

	tmp_dir="./tmp/"


	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)


	# Create JSON output
	out_json=open(tmp_dir+'assoc'+request+".json","w")
	output={}

	chrs=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y"]

	# Define parameters for --variant option
	if region=="variant":
		if myargs.origin==None:
			output["error"]="--origin required when --variant is specified."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

	if myargs.origin!=None:
		# Find coordinates (GRCh37/hg19) for SNP RS number
		if myargs.origin[0:2]=="rs":
			snp=myargs.origin

			# Connect to snp database
			conn=sqlite3.connect(snp_dir)
			conn.text_factory=str
			cur=conn.cursor()

			def get_coords(rs):
				id=rs.strip("rs")
				t=(id,)
				cur.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
				return cur.fetchone()

			# Find RS number in snp database
			var_coord=get_coords(snp)

			# Close snp connection
			cur.close()
			conn.close()

			if var_coord==None:
				output["error"]=snp+" is not in dbSNP build " + config['data']['dbsnp_version'] + "."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print >> out_json, json_output
				out_json.close()
				return("","")

		elif myargs.origin.split(":")[0].strip("chr") in chrs and len(myargs.origin.split(":"))==2:
			snp=myargs.origin
			var_coord=[None,myargs.origin.split(":")[0].strip("chr"),myargs.origin.split(":")[1]]

		else:
			output["error"]="--origin ("+myargs.origin+") is not an RS number (ex: rs12345) or chromosomal position (ex: chr22:25855459)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

		chromosome=var_coord[1]
		org_coord=str(int(var_coord[2]) + 1) # new dbSNP151 position is 1 off


	# Open Association Data
	header_list=[]
	header_list.append(myargs.chr)
	header_list.append(myargs.bp)
	header_list.append(myargs.pval)

	# Load input file
	assoc_data=open(file).readlines()
	header=assoc_data[0].strip().split()
	first=assoc_data[1].strip().split()
	if len(header)!=len(first):
		output["error"]="Header has "+str(len(header))+" elements and first line has "+str(len(first))+" elements."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print json_output
		print >> out_json, json_output
		out_json.close()
		return("","")

	# Check header
	for item in header_list:
		if item not in header:
			output["error"]="Variables mapping is not listed in the in the association file header."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

	len_head=len(header)

	chr_index=header.index(myargs.chr)
	pos_index=header.index(myargs.bp)
	p_index=header.index(myargs.pval)


	# Define window of interest around query SNP
	if myargs.window==None:
		if region=="variant":
			window=500000
		elif region=="gene":
			window=100000
		else:
			window=0
	else:
		window=myargs.window

	if region=="variant":
		coord1=int(org_coord)-window
		if coord1<0:
			coord1=0
		coord2=int(org_coord)+window

	elif region=="gene":
		if myargs.name==None:
			output["error"]="Gene name (--name) is needed when --gene option is used."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

		# Connect to gene database
		conn=sqlite3.connect(gene_dir2)
		conn.text_factory=str
		cur=conn.cursor()

		def get_coords(gene_raw):
			gene=gene_raw.upper()
			t=(gene,)
			cur.execute("SELECT * FROM genes WHERE name=?", t)
			return cur.fetchone()

		# Find RS number in snp database
		gene_coord=get_coords(myargs.name)

		# Close snp connection
		cur.close()
		conn.close()

		if gene_coord==None:
			output["error"]="Gene name "+myargs.name+" is not in RefSeq database."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

		# Define search coordinates
		coord1=int(gene_coord[2])-window
		if coord1<0:
			coord1=0
		coord2=int(gene_coord[3])+window

		# Run with --origin option
		if myargs.origin!=None:
			if gene_coord[1]!=chromosome:
				output["error"]="Origin variant "+myargs.origin+" is not on the same chromosome as "+myargs.gene+" (chr"+chromosome+" is not equal to chr"+gene_coord[1]+")."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print >> out_json, json_output
				out_json.close()
				return("","")

			if coord1>int(org_coord) or int(org_coord)>coord2:
				output["error"]="Origin variant "+myargs.origin+" (chr"+chromosome+":"+org_coord+") is not in the coordinate range chr"+gene_coord[1]+":"+str(coord1)+"-"+str(coord2)+"."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print >> out_json, json_output
				out_json.close()
				return("","")
				
		else:
			chromosome=gene_coord[1]

	elif region=="region":
		if myargs.start==None:
			output["error"]="Start coordinate is needed when --region option is used."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
		
		if myargs.end==None:
			output["error"]="End coordinate is needed when --region option is used."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

		# Parse out chr and positions for --region option
		if len(myargs.start.split(":"))!=2:
			output["error"]="Start coordinate is not in correct format (ex: chr22:25855459)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			
		if len(myargs.end.split(":"))!=2:
			output["error"]="End coordinate is not in correct format (ex: chr22:25855459)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

		chr_s=myargs.start.strip("chr").split(":")[0]
		coord_s=myargs.start.split(":")[1]
		chr_e=myargs.end.strip("chr").split(":")[0]
		coord_e=myargs.end.split(":")[1]

		if chr_s not in chrs:
			output["error"]="Start chromosome (chr"+chr_s+") is not an autosome (chr1-chr22) or sex chromosome (chrX or chrY)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			
		if chr_e not in chrs:
			output["error"]="End chromosome (chr"+chr_e+") is not an autosome (chr1-chr22) or sex chromosome (chrX or chr Y)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			
		if chr_s!=chr_e:
			output["error"]="Start and end chromosome must be the same (chr"+chr_s+" is not equal to chr"+chr_e+")."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			
		if coord_s>=coord_e:
			output["error"]="End coordinate ("+myargs.end+") must be greater than start coordinate("+myargs.start+")."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			

		coord1=int(coord_s)-window
		if coord1<0:
			coord1=0
		coord2=int(coord_e)+window

		# Run with --origin option
		if myargs.origin!=None:
			if chr_s!=chromosome:
				output["error"]="Origin variant "+myargs.origin+" is not on the same chromosome as start and stop coordinates (chr"+chromosome+" is not equal to chr"+chr_e+")."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print >> out_json, json_output
				out_json.close()
				return("","")
				
			if coord1>int(org_coord) or int(org_coord)>coord2:
				output["error"]="Origin variant "+myargs.origin+" is not in the coordinate range "+myargs.start+" to "+myargs.end+" -/+ a "+str(window)+" bp window."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print >> out_json, json_output
				out_json.close()
				return("","")
				
		else:
			chromosome=chr_s

	# Generate coordinate list and P-value dictionary
	max_window=3000000
	if coord2-coord1>max_window:
			output["error"]="Queried regioin is "+str(coord2-coord1)+" base pairs. Max size is "+str(max_window)+" base pairs."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			

	assoc_coords=[]
	a_pos=[]
	assoc_dict={}
	assoc_list=[]
	for i in range(len(assoc_data)):
		col=assoc_data[i].strip().split()
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

		else:
			output["warning"]="Line "+str(i+1)+" of association data file has a different number of elements than the header"

	# Coordinate list checks
	if len(assoc_coords)==0:
		output["error"]="There are no variants in the association file with genomic coordinates inside the plotting window."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("","")

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

	get_pops="cat "+" ".join(pop_dirs)+" > "+tmp_dir+"pops_"+request+".txt"
	subprocess.call(get_pops, shell=True)


	# Get population ids
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
			head=proc_h.stdout.readlines()[0].strip().split()

			tabix_snp="tabix {0} {1} | grep -v -e END > {2}".format(vcf_file, var_p[0], tmp_dir+"snp_no_dups_"+request+".vcf")
			subprocess.call(tabix_snp, shell=True)


			# Check lowest P SNP is in the 1000G population and not monoallelic
			vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()

			if len(vcf)==0:
				if "warning" in output:
					output["warning"]=output["warning"]+". Lowest P-value variant ("+snp+") is not in 1000G reference panel, using next lowest P-value variant"
				else:
					output["warning"]="Lowest P-value variant ("+snp+") is not in 1000G reference panel, using next lowest P-value variant"
				continue
			elif len(vcf)>1:
				if "warning" in output:
					output["warning"]=output["warning"]+". Multiple variants map to lowest P-value variant ("+snp+"), using first variant in VCF file"
				else:
					output["warning"]="Multiple variants map to lowest P-value variant ("+snp+"), using first variant in VCF file"
				geno=vcf[0].strip().split()

			else:
				geno=vcf[0].strip().split()

			if "," in geno[3] or "," in geno[4]:
				if "warning" in output:
					output["warning"]=output["warning"]+". Lowest P-value variant ("+snp+") is not a biallelic variant, using next lowest P-value variant"
				else:
					output["warning"]="Lowest P-value variant ("+snp+" is not a biallelic variant, using next lowest P-value variant"
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
				output["error"]=snp+" is monoallelic in the "+pop+" population."
				if "warning" in output:
					output["warning"]=output["warning"]+". Lowest P-value variant ("+snp+") is monoallelic in the "+pop+" population, using next lowest P-value variant"
				else:
					output["warning"]="Lowest P-value variant ("+snp+") is monoallelic in the "+pop+" population, using next lowest P-value variant"
				continue

			org_coord=var_p[0].split("-")[1]
			break


	else:
		if chromosome+":"+org_coord+"-"+org_coord not in assoc_coords:
			print "##########"
			print "FAIL HERE"
			print chromosome+":"+org_coord+"-"+org_coord
			print assoc_coords
			output["error"]="Association file is missing a p-value for origin variant "+snp+"."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")

		# Extract query SNP phased genotypes
		vcf_file=vcf_dir+chromosome+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"

		tabix_snp_h="tabix -H {0} | grep CHROM".format(vcf_file)
		proc_h=subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE)
		head=proc_h.stdout.readlines()[0].strip().split()

		tabix_snp="tabix {0} {1}:{2}-{2} | grep -v -e END > {3}".format(vcf_file, chromosome, org_coord, tmp_dir+"snp_no_dups_"+request+".vcf")
		subprocess.call(tabix_snp, shell=True)


		# Check query SNP is in the 1000G population, has the correct RS number, and not monoallelic
		vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()

		if len(vcf)==0:
			output["error"]=snp+" is not in 1000G reference panel."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
			subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
			return("","")
			
		elif len(vcf)>1:
			geno=[]
			for i in range(len(vcf)):
				if vcf[i].strip().split()[2]==snp:
					geno=vcf[i].strip().split()
			if geno==[]:
				output["error"]=snp+" is not in 1000G reference panel."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print >> out_json, json_output
				out_json.close()
				subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
				subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
				return("","")
				
		else:
			geno=vcf[0].strip().split()

		if geno[2]!=snp and snp[0:2]=="rs":
			if "warning" in output:
				output["warning"]=output["warning"]+". Genomic position for query variant ("+snp+") does not match RS number at 1000G position (chr"+geno[0]+":"+geno[1]+")"
			else:
				output["warning"]="Genomic position for query variant ("+snp+") does not match RS number at 1000G position (chr"+geno[0]+":"+geno[1]+")"
			snp=geno[2]

		if "," in geno[3] or "," in geno[4]:
			output["error"]=snp+" is not a biallelic variant."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
			subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
			return("","")


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
			output["error"]=snp+" is monoallelic in the "+pop+" population."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
			subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
			return("","")


	# Calculate proxy LD statistics in parallel
	print ""
	if len(assoc_coords)<60:
		threads=1
	else:
		threads=4

	block=len(assoc_coords)/threads
	commands=[]
	for i in range(threads):
		if i==min(range(threads)) and i==max(range(threads)):
			command="python LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords)+" "+request+" "+str(i)
		elif i==min(range(threads)):
			command="python LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[:block])+" "+request+" "+str(i)
		elif i==max(range(threads)):
			command="python LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[(block*i)+1:])+" "+request+" "+str(i)
		else:
			command="python LDassoc_sub.py "+snp+" "+chromosome+" "+"_".join(assoc_coords[(block*i)+1:block*(i+1)])+" "+request+" "+str(i)
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
			col=out_raw[i][j].strip().split("\t")
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


	# Populate JSON and text output
	from math import log10

	outfile=open(tmp_dir+"assoc"+request+".txt","w")
	header=["RS_Number","Coord","Alleles","MAF","Distance","Dprime","R2","Correlated_Alleles","P-value","RegulomeDB","Function"]
	print >> outfile, "\t".join(header)

	ucsc_track={}
	ucsc_track["header"]=["chr","pos","rsid","-log10_p-value"]

	query_snp={}
	query_snp["RS"]=out_p_sort[0][3]
	query_snp["Alleles"]=out_p_sort[0][1]
	query_snp["Coord"]=out_p_sort[0][2]
	query_snp["Dist"]=out_p_sort[0][6]
	query_snp["Dprime"]=str(round(float(out_p_sort[0][7]),4))
	query_snp["R2"]=str(round(float(out_p_sort[0][8]),4))
	query_snp["Corr_Alleles"]=out_p_sort[0][9]
	query_snp["RegulomeDB"]=out_p_sort[0][10]
	query_snp["MAF"]=str(round(float(out_p_sort[0][11]),4))
	query_snp["Function"]=out_p_sort[0][13]
	query_snp["P-value"]=out_p_sort[0][15]

	output["query_snp"]=query_snp

	rows=[]
	row=[]
	row.append(query_snp["RS"])
	chr,pos=query_snp["Coord"].split(':')
	row.append(chr)
	row.append(pos)
	row.append(query_snp["Alleles"])
	row.append(str(round(float(query_snp["MAF"]),4)))
	row.append(abs(query_snp["Dist"]))
	row.append(str(round(float(query_snp["Dprime"]),4)))
	row.append(str(round(float(query_snp["R2"]),4)))
	row.append(query_snp["Corr_Alleles"])
	row.append(query_snp["P-value"])
	row.append(query_snp["RegulomeDB"])
	row.append("HaploReg link")
	row.append(query_snp["Function"])
	rows.append(row)

	temp=[query_snp["RS"],query_snp["Coord"],query_snp["Alleles"],query_snp["MAF"],str(query_snp["Dist"]),str(query_snp["Dprime"]),str(query_snp["R2"]),query_snp["Corr_Alleles"],str(query_snp["P-value"]),query_snp["RegulomeDB"],query_snp["Function"]]
	print >> outfile, "\t".join(temp)

	temp2=[chr,pos,query_snp["RS"],-log10(query_snp["P-value"])]
	ucsc_track["lowest_p"]=temp2

	ucsc_track["gwas_sig"]=[]
	ucsc_track["marg_sig"]=[]
	ucsc_track["sugg_sig"]=[]
	ucsc_track["not_sig"]=[]

	proxies={}
	digits=len(str(len(out_p_sort)))

	for i in range(1,len(out_p_sort)):
		if out_p_sort[i][3]!=snp:
			proxy_info={}
			row=[]
			proxy_info["RS"]=out_p_sort[i][3]
			proxy_info["Alleles"]=out_p_sort[i][4]
			proxy_info["Coord"]=out_p_sort[i][5]
			proxy_info["Dist"]=out_p_sort[i][6]
			proxy_info["Dprime"]=str(round(float(out_p_sort[i][7]),4))
			proxy_info["R2"]=str(round(float(out_p_sort[i][8]),4))
			proxy_info["Corr_Alleles"]=out_p_sort[i][9]
			proxy_info["RegulomeDB"]=out_p_sort[i][10]
			proxy_info["MAF"]=str(round(float(out_p_sort[i][12]),4))
			proxy_info["Function"]=out_p_sort[i][13]
			proxy_info["P-value"]=out_p_sort[i][15]
			proxies["proxy_"+(digits-len(str(i)))*"0"+str(i)]=proxy_info
			chr,pos=proxy_info["Coord"].split(':')

			# Adding a row for the Data Table
			row.append(proxy_info["RS"])
			row.append(chr)
			row.append(pos)
			row.append(proxy_info["Alleles"])
			row.append(str(round(float(proxy_info["MAF"]),4)))
			row.append(abs(proxy_info["Dist"]))
			row.append(str(round(float(proxy_info["Dprime"]),4)))
			row.append(str(round(float(proxy_info["R2"]),4)))
			row.append(proxy_info["Corr_Alleles"])
			row.append(proxy_info["P-value"])
			row.append(proxy_info["RegulomeDB"])
			row.append("HaploReg link")
			row.append(proxy_info["Function"])
			rows.append(row)

			temp=[proxy_info["RS"],proxy_info["Coord"],proxy_info["Alleles"],proxy_info["MAF"],str(proxy_info["Dist"]),str(proxy_info["Dprime"]),str(proxy_info["R2"]),proxy_info["Corr_Alleles"],str(proxy_info["P-value"]),proxy_info["RegulomeDB"],proxy_info["Function"]]
			print >> outfile, "\t".join(temp)

			chr,pos=proxy_info["Coord"].split(':')
			p_val=-log10(proxy_info["P-value"])
			temp2=[chr,pos,proxy_info["RS"],p_val]

			if p_val>-log10(5e-8):
				ucsc_track["gwas_sig"].append(temp2)
			elif -log10(5e-8)>=p_val>5:
				ucsc_track["marg_sig"].append(temp2)
			elif 5>=p_val>3:
				ucsc_track["sugg_sig"].append(temp2)
			else:
				ucsc_track["not_sig"].append(temp2)

	track=open(tmp_dir+"track"+request+".txt","w")
	print >> track, "browser position chr"+str(chromosome)+":"+str(coord1)+"-"+str(coord2)
	print >> track, ""

	print >> track, "track type=bedGraph name=\"Manhattan Plot\" description=\"Plot of -log10 association p-values\" color=50,50,50 visibility=full alwaysZero=on graphType=bar yLineMark=7.301029995663981 yLineOnOff=on maxHeightPixels=60"
	print >> track, "\t".join([str(ucsc_track["lowest_p"][i]) for i in [0,1,1,3]])
	if len(ucsc_track["gwas_sig"])>0:
		for var in ucsc_track["gwas_sig"]:
			print >> track, "\t".join([str(var[i]) for i in [0,1,1,3]])
	if len(ucsc_track["marg_sig"])>0:
		for var in ucsc_track["marg_sig"]:
			print >> track, "\t".join([str(var[i]) for i in [0,1,1,3]])
	if len(ucsc_track["sugg_sig"])>0:
		for var in ucsc_track["sugg_sig"]:
			print >> track, "\t".join([str(var[i]) for i in [0,1,1,3]])
	if len(ucsc_track["not_sig"])>0:
		for var in ucsc_track["not_sig"]:
			print >> track, "\t".join([str(var[i]) for i in [0,1,1,3]])
	print >> track, ""

	print >> track, "track type=bed name=\""+snp+"\" description=\"Variant with lowest association p-value: "+snp+"\" color=108,108,255"
	print >> track, "\t".join([ucsc_track["lowest_p"][i] for i in [0,1,1,2]])
	print >> track, ""

	if len(ucsc_track["gwas_sig"])>0:
		print >> track, "track type=bed name=\"P<5e-8\" description=\"Variants with association p-values <5e-8\" color=198,129,0"
		for var in ucsc_track["gwas_sig"]:
			print >> track, "\t".join([var[i] for i in [0,1,1,2]])
		print >> track, ""

	if len(ucsc_track["marg_sig"])>0:
		print >> track, "track type=bed name=\"5e-8<=P<1e-5\" description=\"Variants with association p-values >=5e-8 and <1e-5\" color=198,129,0"
		for var in ucsc_track["marg_sig"]:
			print >> track, "\t".join([var[i] for i in [0,1,1,2]])
		print >> track, ""

	if len(ucsc_track["sugg_sig"])>0:
		print >> track, "track type=bed name=\"1e-5<=P<1e-3\" description=\"Variants with association p-values >=1e-5 and <1e-3\" color=198,129,0"
		for var in ucsc_track["sugg_sig"]:
			print >> track, "\t".join([var[i] for i in [0,1,1,2]])
		print >> track, ""

	if len(ucsc_track["not_sig"])>0:
		print >> track, "track type=bed name=\"1e-3<=P<=1\" description=\"Variants with association p-values >=1e-3 and <=1\" color=198,129,0"
		for var in ucsc_track["not_sig"]:
			print >> track, "\t".join([var[i] for i in [0,1,1,2]])


	duration=time.time() - start_time

	statsistics={}
	statsistics["individuals"] = str(len(pop_list))
	statsistics["in_region"] = str(len(out_prox))
	statsistics["runtime"] = str(duration)

	output["aaData"]=rows
	output["proxy_snps"]=proxies
	output["report"]={}
	output["report"]["namespace"]={}
	output["report"]["namespace"].update(vars(myargs))
	output["report"]["region"] = region
	output["report"]["statistics"] = statsistics

	# Output JSON and text file
	json_output=json.dumps(output, sort_keys=False, indent=2)
	print >> out_json, json_output
	out_json.close()

	outfile.close()
	track.close()



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
			if myargs.dprime==True:
				color_i=reds[int(d_prime_i*100.0)]
				alpha_i=0.7
			elif myargs.dprime==False:
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
	sup_2=u"\u00B2"

	assoc_plot=figure(
				title="P-values and Regional LD for "+snp+" in "+pop,
				min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
				plot_width=900,
				plot_height=600,
				x_range=xr, y_range=yr,
				tools="tap,pan,box_zoom,wheel_zoom,box_select,undo,redo,reset,previewsave", logo=None,
				toolbar_location="above")

	assoc_plot.title.align="center"

	# Add recombination rate
	tabix_recomb="tabix -fh {0} {1}:{2}-{3} > {4}".format(recomb_dir, chromosome, coord1-whitespace, coord2+whitespace, tmp_dir+"recomb_"+request+".txt")
	subprocess.call(tabix_recomb, shell=True)
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
	if myargs.annotate==True:
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
	if myargs.transcript==True:
		tabix_gene="tabix -fh {0} {1}:{2}-{3} > {4}".format(gene_dir, chromosome, coord1, coord2, tmp_dir+"genes_"+request+".txt")
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
		if len(lines) < 3 or len(genes_raw) > max_genes:
			plot_h_pix = 150
		else:
			plot_h_pix = 150 + (len(lines) - 2) * 50

		gene_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
						   x_range=xr, y_range=yr2, border_fill_color='white',
						   title="", h_symmetry=False, v_symmetry=False, logo=None,
						   plot_width=900, plot_height=plot_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,previewsave")

		if len(genes_raw) <= max_genes:
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

		else:
			x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
			gene_plot.text(x_coord_text, n_rows / 2.0, text=message, alpha=1,
						   text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

		gene_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(GRCh37)"
		gene_plot.yaxis.axis_label = "Genes (All Transcripts)"
		gene_plot.ygrid.grid_line_color = None
		gene_plot.yaxis.axis_line_color = None
		gene_plot.yaxis.minor_tick_line_color = None
		gene_plot.yaxis.major_tick_line_color = None
		gene_plot.yaxis.major_label_text_color = None

		gene_plot.toolbar_location = "below"

		out_grid = gridplot(assoc_plot, rug, gene_plot,
			ncols=1, toolbar_options=dict(logo=None))

		with open(tmp_dir + 'assoc_args' + request + ".json", "w") as out_args:
			json.dump(vars(myargs), out_args)
		out_args.close()

		myargsName = "None"
		try:
			if myargs.name==None:
				myargsName = "None"
			else:
				myargsName = myargs.name
		except:
			pass
		

		myargsOrigin = "None"
		try:
			if myargs.origin==None:
				myargsOrigin = "None"
			else:
				myargsOrigin = myargs.origin
		except:
			pass
		

		# Generate high quality images only if accessed via web instance
		if web:
			# Open thread for high quality image exports
			command = "python LDassoc_plot_sub.py " + tmp_dir + 'assoc_args' + request + ".json" + " " + file + " " + region + " " + pop + " " + request + " " + myargsName + " " + myargsOrigin
			subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)



	# Gene Plot (Collapsed)
	else:
		tabix_gene_c="tabix -fh {0} {1}:{2}-{3} > {4}".format(gene_c_dir, chromosome, coord1, coord2, tmp_dir+"genes_c_"+request+".txt")
		subprocess.call(tabix_gene_c, shell=True)
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
		if len(lines_c) < 3 or len(genes_c_raw) > max_genes_c:
			plot_c_h_pix = 150
		else:
			plot_c_h_pix = 150 + (len(lines_c) - 2) * 50

		gene_c_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
						   x_range=xr, y_range=yr2_c, border_fill_color='white',
						   title="", h_symmetry=False, v_symmetry=False, logo=None,
						   plot_width=900, plot_height=plot_c_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,previewsave")

		if len(genes_c_raw) <= max_genes_c:
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

		else:
			x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
			gene_c_plot.text(x_coord_text, n_rows_c / 2.0, text=message_c, alpha=1,
						   text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

		gene_c_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(GRCh37)"
		gene_c_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
		gene_c_plot.ygrid.grid_line_color = None
		gene_c_plot.yaxis.axis_line_color = None
		gene_c_plot.yaxis.minor_tick_line_color = None
		gene_c_plot.yaxis.major_tick_line_color = None
		gene_c_plot.yaxis.major_label_text_color = None

		gene_c_plot.toolbar_location = "below"
		
		out_grid = gridplot(assoc_plot, rug, gene_c_plot,
					ncols=1, toolbar_options=dict(logo=None))


		with open(tmp_dir + 'assoc_args' + request + ".json", "w") as out_args:
			json.dump(vars(myargs), out_args)
		out_args.close()

		myargsName = "None"
		try:
			if myargs.name==None:
				myargsName = "None"
			else:
				myargsName = myargs.name
		except:
			pass

		myargsOrigin = "None"
		try:
			if myargs.origin==None:
				myargsOrigin = "None"
			else:
				myargsOrigin = myargs.origin
		except:
			pass

		# Generate high quality images only if accessed via web instance
		if web:
			# Open thread for high quality image exports
			command = "python LDassoc_plot_sub.py " + tmp_dir + 'assoc_args' + request + ".json" + " " + file + " " + region + " " + pop + " " + request + " " + myargsName + " " + myargsOrigin
			subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

	###########################
	# Html output for testing #
	###########################
	#html=file_html(out_grid, CDN, "Test Plot")
	#out_html=open("LDassoc.html","w")
	#print >> out_html, html
	#out_html.close()


	out_script,out_div=components(out_grid, CDN)
	reset_output()



	# Print run time statistics
	print "Number of Individuals: "+str(len(pop_list))
	print "SNPs in Region: "+str(len(out_prox))
	duration=round(time.time() - start_time,2)
	print "Run time: "+str(duration)+" seconds\n"


	# Remove temporary files
	subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
	subprocess.call("rm "+tmp_dir+"*"+request+"*.vcf", shell=True)
	subprocess.call("rm "+tmp_dir+"genes_*"+request+".txt", shell=True)
	subprocess.call("rm "+tmp_dir+"recomb_"+request+".txt", shell=True)


	# Return plot output
	return(out_script,out_div)


def main():
	import argparse,json
	tmp_dir="./tmp/"

	# Import LDassoc options
	parser=argparse.ArgumentParser()
	parser.add_argument("file", type=str, help="association file containing p-values")
	region=parser.add_mutually_exclusive_group(required=True)
	region.add_argument("-g", "--gene", help="run LDassoc in gene mode (--name required)", action="store_true")
	region.add_argument("-r", "--region", help="run LDassoc in region mode (--start and --stop required)", action="store_true")
	region.add_argument("-v", "--variant", help="run LDassoc in variant mode (--origin required)", action="store_true")
	parser.add_argument("pop", type=str, help="1000G population to use for LD calculations")
	parser.add_argument("request", type=str, help="id for submitted command")
	parser.add_argument("-a", "--annotate", help="annotate plot with RegulomeDB scores", action="store_true")
	parser.add_argument("-b", "--bp", type=str, help="header name for base pair coordinate (default is \"BP\")", default="BP")
	parser.add_argument("-c", "--chr", type=str, help="header name for chromosome (default is \"CHR\")", default="CHR")
	parser.add_argument("-d", "--dprime", help="plot D prime rather than R2", action="store_true")
	parser.add_argument("-e", "--end", type=str, help="ending coordinate (ex: chr22:25855459), chr must be same as in --start (required with --region)")
	parser.add_argument("-i", "--id", type=str, help="header name for variant RS number (default is \"SNP\")", default="SNP")
	parser.add_argument("-n", "--name", type=str, help="gene name (required with --gene)")
	parser.add_argument("-o", "--origin", type=str, help="reference variant RS number (required with --variant)(default is lowest p-value in region)")
	parser.add_argument("-p", "--pval", type=str, help="header name for p-value (default is \"P\")", default="P")
	parser.add_argument("-s", "--start", type=str, help="starting coordinate (ex: chr22:25855459), chr must be same as in --end (required with --region)")
	parser.add_argument("-t", "--transcript", help="plot all gene transcripts", action="store_true")
	parser.add_argument("-w", "--window", type=int, help="flanking region (+/- bp) around gene, region, or variant of interest (default is 500 for --gene and --variant and 0 for --region)")

	args=parser.parse_args()

	# with open(tmp_dir + 'assoc_args' + args.request + ".json", "w") as out_args:
	# 	json.dump(vars(args), out_args)
	# out_args.close()

	if args.gene:
		region="gene"
	elif args.region:
		region="region"
	elif args.variant:
		region="variant"

	# initialize web instance as True if run via main
	web = True

	# Run function
	out_script,out_div=calculate_assoc(args.file, region, args.pop, args.request, web, args)


	# Print output
	with open(tmp_dir+"assoc"+args.request+".json") as f:
		json_dict=json.load(f)

		try:
			json_dict["error"]

		except KeyError:
			head=["RS_Number","Coord","Alleles","MAF","Distance","Dprime","R2","Correlated_Alleles","Association P-value","RegulomeDB","Functional_Class"]
			print "\t".join(head)
			temp=[json_dict["query_snp"]["RS"],json_dict["query_snp"]["Coord"],json_dict["query_snp"]["Alleles"],json_dict["query_snp"]["MAF"],str(json_dict["query_snp"]["Dist"]),str(json_dict["query_snp"]["Dprime"]),str(json_dict["query_snp"]["R2"]),json_dict["query_snp"]["Corr_Alleles"],str(json_dict["query_snp"]["P-value"]),json_dict["query_snp"]["RegulomeDB"],json_dict["query_snp"]["Function"]]
			print "\t".join(temp)
			for k in sorted(json_dict["proxy_snps"].keys())[0:10]:
				temp=[json_dict["proxy_snps"][k]["RS"],json_dict["proxy_snps"][k]["Coord"],json_dict["proxy_snps"][k]["Alleles"],json_dict["proxy_snps"][k]["MAF"],str(json_dict["proxy_snps"][k]["Dist"]),str(json_dict["proxy_snps"][k]["Dprime"]),str(json_dict["proxy_snps"][k]["R2"]),json_dict["proxy_snps"][k]["Corr_Alleles"],str(json_dict["proxy_snps"][k]["P-value"]),json_dict["proxy_snps"][k]["RegulomeDB"],json_dict["proxy_snps"][k]["Function"]]
				print "\t".join(temp)

		else:
			print ""
			print json_dict["error"]
			print ""

		try:
			json_dict["warning"]
		except KeyError:
			print ""
		else:
			print "WARNING: "+json_dict["warning"]+"!"
			print ""


if __name__ == "__main__":
	main()
