#!/usr/bin/env python3
import yaml
import csv
import json
import operator
import os
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import time
import boto3
import botocore
from multiprocessing.dummy import Pool
import numpy as np
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars, getRefGene, getRecomb,connectMongoDBReadOnly
from LDcommon import validsnp,get_coords,get_coords_gene, get_population,get_query_variant_c,get_output,get_1000g_data_single
from LDutilites import get_config

# Create LDproxy function
def calculate_assoc(file, region, pop, request, genome_build, web, myargs):
	start_time=time.time()

	# Set data directories using config.yml
	param_list = get_config()
	dbsnp_version = param_list['dbsnp_version']
	data_dir = param_list['data_dir']
	tmp_dir = param_list['tmp_dir']
	population_samples_dir = param_list['population_samples_dir']
	genotypes_dir = param_list['genotypes_dir']
	aws_info = param_list['aws_info']
	num_subprocesses = param_list['num_subprocesses']

	export_s3_keys = retrieveAWSCredentials()

	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)

	# Create JSON output
	out_json = open(tmp_dir+'assoc'+request+".json","w")
	output = {}

    # Validate genome build param
	validsnp(None,genome_build,None)

	chrs=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y"]

	# Define parameters for --variant option
	if region=="variant":
		if myargs.origin==None:
			output["error"]="--origin required when --variant is specified."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")

	if myargs.origin!=None:
		# Find coordinates (GRCh37/hg19) or (GRCh38/hg38) for SNP RS number
		if myargs.origin[0:2]=="rs":
			snp=myargs.origin

			# Connect to Mongo snp database
			db = connectMongoDBReadOnly(web)

			var_coord = get_coords(db, snp)

			if var_coord==None:
				output["error"] = snp + " is not in dbSNP " + dbsnp_version + " (" + genome_build_vars[genome_build]['title'] + ")."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print(json_output, file=out_json)
				out_json.close()
				return("","")

			# check if variant is on chrY for genome build = GRCh38
			if var_coord['chromosome'] == "Y" and (genome_build == "grch38" or genome_build == "grch38_high_coverage"):
				output["error"] = "Input variants on chromosome Y are unavailable for GRCh38, only available for GRCh37 (" + "rs" + var_coord['id'] + " = chr" + var_coord['chromosome'] + ":" + var_coord[genome_build_vars[genome_build]['position']] + ")"
				json_output = json.dumps(output, sort_keys=True, indent=2)
				print(json_output, file=out_json)
				out_json.close()
				return("", "")

		elif myargs.origin.split(":")[0].strip("chr") in chrs and len(myargs.origin.split(":"))==2:
			snp=myargs.origin
			#var_coord=[None,myargs.origin.split(":")[0].strip("chr"),myargs.origin.split(":")[1]]
			var_coord = {'chromosome':myargs.origin.split(":")[0].strip("chr"), 'position':myargs.origin.split(":")[1]}

		else:
			output["error"]="--origin ("+myargs.origin+") is not a RS number (ex: rs12345) or chromosomal position (ex: chr22:25855459)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")

		chromosome = var_coord['chromosome']
		org_coord = var_coord[genome_build_vars[genome_build]['position']]

	# Open Association Data
	header_list=[]
	header_list.append(myargs.chr)
	header_list.append(myargs.bp)
	header_list.append(myargs.pval)

	# print "[ldassoc debug] load input file"

	# Load input file
	with open(file) as fp:
		header = fp.readline().strip().split()
		first = fp.readline().strip().split()
	print("HEADER: " + str(header))
	print("FIRST: " + str(first))

	if len(header)!=len(first):
		output["error"]="Header has "+str(len(header))+" elements and first line has "+str(len(first))+" elements."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print(json_output)
		print(json_output, file=out_json)
		out_json.close()
		return("","")

	# print "[ldassoc debug] check header"

	# Check header
	for item in header_list:
		if item not in header:
			output["error"]="Variables mapping is not listed in the in the association file header."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
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
		# print "[ldassoc debug] choose variant"
		coord1=int(org_coord)-window
		if coord1<0:
			coord1=0
		coord2=int(org_coord)+window

	elif region=="gene":
		# print "[ldassoc debug] choose gene"
		if myargs.name==None:
			output["error"]="Gene name (--name) is needed when --gene option is used."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")

		# Connect to Mongo snp database
		db = connectMongoDBReadOnly(web)
		

		# Find RS number in snp database
		gene_coord = get_coords_gene(myargs.name, db,genome_build)

		if gene_coord == None or gene_coord[2] == 'NA' or gene_coord == 'NA':
			output["error"]="Gene name " + myargs.name + " is not in RefSeq database."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
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
				output["error"]="Origin variant "+myargs.origin+" is not on the same chromosome as "+myargs.name+" (chr"+chromosome+" is not equal to chr"+gene_coord[1]+")."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print(json_output, file=out_json)
				out_json.close()
				return("","")

			if coord1>int(org_coord) or int(org_coord)>coord2:
				output["error"]="Origin variant "+myargs.origin+" (chr"+chromosome+":"+org_coord+") is not in the coordinate range chr"+gene_coord[1]+":"+str(coord1)+"-"+str(coord2)+"."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print(json_output, file=out_json)
				out_json.close()
				return("","")
				
		else:
			chromosome=gene_coord[1]

	elif region=="region":
		# print "[ldassoc debug] choose region"
		if myargs.start==None:
			output["error"]="Start coordinate is needed when --region option is used."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
		
		if myargs.end==None:
			output["error"]="End coordinate is needed when --region option is used."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")

		# Parse out chr and positions for --region option
		if len(myargs.start.split(":"))!=2:
			output["error"]="Start coordinate is not in correct format (ex: chr22:25855459)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
			
		if len(myargs.end.split(":"))!=2:
			output["error"]="End coordinate is not in correct format (ex: chr22:25855459)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
		
		chr_s = myargs.start.strip("chr").split(":")[0]
		chr_s = chr_s.upper() if chr_s == 'x' or chr_s == 'y' else chr_s
		coord_s = myargs.start.split(":")[1]
		chr_e = myargs.end.strip("chr").split(":")[0]
		chr_e = chr_e.upper() if chr_e == 'x' or chr_e == 'y' else chr_e
		coord_e = myargs.end.split(":")[1]

		if chr_s not in chrs:
			output["error"]="Start chromosome (chr"+chr_s+") is not an autosome (chr1-chr22) or sex chromosome (chrX or chrY)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
			
		if chr_e not in chrs:
			output["error"]="End chromosome (chr"+chr_e+") is not an autosome (chr1-chr22) or sex chromosome (chrX or chrY)."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
			
		if chr_s != chr_e:
			output["error"]="Start and end chromosome must be the same (chr"+chr_s+" is not equal to chr"+chr_e+")."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
			
		if coord_s >= coord_e:
			output["error"]="End coordinate ("+myargs.end+") must be greater than start coordinate("+myargs.start+")."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
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
				print(json_output, file=out_json)
				out_json.close()
				return("","")
				
			if coord1>int(org_coord) or int(org_coord)>coord2:
				output["error"]="Origin variant "+myargs.origin+" is not in the coordinate range "+myargs.start+" to "+myargs.end+" -/+ a "+str(window)+" bp window."
				json_output=json.dumps(output, sort_keys=True, indent=2)
				print(json_output, file=out_json)
				out_json.close()
				return("","")
				
		else:
			chromosome=chr_s

	# Generate coordinate list and P-value dictionary
	max_window=3000000
	if coord2-coord1>max_window:
			output["error"]="Queried regioin is "+str(coord2-coord1)+" base pairs. Max size is "+str(max_window)+" base pairs."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")
			

	assoc_coords=[]
	a_pos=[]
	assoc_dict={}
	assoc_list=[]
	# print "[ldassoc debug] iterate through uploaded file"
	print ("file: ", file)#
	#print("chromosome: ", chromosome)
	with open(file) as fp:
		for line_num, line in enumerate(fp, 1):
			col = line.strip().split()
			
			if len(col)==len_head:
				if col[chr_index].strip("chr")==chromosome:
					try:
						int(col[pos_index])
					except ValueError:
						continue
					else:
						#print("coord1: ", coord1)
						#print("coord2: ", coord2)
						#for x in range(len(col)):
							#print (col[x], ",")
						#print(col[pos_index])
						#print("middle: ", col[pos_index])
						if coord1<=int(col[pos_index])<=coord2:
							try:
								float(col[p_index])
							except ValueError:
								continue
							else:
								coord_i = genome_build_vars[genome_build]['1000G_chr_prefix'] + col[chr_index].strip("chr")+":"+col[pos_index]+"-"+col[pos_index]
								assoc_coords.append(coord_i)
								a_pos.append(col[pos_index])
								assoc_dict[coord_i]=[col[p_index]]
								assoc_list.append([coord_i,float(col[p_index])])

			else:
				output["warning"]="Line " + str(line_num) + " of association data file has a different number of elements than the header"

	# Coordinate list checks
	if len(assoc_coords)==0:
		output["error"]="There are no variants in the association file with genomic coordinates inside the plotting window."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print(json_output, file=out_json)
		out_json.close()
		return("","")

	# Select desired ancestral populations
	pop_ids = get_population(pop,request,output)
	if isinstance(pop_ids,str):
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print(json_output, file=out_json)
		out_json.close()
		return("","")
	# Define LD origin coordinate
	try:
		org_coord
	except NameError:
		counterMissing = 0
		for var_p in sorted(assoc_list, key=operator.itemgetter(1)):
			snp=var_p[0].split("-")[0]
			# Extract lowest P SNP phased genotypes
			vcf_filePath = "%s/%s%s/%s" % (aws_info['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]["1000G_dir"], genome_build_vars[genome_build]["1000G_file"] % (chromosome))
			vcf_file = "s3://%s/%s" % (aws_info['bucket'], vcf_filePath)
			checkS3File(aws_info, aws_info['bucket'], vcf_filePath)
			#tabix_snp_h= export_s3_keys + " cd {1}; tabix -HD {0} | grep CHROM".format(vcf_file, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
			#head = [x.decode('utf-8') for x in subprocess.Popen(tabix_snp_h, shell=True, stdout=subprocess.PIPE).stdout.readlines()][0].strip().split()
			tabix_snp= export_s3_keys + " cd {3}; tabix -hD {0} {1} | grep -v -e END > {2}".format(vcf_file, genome_build_vars[genome_build]['1000G_chr_prefix'] + var_p[0], tmp_dir+"snp_no_dups_"+request+".vcf", data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
			subprocess.call(tabix_snp, shell=True)
			#print(snp,var_p)
			# Check lowest P SNP is in the 1000G population and not monoallelic
			vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()
			h = 0
			while vcf[h][0:2] == "##":
				h += 1
			head = vcf[h].strip().split()
			vcf = vcf[h+1:]
			#print("vcf length:",len(vcf))
			if len(vcf)==0:
				counterMissing = counterMissing +1
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
				geno = vcf[0].strip().split()
				geno[0] = geno[0].lstrip('chr')

			else:
				geno = vcf[0].strip().split()
				geno[0] = geno[0].lstrip('chr')

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
		#print(counterMissing,len(assoc_list))
		if counterMissing == len(assoc_list):
			output["error"]="Association file Lowest P-value variant ("+snp+") is not in 1000G reference panel"
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")

	else:
		if genome_build_vars[genome_build]['1000G_chr_prefix'] + chromosome + ":" + org_coord + "-" + org_coord not in assoc_coords:
			output["error"]="Association file is missing a p-value for origin variant "+snp+"."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print(json_output, file=out_json)
			out_json.close()
			return("","")

		# Extract query SNP phased genotypes
		temp = [snp, str(chromosome), org_coord]
		#print(temp)
		(geno,tmp_dist, warningmsg) = get_query_variant_c(temp, pop_ids, str(request), genome_build, True,output)



	# print "[ldassoc debug] begin calculating LD in parallel"
	# Calculate proxy LD statistics in parallel
	print("")
	if len(assoc_coords) < 60:
		num_subprocesses = 1
	# else:
	# 	threads=4

	# print("######assoc_coords######")
	# print("assoc_coords length:", len(assoc_coords))
	# # print("\n".join(assoc_coords))
	# print("####################")

	# block=len(assoc_coords) // num_subprocesses
	assoc_coords_subset_chunks = np.array_split(assoc_coords, num_subprocesses)
	# print(assoc_coords_subset_chunks)

	commands=[]
	print("Create LDassoc_sub subprocesses")

	for subprocess_id in range(num_subprocesses):
		subprocessArgs = " ".join([str(snp), str(chromosome), str("_".join(assoc_coords_subset_chunks[subprocess_id])), str(request), str(genome_build), str(subprocess_id)])
		#print(subprocessArgs)
		commands.append("python3 LDassoc_sub.py " + subprocessArgs)
	
	processes=[subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in commands]

	# print "[ldassoc debug] collect output in parallel" 

	pool = Pool(len(processes))
	out_raw=pool.map(get_output, processes)
	pool.close()
	pool.join()

	print("LDassoc_sub subprocessed completed.")

	# print "[ldassoc debug] aggregate output"

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
			coord_i_j=genome_build_vars[genome_build]['1000G_chr_prefix'] + chromosome + ":" + pos_i_j + "-" + pos_i_j
			if coord_i_j in assoc_dict:
				col.append(float(assoc_dict[coord_i_j][0]))
				out_prox.append(col)

	out_dist_sort=sorted(out_prox, key=operator.itemgetter(15))
	out_p_sort=sorted(out_dist_sort, key=operator.itemgetter(16), reverse=False)


	# Populate JSON and text output
	from math import log10

	outfile=open(tmp_dir+"assoc"+request+".txt","w")
	header=["RS_Number","Coord","Alleles","MAF","Distance","Dprime","R2","Correlated_Alleles","P-value","FORGEdb","RegulomeDB","Function"]
	print("\t".join(header), file=outfile)

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
	query_snp["FORGEdb"] = out_p_sort[0][10]
	query_snp["RegulomeDB"]=out_p_sort[0][11]
	query_snp["MAF"]=str(round(float(out_p_sort[0][12]),4))
	query_snp["Function"]=out_p_sort[0][14]
	query_snp["P-value"]=out_p_sort[0][16]

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
	row.append(query_snp["FORGEdb"])
	row.append(query_snp["RegulomeDB"])
	row.append("HaploReg link")
	row.append(query_snp["Function"])
	rows.append(row)

	temp=[query_snp["RS"],query_snp["Coord"],query_snp["Alleles"],query_snp["MAF"],str(query_snp["Dist"]),str(query_snp["Dprime"]),str(query_snp["R2"]),query_snp["Corr_Alleles"],str(query_snp["P-value"]),query_snp["FORGEdb"],query_snp["RegulomeDB"],query_snp["Function"]]
	print("\t".join(temp), file=outfile)

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
			proxy_info["FORGEdb"]=out_p_sort[i][10]
			proxy_info["RegulomeDB"]=out_p_sort[i][11]
			proxy_info["MAF"]=str(round(float(out_p_sort[i][13]),4))
			proxy_info["Function"]=out_p_sort[i][14]
			proxy_info["P-value"]=out_p_sort[i][16]
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
			row.append(proxy_info["FORGEdb"])
			row.append(proxy_info["RegulomeDB"])
			row.append("HaploReg link")
			row.append(proxy_info["Function"])
			rows.append(row)

			temp=[proxy_info["RS"],proxy_info["Coord"],proxy_info["Alleles"],proxy_info["MAF"],str(proxy_info["Dist"]),str(proxy_info["Dprime"]),str(proxy_info["R2"]),proxy_info["Corr_Alleles"],str(proxy_info["P-value"]),proxy_info["FORGEdb"],proxy_info["RegulomeDB"],proxy_info["Function"]]
			print("\t".join(temp), file=outfile)

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
	print("browser position chr"+str(chromosome)+":"+str(coord1)+"-"+str(coord2), file=track)
	print("", file=track)

	print("track type=bedGraph name=\"Manhattan Plot\" description=\"Plot of -log10 association p-values\" color=50,50,50 visibility=full alwaysZero=on graphType=bar yLineMark=7.301029995663981 yLineOnOff=on maxHeightPixels=60", file=track)
	print("\t".join([str(ucsc_track["lowest_p"][i]) for i in [0,1,1,3]]), file=track)
	if len(ucsc_track["gwas_sig"])>0:
		for var in ucsc_track["gwas_sig"]:
			print("\t".join([str(var[i]) for i in [0,1,1,3]]), file=track)
	if len(ucsc_track["marg_sig"])>0:
		for var in ucsc_track["marg_sig"]:
			print("\t".join([str(var[i]) for i in [0,1,1,3]]), file=track)
	if len(ucsc_track["sugg_sig"])>0:
		for var in ucsc_track["sugg_sig"]:
			print("\t".join([str(var[i]) for i in [0,1,1,3]]), file=track)
	if len(ucsc_track["not_sig"])>0:
		for var in ucsc_track["not_sig"]:
			print("\t".join([str(var[i]) for i in [0,1,1,3]]), file=track)
	print("", file=track)

	print("track type=bed name=\""+snp+"\" description=\"Variant with lowest association p-value: "+snp+"\" color=108,108,255", file=track)
	print("\t".join([ucsc_track["lowest_p"][i] for i in [0,1,1,2]]), file=track)
	print("", file=track)

	if len(ucsc_track["gwas_sig"])>0:
		print("track type=bed name=\"P<5e-8\" description=\"Variants with association p-values <5e-8\" color=198,129,0", file=track)
		for var in ucsc_track["gwas_sig"]:
			print("\t".join([var[i] for i in [0,1,1,2]]), file=track)
		print("", file=track)

	if len(ucsc_track["marg_sig"])>0:
		print("track type=bed name=\"5e-8<=P<1e-5\" description=\"Variants with association p-values >=5e-8 and <1e-5\" color=198,129,0", file=track)
		for var in ucsc_track["marg_sig"]:
			print("\t".join([var[i] for i in [0,1,1,2]]), file=track)
		print("", file=track)

	if len(ucsc_track["sugg_sig"])>0:
		print("track type=bed name=\"1e-5<=P<1e-3\" description=\"Variants with association p-values >=1e-5 and <1e-3\" color=198,129,0", file=track)
		for var in ucsc_track["sugg_sig"]:
			print("\t".join([var[i] for i in [0,1,1,2]]), file=track)
		print("", file=track)

	if len(ucsc_track["not_sig"])>0:
		print("track type=bed name=\"1e-3<=P<=1\" description=\"Variants with association p-values >=1e-3 and <=1\" color=198,129,0", file=track)
		for var in ucsc_track["not_sig"]:
			print("\t".join([var[i] for i in [0,1,1,2]]), file=track)


	duration=time.time() - start_time

	statsistics={}
	statsistics["individuals"] = str(len(pop_ids))
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
	print(json_output, file=out_json)
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

	# print "[ldassoc debug] begin Bokeh plotting"

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

	data = {'x': x, 'y': y, 'qrs': q_rs, 'q_alle': q_allele, 'q_maf': q_maf, 'prs': p_rs, 'p_alle': p_allele, 'p_maf': p_maf, 'dist': dist, 'r': r2_round, 'd': d_prime_round, 'alleles': corr_alleles, 'forgedb':forgedb,'regdb': regdb, 'funct': funct, 'p_val': p_val, 'size': size, 'color': color, 'alpha': alpha}
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

	# Add recombination rate
	recomb_file = tmp_dir + "recomb_" + request + ".json"
	db = connectMongoDBReadOnly(True)
	recomb_json = getRecomb(db, recomb_file, chromosome, coord1 - whitespace, coord2 + whitespace, genome_build)

	recomb_x=[]
	recomb_y=[]

	for recomb_obj in recomb_json:
		recomb_x.append(int(recomb_obj[genome_build_vars[genome_build]['position']]) / 1000000.0)
		recomb_y.append(float(recomb_obj['rate']) / 100 * max(y))

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
		("FORGEdb Score", "@forgedb"),
		("RegulomeDB Rank", "@regdb"),
		("Functional Class", "@funct"),
	])

	assoc_plot.add_tools(hover)

	# Annotate RebulomeDB scores
	if myargs.annotate=="forge":
		assoc_plot.text(x, y, text=forgedb, alpha=1, text_font_size="7pt", text_baseline="middle", text_align="center", angle=0)
	elif myargs.annotate=="regulome":
		assoc_plot.text(x, y, text=regdb, alpha=1, text_font_size="7pt", text_baseline="middle", text_align="center", angle=0)

	assoc_plot.yaxis.axis_label="-log10 P-value"

	assoc_plot.extra_y_ranges = {"y2_axis": Range1d(start=-3, end=103)}
	assoc_plot.add_layout(LinearAxis(y_range_name="y2_axis", axis_label="Combined Recombination Rate (cM/Mb)"), "right")  ## Need to confirm units


	# Rug Plot
	y2_ll=[-0.03]*len(x)
	y2_ul=[1.03]*len(x)
	yr_rug=Range1d(start=-0.03, end=1.03)

	data_rug = {'x': x, 'y': y, 'y2_ll': y2_ll, 'y2_ul': y2_ul,'qrs': q_rs, 'q_alle': q_allele, 'q_maf': q_maf, 'prs': p_rs, 'p_alle': p_allele, 'p_maf': p_maf, 'dist': dist, 'r': r2_round, 'd': d_prime_round, 'alleles': corr_alleles, 'forgedb':forgedb,'regdb': regdb, 'funct': funct, 'p_val': p_val, 'size': size, 'color': color, 'alpha': alpha}
	source_rug = ColumnDataSource(data_rug)

	rug=figure(
			x_range=xr, y_range=yr_rug, border_fill_color='white', y_axis_type=None,
			title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, h_symmetry=False, v_symmetry=False,
			plot_width=900, plot_height=50, tools="xpan,tap,wheel_zoom", logo=None)

	rug.segment(x0='x', y0='y2_ll', x1='x', y1='y2_ul', source=source_rug, color='color', alpha='alpha', line_width=1)
	rug.toolbar_location=None

	if myargs.transcript==True:
		# Gene Plot (All Transcripts)
		genes_file = tmp_dir + "genes_" + request + ".json"
		genes_json = getRefGene(db, genes_file, chromosome, coord1, coord2, genome_build, False)

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
		# 	x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
		# 	gene_plot.text(x_coord_text, n_rows / 2.0, text=message, alpha=1,
		# 				   text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

		gene_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
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
		

		# # Generate high quality images only if accessed via web instance
		# if web:
		# 	# Open thread for high quality image exports
		# 	print("Open thread for high quality image exports.")
		# 	command = "python3 LDassoc_plot_sub.py " + tmp_dir + 'assoc_args' + request + ".json" + " " + file + " " + region + " " + pop + " " + request + " " + genome_build + " " + myargsName + " " + myargsOrigin
		# 	subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)



	# Gene Plot (Collapsed)
	else:
		genes_c_file = tmp_dir + "genes_c_" + request + ".json"
		genes_c_json = getRefGene(db, genes_c_file, chromosome, coord1, coord2, genome_build, True)

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

		gene_c_plot.xaxis.axis_label = "Chromosome " + chromosome + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
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
		print("Open thread for high quality image exports.")
		command = "python3 LDassoc_plot_sub.py " + tmp_dir + 'assoc_args' + request + ".json" + " " + file + " " + region + " " + pop + " " + request + " " + genome_build + " " + myargsName + " " + myargsOrigin
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
	print("Number of Individuals: "+str(len(pop_ids)))
	print("SNPs in Region: "+str(len(out_prox)))
	duration=round(time.time() - start_time,2)
	print("Run time: "+str(duration)+" seconds\n")


	# Remove temporary files in LDassoc_plot_sub.py

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

	genome_build = "grch37"

	# Run function
	out_script,out_div=calculate_assoc(args.file, region, args.pop, args.request, genome_build, web, args)


	# Print output
	with open(tmp_dir+"assoc"+args.request+".json") as f:
		json_dict=json.load(f)

		try:
			json_dict["error"]

		except KeyError:
			head=["RS_Number","Coord","Alleles","MAF","Distance","Dprime","R2","Correlated_Alleles","Association P-value","FORGEdb","RegulomeDB","Functional_Class"]
			print("\t".join(head))
			temp=[json_dict["query_snp"]["RS"],json_dict["query_snp"]["Coord"],json_dict["query_snp"]["Alleles"],json_dict["query_snp"]["MAF"],str(json_dict["query_snp"]["Dist"]),str(json_dict["query_snp"]["Dprime"]),str(json_dict["query_snp"]["R2"]),json_dict["query_snp"]["Corr_Alleles"],str(json_dict["query_snp"]["P-value"]),json_dict["query_snp"]["FORGEdb"],json_dict["query_snp"]["RegulomeDB"],json_dict["query_snp"]["Function"]]
			print("\t".join(temp))
			for k in sorted(json_dict["proxy_snps"].keys())[0:10]:
				temp=[json_dict["proxy_snps"][k]["RS"],json_dict["proxy_snps"][k]["Coord"],json_dict["proxy_snps"][k]["Alleles"],json_dict["proxy_snps"][k]["MAF"],str(json_dict["proxy_snps"][k]["Dist"]),str(json_dict["proxy_snps"][k]["Dprime"]),str(json_dict["proxy_snps"][k]["R2"]),json_dict["proxy_snps"][k]["Corr_Alleles"],str(json_dict["proxy_snps"][k]["P-value"]),json_dict["proxy_snps"][k]["FORGEdb"],json_dict["proxy_snps"][k]["RegulomeDB"],json_dict["proxy_snps"][k]["Function"]]
				print("\t".join(temp))

		else:
			print("")
			print(json_dict["error"])
			print("")

		try:
			json_dict["warning"]
		except KeyError:
			print("")
		else:
			print("WARNING: "+json_dict["warning"]+"!")
			print("")


if __name__ == "__main__":
	main()
