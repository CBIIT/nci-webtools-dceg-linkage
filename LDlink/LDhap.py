#!/usr/bin/env python

# Create LDhap function
def calculate_hap(snplst,pop,request):
	import json,math,operator,os,sqlite3,subprocess,sys,time
	start_time=time.time()
	
	# Set data directories
	data_dir="/local/content/ldlink/data/"
	snp_dir=data_dir+"snp141/snp141.db"
	pop_dir=data_dir+"1000G/Phase3/samples/"
	vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"
	tmp_dir="./tmp/"
	
	
	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)
	
	
	# Create JSON output
	output={}
	
	
	# Open SNP list file
	snps=open(snplst).readlines()
	if len(snps)>30:
		output["error"]="Maximum SNP list is 30 SNPs. Your list contains "+str(len(snps))+" entries."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise
	
	
	# Find coordinates (GRCh37/hg19) for SNP RS number
	# Connect to snp141 database
	conn=sqlite3.connect(snp_dir)
	conn.text_factory=str
	cur=conn.cursor()
	
	
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
	
	get_pops="cat "+ " ".join(pop_dirs) +" > "+tmp_dir+"pops_"+request+".txt"
	subprocess.call(get_pops, shell=True)
	
	pop_list=open(tmp_dir+"pops_"+request+".txt").readlines()
	ids=[]
	for i in range(len(pop_list)):
		ids.append(pop_list[i].strip())
	
	pop_ids=list(set(ids))
	
	
	# Find RS numbers in snp141 database
	rs_nums=[]
	snp_pos=[]
	snp_coords=[]
	warn=[]
	tabix_coords=""
	for i in range(len(snps)):
		snp_i=snps[i].strip().split()
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
						temp2=snp_coord[2]+":"+snp_coord[3]+"-"+snp_coord[3]
						tabix_coords=tabix_coords+" "+temp2
					else:
						warn.append(snp_i[0])
	
	if warn!=[]:
		output["warning"]="Not all input SNPs were found in dbSNP 141 ("+",".join(warn)+")"
	
	
	# Check SNPs are all on the same chromosome
	for i in range(len(snp_coords)):
		if snp_coords[0][1]!=snp_coords[i][1]:
			output["error"]="Not all input SNPs are on the same chromosome"
			return(json.dumps(output, sort_keys=True, indent=2))
			raise
	
	
	# Extract 1000 Genomes phased genotypes
	vcf_file=vcf_dir+snp_coord[2]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
	tabix_snps="tabix -fh {0}{1} > {2}".format(vcf_file, tabix_coords, tmp_dir+"snps_"+request+".vcf")
	subprocess.call(tabix_snps, shell=True)
	grep_remove_dups="grep -v -e END "+tmp_dir+"snps_"+request+".vcf > "+tmp_dir+"snps_no_dups_"+request+".vcf"
	subprocess.call(grep_remove_dups, shell=True)
	
	
	# Import SNP VCF files
	vcf=open(tmp_dir+"snps_no_dups_"+request+".vcf").readlines()
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
	
	
	# Sort results
	results=[]
	for hap in haps:
		temp=[hap,haps[hap]]
		results.append(temp)
	
	results_sort1=sorted(results, key=operator.itemgetter(0))
	results_sort2=sorted(results_sort1, key=operator.itemgetter(1), reverse=True)
	
	
	# Generate JSON output
	digits=len(str(len(results_sort2)))
	haps_out={}
	for i in range(len(results_sort2)):
		hap_info={}
		hap_info["Haplotype"]=results_sort2[i][0]
		hap_info["Count"]=results_sort2[i][1]
		hap_info["Frequency"]=round(float(results_sort2[i][1])/(2*len(pop_ids)),4)
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
	
	
	duration=time.time() - start_time
	
	subprocess.call("rm "+tmp_dir+"pops_"+request+".txt", shell=True)
	subprocess.call("rm "+tmp_dir+"*_"+request+".vcf", shell=True)
	
	
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
