#!/usr/bin/env python
import math,operator,sqlite3,subprocess,sys,time
start_time=time.time()

# Import LDLink options
if len(sys.argv)==3:
	snplst=sys.argv[1]
	pop =sys.argv[2]
	print "\n   command: " + " ".join(sys.argv)
else:
	raise ValueError("Correct useage is: LDLink.py snplst population")


# Open SNP list file
snps=open(snplst).readlines()


# Connect to snp138 database
conn=sqlite3.connect("/DCEG/Home/machielamj/programs/LDlink/snp138/snp138.db")
conn.text_factory=str
cur=conn.cursor()
print "  database: snp138"


# Select desired ancestral population
if pop in ["ALL","AFR","AMR","EAS","EUR","SAS","ACB","ASW","BEB","CDX","CEU","CHB","CHS","CLM","ESN","FIN","GBR","GIH","GWD","IBS","ITU","JPT","KHV","LWK","MSL","MXL","PEL","PJL","PUR","STU","TSI","YRI"]:
	pop_list=open("/DCEG/Home/machielamj/programs/LDlink/1000G/Phase3/samples/"+pop+".txt").readlines()
	pop_ids=[]
	for i in range(len(pop_list)):
		pop_ids.append(pop_list[i].strip())
	print "population: " + pop+" (Individuals="+str(len(pop_ids))+", Haplotypes="+str(2*len(pop_ids))+")\n"

else:
	raise ValueError("%s is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI." % pop)


# Find RS numbers in snp138 database
rs_nums=[]
snp_coords=[]
tabix_coords=""
for i in range(len(snps)):
	snp_i=snps[i].strip().split()
	if snp_i[0][0:2]=="rs":
		cur.execute('SELECT * FROM snps WHERE rsnumber=?', (snp_i[0],))
		snp_coord=cur.fetchone()
		if snp_coord!=None:
			rs_nums.append(snp_i[0])
			temp=[snp_coord[0],snp_coord[1],snp_coord[2]]
			snp_coords.append(temp)
			temp2=snp_coord[1]+":"+snp_coord[2]+"-"+snp_coord[2]
			tabix_coords=tabix_coords+" "+temp2


# Check SNPs are all on the same chromosome
for i in range(len(snp_coords)):
	if snp_coords[0][1]!=snp_coords[i][1]:
		raise ValueError("Not all input SNPs are on the same chromosome")


# Extract 1000 Genomes phased genotypes
vcf_file="/DCEG/Home/machielamj/programs/LDlink/1000G/Phase3/genotypes/ALL.chr"+snp_coord[1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snps="tabix -fh {0}{1} > {2}".format(vcf_file, tabix_coords, "snps.vcf")
subprocess.call(tabix_snps, shell=True)
grep_remove_dups="grep -v -e END snps.vcf > snps_no_dups.vcf"
subprocess.call(grep_remove_dups, shell=True)


# Import SNP VCF files
vcf=open("snps_no_dups.vcf").readlines()
h=0
while vcf[h][0:2]=="##":
	h+=1

head=vcf[h].strip().split()

# Extract haplotypes
index=[]
for i in range(9,len(head)):
	if head[i] in pop_ids:
		index.append(i)

print "SNP Queried\tPosition (GRCh37/hg19)  \tAlleles\tFrequecies"
hap1=[""]*len(index)
hap2=[""]*len(index)
counter=0
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
	else:
		for i in range(len(index)):
			hap1[i]=hap1[i]+"-"
			hap2[i]=hap2[i]+"-"
	
	rsnum=rs_nums[counter]
	counter+=1
	position="chr"+geno[0]+":"+geno[1]+"-"+geno[1]
	alleles=geno[3]+"/"+geno[4]
	f0=round(float(count0)/(count0+count1),4)
	f1=round(float(count1)/(count0+count1),4)
	freq=str(f0)+"/"+str(f1)
	
	temp=[rsnum,position,alleles,freq]
	print "\t".join(temp)

print ""


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


# Format and Print Results
results=[]
for hap in haps:
	temp=[hap,haps[hap]]
	results.append(temp)

results_sort1=sorted(results, key=operator.itemgetter(0))
results_sort2=sorted(results_sort1, key=operator.itemgetter(1), reverse=True)

print "Haplotype\tCount\tFrequency"
for i in results_sort2:
	print i[0]+"\t"+str(i[1])+"\t"+str(round(float(i[1])/(2*len(pop_ids)),4))

print ""

duration=time.time() - start_time
print "Run time: "+str(duration)+" seconds\n"

subprocess.call("rm snps.vcf", shell=True)
subprocess.call("rm snps.vcf", shell=True)