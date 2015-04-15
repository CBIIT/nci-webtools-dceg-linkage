#!/usr/bin/env python

# Create LDpair function
def calculate_pair(snp1,snp2,pop,request):
	import json,math,os,sqlite3,subprocess,sys

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


	# Connect to snp142 database
	conn=sqlite3.connect(snp_dir)
	conn.text_factory=str
	cur=conn.cursor()
	
	def get_coords(rs):
		id=rs.strip("rs")
		t=(id,)
		cur.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
		return cur.fetchone()

	# Find RS numbers in snp141 database
	# SNP1
	snp1_coord=get_coords(snp1)
	
	if snp1_coord==None:
		output["error"]=snp1+" is not in dbSNP build 142."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise
	
	# SNP2
	snp2_coord=get_coords(snp2)
	if snp2_coord==None:
		output["error"]=snp2+" is not in dbSNP build 141."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise
	
	
	# Check if SNPs are on the same chromosome
	if snp1_coord[1]!=snp2_coord[1]:
		output["warning"]=snp1+" and "+snp2+" are on different chromosomes"
	
	
	
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
	
	
	
	# Extract 1000 Genomes phased genotypes
	# SNP1
	vcf_file1=vcf_dir+snp1_coord[1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
	tabix_snp1="tabix -fh {0} {1}:{2}-{2} | grep -v -e END".format(vcf_file1, snp1_coord[1], snp1_coord[2])
	proc1=subprocess.Popen(tabix_snp1, shell=True, stdout=subprocess.PIPE)

	# SNP2
	vcf_file2=vcf_dir+snp2_coord[1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
	tabix_snp2="tabix -fh {0} {1}:{2}-{2} | grep -v -e END".format(vcf_file2, snp2_coord[1], snp2_coord[2])
	proc2=subprocess.Popen(tabix_snp2, shell=True, stdout=subprocess.PIPE)

	# Import SNP VCF files
	vcf1=proc1.stdout.readlines()
	head1=vcf1[len(vcf1)-2].strip().split()
	geno1=vcf1[len(vcf1)-1].strip().split()

	if geno1[0]=="#CHROM":
		output["error"]=snp1+" is not in 1000G reference panel."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise

	if geno1[3] in ["A","C","G","T"] and geno1[4] in ["A","C","G","T"]:
		allele1={"0|0":geno1[3]+geno1[3],"0|1":geno1[3]+geno1[4],"1|0":geno1[4]+geno1[3],"1|1":geno1[4]+geno1[4],"0":geno1[3]+".","1":geno1[4]+".","./.":"..",".":".."}
	else:
		output["error"]=snp1+" is not a biallelic SNP."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise

	vcf2=proc2.stdout.readlines()
	head2=vcf2[len(vcf2)-2].strip().split()
	geno2=vcf2[len(vcf2)-1].strip().split()

	if geno2[0]=="#CHROM":
		output["error"]=snp2+" is not in 1000G reference panel."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise

	if geno2[3] in ["A","C","G","T"] and geno2[4] in ["A","C","G","T"]:
		allele2={"0|0":geno2[3]+geno2[3],"0|1":geno2[3]+geno2[4],"1|0":geno2[4]+geno2[3],"1|1":geno2[4]+geno2[4],"0":geno2[3]+".","1":geno2[4]+".","./.":"..",".":".."}
	else:
		output["error"]=snp2+" is not a biallelic SNP."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise


	if geno1[1]!=snp1_coord[2] or geno2[1]!=snp2_coord[2]:
		output["error"]="VCF File does not match SNP coordinates."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise

	# Combine phased genotypes
	geno={}
	for i in range(9,len(head1)):
		geno[head1[i]]=[allele1[geno1[i]],".."]

	for i in range(9,len(head2)):
		if head2[i] in geno:
			geno[head2[i]][1]=allele2[geno2[i]]

	# Extract haplotypes
	hap={}
	for ind in pop_ids:
		if ind in geno:
			hap1=geno[ind][0][0]+geno[ind][1][0]
			hap2=geno[ind][0][1]+geno[ind][1][1]

			if hap1 in hap:
				hap[hap1]+=1
			else:
				hap[hap1]=1

			if hap2 in hap:
				hap[hap2]+=1
			else:
				hap[hap2]=1

	# Remove Missing Haplotypes
	keys=hap.keys()
	for key in keys:
		if "." in key:
			hap.pop(key, None)
	
	# Check all haplotypes are present
	if len(hap)!=4:
		snp1_a=[geno1[3],geno1[4]]
		snp2_a=[geno2[3],geno2[4]]
		haps=[snp1_a[0]+snp2_a[0],snp1_a[0]+snp2_a[1],snp1_a[1]+snp2_a[0],snp1_a[1]+snp2_a[1]]
		for i in haps:
			if i not in hap:
				hap[i]=0

	# Sort haplotypes
	A=hap[sorted(hap)[0]]
	B=hap[sorted(hap)[1]]
	C=hap[sorted(hap)[2]]
	D=hap[sorted(hap)[3]]
	N=A+B+C+D

	hap1=sorted(hap, key=hap.get, reverse=True)[0]
	hap2=sorted(hap, key=hap.get, reverse=True)[1]
	hap3=sorted(hap, key=hap.get, reverse=True)[2]
	hap4=sorted(hap, key=hap.get, reverse=True)[3]

	delta=float(A*D-B*C)
	Ms=float((A+C)*(B+D)*(A+B)*(C+D))
	if Ms!=0:

		# D prime
		if delta<0:
			D_prime=delta/min((A+C)*(A+B),(B+D)*(C+D))
		else:
			D_prime=delta/min((A+C)*(C+D),(A+B)*(B+D))

		# R2
		r2=(delta**2)/Ms

		# P-value
		num=(A+B+C+D)*(A*D-B*C)**2
		denom=Ms
		chisq=num/denom
		p=2*(1-(0.5*(1+math.erf(chisq**0.5/2**0.5))))

	else:
		D_prime="NA"
		r2="NA"
		chisq="NA"
		p="NA"

	# Find Correlated Alleles
	if r2>0.1 and r2!="NA":
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
			corr1=snp1+"("+sorted(hap)[0][0]+") allele is correlated with "+snp2+"("+sorted(hap)[0][1]+") allele"
			corr2=snp1+"("+sorted(hap)[2][0]+") allele is correlated with "+snp2+"("+sorted(hap)[1][1]+") allele"
			corr_alleles=[corr1,corr2]
		else:
			corr1=snp1+"("+sorted(hap)[0][0]+") allele is correlated with "+snp2+"("+sorted(hap)[1][1]+") allele"
			corr2=snp1+"("+sorted(hap)[2][0]+") allele is correlated with "+snp2+"("+sorted(hap)[0][1]+") allele"
			corr_alleles=[corr1,corr2]
	else:
		corr_alleles=[snp1+" and "+snp2+" are in linkage equilibrium"]



	# Create JSON output
	snp_1={}
	snp_1["rsnum"]=snp1
	snp_1["coord"]="chr"+snp1_coord[1]+":"+snp1_coord[2]

	snp_1_allele_1={}
	snp_1_allele_1["allele"]=sorted(hap)[0][0]
	snp_1_allele_1["count"]=str(A+B)
	snp_1_allele_1["frequency"]=str(round(float(A+B)/N,3))
	snp_1["allele_1"]=snp_1_allele_1

	snp_1_allele_2={}
	snp_1_allele_2["allele"]=sorted(hap)[2][0]
	snp_1_allele_2["count"]=str(C+D)
	snp_1_allele_2["frequency"]=str(round(float(C+D)/N,3))
	snp_1["allele_2"]=snp_1_allele_2
	output["snp1"]=snp_1


	snp_2={}
	snp_2["rsnum"]=snp2
	snp_2["coord"]="chr"+snp2_coord[1]+":"+snp2_coord[2]

	snp_2_allele_1={}
	snp_2_allele_1["allele"]=sorted(hap)[0][1]
	snp_2_allele_1["count"]=str(A+C)
	snp_2_allele_1["frequency"]=str(round(float(A+C)/N,3))
	snp_2["allele_1"]=snp_2_allele_1

	snp_2_allele_2={}
	snp_2_allele_2["allele"]=sorted(hap)[1][1]
	snp_2_allele_2["count"]=str(B+D)
	snp_2_allele_2["frequency"]=str(round(float(B+D)/N,3))
	snp_2["allele_2"]=snp_2_allele_2
	output["snp2"]=snp_2


	two_by_two={}
	cells={}
	cells["c11"]=str(A)
	cells["c12"]=str(B)
	cells["c21"]=str(C)
	cells["c22"]=str(D)
	two_by_two["cells"]=cells
	two_by_two["total"]=str(N)
	output["two_by_two"]=two_by_two


	haplotypes={}
	hap_1={}
	hap_1["alleles"]=hap1
	hap_1["count"]=str(hap[hap1])
	hap_1["frequency"]=str(round(float(hap[hap1])/N,3))
	haplotypes["hap1"]=hap_1

	hap_2={}
	hap_2["alleles"]=hap2
	hap_2["count"]=str(hap[hap2])
	hap_2["frequency"]=str(round(float(hap[hap2])/N,3))
	haplotypes["hap2"]=hap_2

	hap_3={}
	hap_3["alleles"]=hap3
	hap_3["count"]=str(hap[hap3])
	hap_3["frequency"]=str(round(float(hap[hap3])/N,3))
	haplotypes["hap3"]=hap_3

	hap_4={}
	hap_4["alleles"]=hap4
	hap_4["count"]=str(hap[hap4])
	hap_4["frequency"]=str(round(float(hap[hap4])/N,3))
	haplotypes["hap4"]=hap_4
	output["haplotypes"]=haplotypes


	statistics={}
	if Ms!=0:
		statistics["d_prime"]=str(round(abs(D_prime),4))
		statistics["r2"]=str(round(r2,4))
		statistics["chisq"]=str(round(chisq,4))
		statistics["p"]=str(round(p,4))
	else:
		statistics["d_prime"]=D_prime
		statistics["r2"]=r2
		statistics["chisq"]=chisq
		statistics["p"]=p

	output["statistics"]=statistics

	output["corr_alleles"]=corr_alleles
	
	
	# Return output
	return(json.dumps(output, sort_keys=True, indent=2))


def main():
	import json,sys

	# Import LDpair options
	if len(sys.argv)==5:
		snp1=sys.argv[1]
		snp2=sys.argv[2]
		pop=sys.argv[3]
		request=sys.argv[4]
	else:
		print "Correct useage is: LDpair.py snp1 snp2 populations request"
		sys.exit()

	# Run function
	out_json=calculate_pair(snp1,snp2,pop,request)

	# Print output
	json_dict=json.loads(out_json)
	try:
		json_dict["error"]

	except KeyError:
		print ""
		print "Query SNPs:"
		print json_dict["snp1"]["rsnum"]+" ("+json_dict["snp1"]["coord"]+")"
		print json_dict["snp2"]["rsnum"]+" ("+json_dict["snp2"]["coord"]+")"
		print ""
		print pop+" Haplotypes:"
		print " "*15+json_dict["snp2"]["rsnum"]
		print " "*15+json_dict["snp2"]["allele_1"]["allele"]+" "*7+json_dict["snp2"]["allele_2"]["allele"]
		print " "*13+"-"*17
		print " "*11+json_dict["snp1"]["allele_1"]["allele"]+" | "+json_dict["two_by_two"]["cells"]["c11"]+" "*(5-len(json_dict["two_by_two"]["cells"]["c11"]))+" | "+json_dict["two_by_two"]["cells"]["c12"]+" "*(5-len(json_dict["two_by_two"]["cells"]["c12"]))+" | "+json_dict["snp1"]["allele_1"]["count"]+" "*(5-len(json_dict["snp1"]["allele_1"]["count"]))+" ("+json_dict["snp1"]["allele_1"]["frequency"]+")"
		print json_dict["snp1"]["rsnum"]+" "*(10-len(json_dict["snp1"]["rsnum"]))+" "*3+"-"*17
		print " "*11+json_dict["snp2"]["allele_2"]["allele"]+" | "+json_dict["two_by_two"]["cells"]["c21"]+" "*(5-len(json_dict["two_by_two"]["cells"]["c21"]))+" | "+json_dict["two_by_two"]["cells"]["c22"]+" "*(5-len(json_dict["two_by_two"]["cells"]["c22"]))+" | "+json_dict["snp1"]["allele_2"]["count"]+" "*(5-len(json_dict["snp1"]["allele_2"]["count"]))+" ("+json_dict["snp1"]["allele_2"]["frequency"]+")"
		print " "*13+"-"*17
		print " "*15+json_dict["snp2"]["allele_1"]["count"]+" "*(5-len(json_dict["snp2"]["allele_1"]["count"]))+" "*3+json_dict["snp2"]["allele_2"]["count"]+" "*(5-len(json_dict["snp2"]["allele_2"]["count"]))+" "*3+json_dict["two_by_two"]["total"]
		print " "*14+"("+json_dict["snp2"]["allele_1"]["frequency"]+")"+" "*(5-len(json_dict["snp2"]["allele_1"]["frequency"]))+" ("+json_dict["snp2"]["allele_2"]["frequency"]+")"+" "*(5-len(json_dict["snp2"]["allele_2"]["frequency"]))
		print ""
		print "          "+json_dict["haplotypes"]["hap1"]["alleles"]+": "+json_dict["haplotypes"]["hap1"]["count"]+" ("+json_dict["haplotypes"]["hap1"]["frequency"]+")"
		print "          "+json_dict["haplotypes"]["hap2"]["alleles"]+": "+json_dict["haplotypes"]["hap2"]["count"]+" ("+json_dict["haplotypes"]["hap2"]["frequency"]+")"
		print "          "+json_dict["haplotypes"]["hap3"]["alleles"]+": "+json_dict["haplotypes"]["hap3"]["count"]+" ("+json_dict["haplotypes"]["hap3"]["frequency"]+")"
		print "          "+json_dict["haplotypes"]["hap4"]["alleles"]+": "+json_dict["haplotypes"]["hap4"]["count"]+" ("+json_dict["haplotypes"]["hap4"]["frequency"]+")"
		print ""
		print "          D': "+json_dict["statistics"]["d_prime"]
		print "          R2: "+json_dict["statistics"]["r2"]
		print "      Chi-sq: "+json_dict["statistics"]["chisq"]
		print "     p-value: "+json_dict["statistics"]["p"]
		print ""
		if len(json_dict["corr_alleles"])==2:
			print json_dict["corr_alleles"][0]
			print json_dict["corr_alleles"][1]
		else:
			print json_dict["corr_alleles"][0]

		try:
			json_dict["warning"]
		except KeyError:
			print ""
		else:
			print "WARNING: "+json_dict["warning"]+"!"
			print ""

	else:
		print ""
		print json_dict["error"]
		print ""


if __name__ == "__main__":
	main()
