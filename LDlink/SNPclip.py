#!/usr/bin/env python

###########
# SNPclip #  LDthin a list of prioritized SNPs
###########

# To Do:
# Add functionality for indels
# Add functionality for sex chromosomes
# Add functionality for combining multiple input chromosomes
# Add sorting priority (ie: Regulome DB, exonic)

# Create SNPtip function
def calculate_clip(snplst,pop,request):
	import json,math,operator,os,sqlite3,subprocess,sys
	maf_threshold=0.05
	r2_threshold=0.1

	# Set data directories
	data_dir="/local/content/ldlink/data/"
	gene_dir=data_dir+"refGene/sorted_refGene.txt.gz"
	snp_dir=data_dir+"snp142/snp142_annot_2.db"
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
	max_list=5000
	if len(snps_raw)>max_list:
		output["error"]="Maximum SNP list is "+str(max_list)+" RS numbers. Your list contains "+str(len(snps_raw))+" entries."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("")
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


	# Connect to snp142 database
	conn=sqlite3.connect(snp_dir)
	conn.text_factory=str
	cur=conn.cursor()
	
	def get_coords(rs):
		id=rs.strip("rs")
		t=(id,)
		cur.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
		return cur.fetchone()


	# Find RS numbers in snp142 database
	details={}
	rs_nums=[]
	snp_pos=[]
	snp_coords=[]
	warn=[]
	tabix_coords=""
	for snp_i in snps:
		if len(snp_i)>0:
			if len(snp_i[0])>2:
				if snp_i[0][0:2]=="rs":
					snp_coord=get_coords(snp_i[0])
					if snp_coord!=None:
						rs_nums.append(snp_i[0])
						snp_pos.append(snp_coord[2])
						temp=[snp_i[0],snp_coord[1],snp_coord[2]]
						snp_coords.append(temp)
					else:
						warn.append(snp_i[0])
						details[snp_i[0]]="SNP not found in dbSNP142, SNP removed."
				else:
					warn.append(snp_i[0])
					details[snp_i[0]]="Not an RS number, query removed."
			else:
				warn.append(snp_i[0])
				details[snp_i[0]]="Not an RS number, query removed."
		else:
			warn.append(snp_i[0])
			details[snp_i[0]]="Not an RS number, query removed."

	if warn!=[]:
		output["warning"]="The following RS numbers were not found in dbSNP 142: "+",".join(warn)
			
	
	if len(rs_nums)==0:
		output["error"]="Input SNP list does not contain any valid RS numbers that are in dbSNP 142."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("")
		raise		
	
	# Check SNPs are all on the same chromosome
	for i in range(len(snp_coords)):
		if snp_coords[0][1]!=snp_coords[i][1]:
			output["error"]="Not all input SNPs are on the same chromosome: "+snp_coords[i-1][0]+"=chr"+str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0]+"=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+"."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","")
			raise		
	
	# Make tabix formatted coordinates
	snp_coord_str=[snp_coords[0][1]+":"+i+"-"+i for i in snp_pos]
	tabix_coords=" "+" ".join(snp_coord_str)
	

	# Extract 1000 Genomes phased genotypes
	vcf_file=vcf_dir+snp_coords[0][1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
	tabix_snps="tabix -fh {0}{1} | grep -v -e END".format(vcf_file, tabix_coords)
	proc=subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE)
	
	
	# Make MAF function
	def calc_maf(genos):
		vals={"0|0":0, "0|1":0, "1|0":0, "1|1":0}
		for i in range(len(genos)):
			if genos[i] in vals:
				vals[genos[i]]+=1
		
		zeros=vals["0|0"]*2+vals["0|1"]+vals["1|0"]
		ones =vals["1|1"]*2+vals["0|1"]+vals["1|0"]
		total=zeros+ones
		
		if zeros<ones:
			maf=zeros*1.0/total
		else:
			maf=ones*1.0/total
		
		return maf
	
	
	# Make R2 function
	def calc_r2(var1,var2):
		hap_vals={"0|0-0|0":0, "0|0-0|1":0, "0|0-1|0":0, "0|0-1|1":0, "0|1-0|0":0, "0|1-0|1":0, "0|1-1|0":0, "0|1-1|1":0, "1|0-0|0":0, "1|0-0|1":0, "1|0-1|0":0, "1|0-1|1":0, "1|1-0|0":0, "1|1-0|1":0, "1|1-1|0":0, "1|1-1|1":0, "0-0":0, "0-1":0, "1-0":0, "1-1":0}
		for i in range(len(var1)):
			ind_geno=var1[i]+"-"+var2[i]
			if ind_geno in hap_vals:
				hap_vals[ind_geno]+=1
		
		A=hap_vals["0|0-0|0"]*2+hap_vals["0|0-0|1"]+hap_vals["0|0-1|0"]+hap_vals["0|1-0|0"]+hap_vals["0|1-0|1"]+hap_vals["1|0-0|0"]+hap_vals["1|0-1|0"]+hap_vals["0-0"]
		B=hap_vals["0|0-0|1"]+hap_vals["0|0-1|0"]+hap_vals["0|0-1|1"]*2+hap_vals["0|1-1|0"]+hap_vals["0|1-1|1"]+hap_vals["1|0-0|1"]+hap_vals["1|0-1|1"]+hap_vals["0-1"]
		C=hap_vals["0|1-0|0"]+hap_vals["0|1-1|0"]+hap_vals["1|0-0|0"]+hap_vals["1|0-0|1"]+hap_vals["1|1-0|0"]*2+hap_vals["1|1-0|1"]+hap_vals["1|1-1|0"]+hap_vals["1-0"]
		D=hap_vals["0|1-0|1"]+hap_vals["0|1-1|1"]+hap_vals["1|0-1|0"]+hap_vals["1|0-1|1"]+hap_vals["1|1-0|1"]+hap_vals["1|1-1|0"]+hap_vals["1|1-1|1"]*2+hap_vals["1-1"]
		
		delta=float(A*D-B*C)
		Ms=float((A+C)*(B+D)*(A+B)*(C+D))
		if Ms!=0:
			r2=(delta**2)/Ms
		else:
			r2=None
		
		return(r2)
	
			
	# Import SNP VCF file
	hap_dict={}
	vcf=proc.stdout.readlines()
	h=0
	while vcf[h][0:2]=="##":
		h+=1

	head=vcf[h].strip().split()	
	
	# Extract population specific haplotypes
	pop_index=[]
	for i in range(9,len(head)):
		if head[i] in pop_ids:
			pop_index.append(i)
	
	snp_list=[]
	
	for g in range(h+1,len(vcf)):
		geno=vcf[g].strip().split()
		if geno[1] in snp_pos:
			rsnum=rs_nums[snp_pos.index(geno[1])]
			if geno[3] in ["A","C","G","T"] and geno[4] in ["A","C","G","T"]:
				temp_genos=[]
				for i in range(len(pop_index)):
					temp_genos.append(geno[pop_index[i]])
				r2=calc_maf(temp_genos)
				if maf_threshold<=r2:
					hap_dict[rsnum]=[temp_genos]
					snp_list.append(rsnum)
				else:
					details[rsnum]="SNP MAF is "+str(r2)+", SNP removed"
			else:
				details[rsnum]="SNP has alleles "+geno[3]+" and "+geno[4]+", SNP removed"
	
	for i in rs_nums:
		if i not in snp_list:
			if i not in details:
				details[i]="SNP not in 1000G VCF file, SNP removed"
	
	# Thin the SNPs
	i=0
	while i<len(snp_list):
		#if snp_list[i] in hap_dict:
			details[snp_list[i]]="SNP kept"
			remove_list=[]
			for j in range(i+1,len(snp_list)):
				r2=calc_r2(hap_dict[snp_list[i]][0],hap_dict[snp_list[j]][0])
				if r2_threshold<=r2:
					snp=snp_list[j]
					details[snp]="SNP in LD with "+snp_list[i]+" (R2="+str(r2)+"), SNP removed"
					remove_list.append(snp)
			for snp in remove_list:
				snp_list.remove(snp)
			i+=1
		#else:
		#	details[snp_list[i]]="SNP not in 1000G VCF file, SNP removed"
		#	snp_list.remove(snp_list[i])
	
	
	
	# Return output
	json_output=json.dumps(output, sort_keys=True, indent=2)
	print >> out_json, json_output
	out_json.close()
	return(snps,snp_list,details)


def main():
	import json,sys
	tmp_dir="./tmp/"

	# Import SNPclip options
	if len(sys.argv)==4:
		snplst=sys.argv[1]
		pop=sys.argv[2]
		request=sys.argv[3]
	else:
		print "Correct useage is: SNPclip.py snplst populations request"
		sys.exit()


	# Run function
	snps,snp_list,details=calculate_clip(snplst,pop,request)


	# Print output
	with open(tmp_dir+"matrix"+request+".json") as f:
		json_dict=json.load(f)

	try:
		json_dict["error"]

	except KeyError:
		print ""
		print "LD Thinned SNP list ("+pop+"):"
		for snp in snp_list:
			print snp
		
		print ""
		print "Details:"
		for snp in snps:
			print snp[0]+"\t"+details[snp[0]]

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
	
	
	

