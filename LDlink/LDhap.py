#!/usr/bin/env python

# Create LDhap function
def calculate_hap(snplst,pop,request):
	import json,math,operator,os,sqlite3,subprocess,sys
	
	# Set data directories
	data_dir="/local/content/ldlink/data/"
	snp_dir=data_dir+"snp142/snp142_annot_2.db"
	pop_dir=data_dir+"1000G/Phase3/samples/"
	vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"
	tmp_dir="./tmp/"
	
	
	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)
	
	
	# Create JSON output
	output={}
	
	
	# Open SNP list file
	snps_raw=open(snplst).readlines()
	if len(snps_raw)>30:
		output["error"]="Maximum SNP list is 30 RS numbers. Your list contains "+str(len(snps_raw))+" entries."
		return(json.dumps(output, sort_keys=True, indent=2))
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
			return(json.dumps(output, sort_keys=True, indent=2))
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
	
	if warn!=[]:
		output["warning"]="The following RS numbers were not found in dbSNP 141: "+",".join(warn)
	
	if len(rs_nums)==0:
		output["error"]="Input SNP list does not contain any valid RS numbers that are in dbSNP 141."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise
	
	
	# Check SNPs are all on the same chromosome
	for i in range(len(snp_coords)):
		if snp_coords[0][1]!=snp_coords[i][1]:
			output["error"]="Not all input SNPs are on the same chromosome: "+snp_coords[i-1][0]+"=chr"+str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0]+"=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+"."
			return(json.dumps(output, sort_keys=True, indent=2))
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
				elif geno[index[i]]=="0":
					hap1[i]=hap1[i]+geno[3]
					hap2[i]=hap2[i]+"."
					count0+=1
				elif geno[index[i]]=="1":
					hap1[i]=hap1[i]+geno[4]
					hap2[i]=hap2[i]+"."
					count1+=1
				else:
					hap1[i]=hap1[i]+"."
					hap2[i]=hap2[i]+"."
			
			if geno[1] in snp_pos:
				rsnum=rs_nums[snp_pos.index(geno[1])]
			else:
				rsnum=str(g)+"?"
			rsnum_lst.append(rsnum)
			
			position="chr"+geno[0]+":"+geno[1]
			pos_lst.append(position)
			
			f0=round(float(count0)/(count0+count1),4)
			f1=round(float(count1)/(count0+count1),4)
			if f0>=f1:
				alleles=geno[3]+"="+str(round(f0,3))+", "+geno[4]+"="+str(round(f1,3))
			else:
				alleles=geno[4]+"="+str(round(f1,3))+", "+geno[3]+"="+str(round(f0,3))
			allele_lst.append(alleles)
	
	
	haps={}
	for i in range(len(index)):
		if hap1[i] in haps:
			haps[hap1[i]]+=1
		else:
			haps[hap1[i]]=1
		
		if hap2[i] in haps:
			haps[hap2[i]]+=1
		else:
			haps[hap2[i]]=1
	
	
	# Remove Missing Haplotypes
	keys=haps.keys()
	for key in keys:
		if "." in key:
			haps.pop(key, None)
	
	
	# Sort results
	results=[]
	for hap in haps:
		temp=[hap,haps[hap]]
		results.append(temp)
	
	total_haps=sum(haps.values())
	
	results_sort1=sorted(results, key=operator.itemgetter(0))
	results_sort2=sorted(results_sort1, key=operator.itemgetter(1), reverse=True)
	
	
	# Generate JSON output
	digits=len(str(len(results_sort2)))
	haps_out={}
	for i in range(len(results_sort2)):
		hap_info={}
		hap_info["Haplotype"]=results_sort2[i][0]
		hap_info["Count"]=results_sort2[i][1]
		hap_info["Frequency"]=round(float(results_sort2[i][1])/total_haps,4)
		haps_out["haplotype_"+(digits-len(str(i+1)))*"0"+str(i+1)]=hap_info
	output["haplotypes"]=haps_out
	
	digits=len(str(len(rsnum_lst)))
	snps_out={}
	for i in range(len(rsnum_lst)):
		snp_info={}
		snp_info["RS"]=rsnum_lst[i]
		snp_info["Alleles"]=allele_lst[i]
		snp_info["Coord"]=pos_lst[i]
		snps_out["snp_"+(digits-len(str(i+1)))*"0"+str(i+1)]=snp_info
	output["snps"]=snps_out
	
	# Create SNP File
	snp_out=open(tmp_dir+"snps_"+request+".txt", "w")
	print >> snp_out, "RS_Number\tPosition (hg19)\tAllele Frequency"
	for k in sorted(output["snps"].keys()):
		rs_k=output["snps"][k]["RS"]
		coord_k=output["snps"][k]["Coord"]
		alleles_k0=output["snps"][k]["Alleles"].strip(" ").split(",")
		alleles_k1=alleles_k0[0]+"0"*(7-len(str(alleles_k0[0])))+","+alleles_k0[1]+"0"*(8-len(str(alleles_k0[1])))
		temp_k=[rs_k,coord_k,alleles_k1]
		print >> snp_out, "\t".join(temp_k)
	snp_out.close()
	
	# Create Haplotype File
	hap_out=open(tmp_dir+"haplotypes_"+request+".txt", "w")
	print >> hap_out, "Haplotype\tCount\tFrequency"
	for k in sorted(output["haplotypes"].keys()):
		hap_k=output["haplotypes"][k]["Haplotype"]
		count_k=str(output["haplotypes"][k]["Count"])
		freq_k=str(output["haplotypes"][k]["Frequency"])
		temp_k=[hap_k,count_k,freq_k]
		print >> hap_out, "\t".join(temp_k)
	hap_out.close()

	
	# Return JSON output
	return(json.dumps(output, sort_keys=True, indent=2))


def main():
	import json,sys
	
	# Import LDLink options
	if len(sys.argv)==4:
		snplst=sys.argv[1]
		pop=sys.argv[2]
		request=sys.argv[3]
	else:
		print "Correct useage is: LDLink.py snplst populations request"
		sys.exit()
		
	
	# Run function
	out_json=calculate_hap(snplst,pop,request)
	
	
	# Print output
	json_dict=json.loads(out_json)
	
	try:
		json_dict["error"]
	
	except KeyError:
		hap_lst=[]
		hap_count=[]
		hap_freq=[]
		for k in sorted(json_dict["haplotypes"].keys()):
			hap_lst.append(json_dict["haplotypes"][k]["Haplotype"])
			hap_count.append(" "*(6-len(str(json_dict["haplotypes"][k]["Count"])))+str(json_dict["haplotypes"][k]["Count"]))
			hap_freq.append(str(json_dict["haplotypes"][k]["Frequency"])+"0"*(6-len(str(json_dict["haplotypes"][k]["Frequency"]))))
		
		# Only print haplotypes >1 percent frequency
		freq_count=0
		for i in range(len(hap_freq)):
			if float(hap_freq[i])>=0.01:
				freq_count+=1
		
		hap_snp=[]
		for i in range(len(hap_lst[0])):
			temp=[]
			for j in range(freq_count):     ## use "len(hap_lst)" for all haplotypes
				temp.append(hap_lst[j][i])
			hap_snp.append(temp)
		
		print ""
		print "RS Number     Coordinates      Allele Frequency      Common Haplotypes (>1%)"
		print ""
		counter=0
		for k in sorted(json_dict["snps"].keys()):
			rs_k=json_dict["snps"][k]["RS"]+" "*(11-len(str(json_dict["snps"][k]["RS"])))
			coord_k=json_dict["snps"][k]["Coord"]+" "*(14-len(str(json_dict["snps"][k]["Coord"])))
			alleles_k0=json_dict["snps"][k]["Alleles"].strip(" ").split(",")
			alleles_k1=alleles_k0[0]+"0"*(7-len(str(alleles_k0[0])))+","+alleles_k0[1]+"0"*(8-len(str(alleles_k0[1])))
			temp_k=[rs_k,coord_k,alleles_k1,"   "+"      ".join(hap_snp[counter])]
			print "   ".join(temp_k)
			counter+=1
		
		print ""
		print "                                         Count: "+" ".join(hap_count[0:freq_count])
		print "                                     Frequency: "+" ".join(hap_freq[0:freq_count])
		
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
