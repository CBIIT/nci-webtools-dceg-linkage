#!/usr/bin/env python
import json,math,operator,sqlite3,subprocess,sys,time
start_time=time.time()

# Import LDLink options
if len(sys.argv)==4:
	snplst=sys.argv[1]
	pop=sys.argv[2]
	request=sys.argv[3]
else:
	print "Correct useage is: LDLink.py snplst populations request"
	sys.exit()

# Set data directories
data_dir="/local/content/ldlink/data/"
snp_dir=data_dir+"snp141/snp141.db"
pop_dir=data_dir+"1000G/Phase3/samples/"
vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"


# Create output JSON file
out=open(request+".json","w")
output={}


# Open SNP list file
snps=open(snplst).readlines()


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
		json.dump(output, out)
		sys.exit()

get_pops="cat "+ " ".join(pop_dirs) +" > pops_"+request+".txt"
subprocess.call(get_pops, shell=True)

pop_list=open("pops_"+request+".txt").readlines()
ids=[]
for i in range(len(pop_list)):
	ids.append(pop_list[i].strip())

pop_ids=list(set(ids))


# Find RS numbers in snp141 database
rs_nums=[]
snp_pos=[]
snp_coords=[]
tabix_coords=""
for i in range(len(snps)):
	snp_i=snps[i].strip().split()
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


# Check SNPs are all on the same chromosome
for i in range(len(snp_coords)):
	if snp_coords[0][1]!=snp_coords[i][1]:
		output["error"]="Not all input SNPs are on the same chromosome"
		json.dump(output, out)
		sys.exit()


# Extract 1000 Genomes phased genotypes
vcf_file=vcf_dir+snp_coord[2]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snps="tabix -fh {0}{1} > {2}".format(vcf_file, tabix_coords, "snps_"+request+".vcf")
subprocess.call(tabix_snps, shell=True)
grep_remove_dups="grep -v -e END snps_"+request+".vcf > snps_no_dups_"+request+".vcf"
subprocess.call(grep_remove_dups, shell=True)


# Import SNP VCF files
vcf=open("snps_no_dups_"+request+".vcf").readlines()
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
for i in range(len(results_sort2)):
	hap_info={}
	hap_info["Haplotype"]=results_sort2[i][0]
	hap_info["Count"]=results_sort2[i][1]
	hap_info["Frequency"]=round(float(results_sort2[i][1])/(2*len(pop_ids)),4)
	output["haplotype_"+(digits-len(str(i)))*"0"+str(i+1)]=hap_info


# Save JSON output
json.dump(output, out, sort_keys=True, indent=2)


duration=time.time() - start_time
print "Run time: "+str(duration)+" seconds\n"

subprocess.call("rm pops_"+request+".txt", shell=True)
subprocess.call("rm *_"+request+".vcf", shell=True)