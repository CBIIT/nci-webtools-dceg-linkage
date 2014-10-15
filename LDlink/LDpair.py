#!/usr/bin/env python
import json,math,sqlite3,subprocess,sys,time
start=time.time()
random=str(start)

# Create output dictionary
out=open(random+".json","w")
output={}

# Import LDLink options
if len(sys.argv)==4:
	snp1=sys.argv[1]
	snp2=sys.argv[2]
	pop =sys.argv[3]
else:
	output["error"]="Correct useage is: LDpair.py snp1 snp2 population"
	json.dump(output, out)
	sys.exit()

	
# Find coordinates (GRCh37/hg19) for SNP RS numbers
# Connect to snp138 database
conn=sqlite3.connect("/local/content/ldlink/data/snp138/snp138.db")
conn.text_factory=str
cur=conn.cursor()

# Find RS numbers in snp138 database
# SNP1
cur.execute('SELECT * FROM snps WHERE rsnumber=?', (snp1,))
snp1_coord=cur.fetchone()
if snp1_coord!=None:
	print "      snp1: "+snp1_coord[0]+" chr"+snp1_coord[1]+":"+snp1_coord[2]+"-"+snp1_coord[2]+" (GRCh37/hg19)"
else:
	output["error"]=snp1+" is not a valid RS number for SNP1."
	json.dump(output, out)
	sys.exit()

# SNP2
cur.execute('SELECT * FROM snps WHERE rsnumber=?', (snp2,))
snp2_coord=cur.fetchone()
if snp2_coord!=None:
	print "      snp2: "+snp2_coord[0]+" chr"+snp2_coord[1]+":"+snp2_coord[2]+"-"+snp2_coord[2]+" (GRCh37/hg19)"
else:
	output["error"]=snp2+" is not a valid RS number for SNP2."
	json.dump(output, out)
	sys.exit()

# Check if SNPs are on the same chromosome
if snp1_coord[1]!=snp2_coord[1]:
	output["warning"]=snp1+" and "+snp2+" are on different chromosomes"



# Select desired ancestral population
if pop in ["ALL","AFR","AMR","EAS","EUR","SAS","ACB","ASW","BEB","CDX","CEU","CHB","CHS","CLM","ESN","FIN","GBR","GIH","GWD","IBS","ITU","JPT","KHV","LWK","MSL","MXL","PEL","PJL","PUR","STU","TSI","YRI"]:
	pop_list=open("/local/content/ldlink/data/1000G/Phase3/samples/"+pop+".txt").readlines()
	pop_ids=[]
	for i in range(len(pop_list)):
		pop_ids.append(pop_list[i].strip())
	print "population: " + pop+" (Individuals="+str(len(pop_ids))+", Haplotypes="+str(2*len(pop_ids))+")\n"

else:
	output["error"]=pop+" is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
	json.dump(output, out)
	sys.exit()



# Extract 1000 Genomes phased genotypes
# SNP1
vcf_file1="/local/content/ldlink/data/1000G/Phase3/genotypes/ALL.chr"+snp1_coord[1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snp1="/usr/local/tabix-0.2.6/tabix -fh {0} {1}:{2}-{2} > {3}".format(vcf_file1, snp1_coord[1], snp1_coord[2], "snp1_"+random+".vcf")
subprocess.call(tabix_snp1, shell=True)
grep_remove_dups="grep -v -e END snp1_"+random+".vcf > snp1_no_dups_"+random+".vcf"
subprocess.call(grep_remove_dups, shell=True)

# SNP2
vcf_file2="/local/content/tabix-0.2.6/ldlink/data/1000G/Phase3/genotypes$$/ALL.chr"+snp2_coord[1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snp2="/usr/local/$$tabix -fh {0} {1}:{2}-{2} > {3}".format(vcf_file2, snp2_coord[1], snp2_coord[2], "snp2_"+random+".vcf")
subprocess.call(tabix_snp2, shell=True)
grep_remove_dups="grep -v -e END snp2_"+random+".vcf > snp2_no_dups_"+random+".vcf"
subprocess.call(grep_remove_dups, shell=True)

# Import SNP VCF files
vcf1=open("snp1_no_dups_"+random+".vcf").readlines()
head1=vcf1[len(vcf1)-2].strip().split()
geno1=vcf1[len(vcf1)-1].strip().split()
if geno1[3] in ["A","C","G","T"] and geno1[4] in ["A","C","G","T"]:
	allele1={"0|0":geno1[3]+geno1[3],"0|1":geno1[3]+geno1[4],"1|0":geno1[4]+geno1[3],"1|1":geno1[4]+geno1[4],"./.":""}
else:
	output["error"]=snp1+" is not a biallelic SNP."
	json.dump(output, out)
	sys.exit()

vcf2=open("snp2_no_dups_"+random+".vcf").readlines()
head2=vcf2[len(vcf2)-2].strip().split()
geno2=vcf2[len(vcf2)-1].strip().split()
if geno2[3] in ["A","C","G","T"] and geno2[4] in ["A","C","G","T"]:
	allele2={"0|0":geno2[3]+geno2[3],"0|1":geno2[3]+geno2[4],"1|0":geno2[4]+geno2[3],"1|1":geno2[4]+geno2[4],"./.":""}
else:
	output["error"]=snp2+" is not a biallelic SNP."
	json.dump(output, out)
	sys.exit()


if geno1[1]!=snp1_coord[2] or geno2[1]!=snp2_coord[2]:
	output["error"]="VCF File does not match SNP coordinates."
	json.dump(output, out)
	sys.exit()

# Combine phased genotypes
geno={}
for i in range(9,len(head1)):
	geno[head1[i]]=[allele1[geno1[i]],""]

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

print pop+" Haplotypes:"
print " "*15+snp2
print " "*15+sorted(hap)[0][1]+" "*7+sorted(hap)[1][1]
print " "*13+"-"*17
print " "*11+sorted(hap)[0][0]+" | "+str(A)+" "*(5-len(str(A)))+" | "+str(B)+" "*(5-len(str(B)))+" | "+str(A+B)+" "*(5-len(str(A+B)))+" ("+str(round(float(A+B)/(A+B+C+D),3))+")"
print snp1+" "*(10-len(snp1))+" "*3+"-"*17
print " "*11+sorted(hap)[2][0]+" | "+str(C)+" "*(5-len(str(C)))+" | "+str(D)+" "*(5-len(str(D)))+" | "+str(C+D)+" "*(5-len(str(C+D)))+" ("+str(round(float(C+D)/(A+B+C+D),3))+")"
print " "*13+"-"*17
print " "*15+str(A+C)+" "*(5-len(str(A+C)))+" "*3+str(B+D)+" "*(5-len(str(B+D)))+" "*3+str(A+B+C+D)
print " "*14+"("+str(round(float(A+C)/(A+B+C+D),3))+")"+" "*(5-len(str(round(float(A+C)/(A+B+C+D),3))))+" ("+str(round(float(B+D)/(A+B+C+D),3))+")"+" "*(5-len(str(round(float(B+D)/(A+B+C+D),3))))
print ""

print "        "+sorted(hap)[0]+": "+str(A)+"\t("+str(round(float(A)/N,3))+")"
print "        "+sorted(hap)[1]+": "+str(B)+"\t("+str(round(float(B)/N,3))+")"
print "        "+sorted(hap)[2]+": "+str(C)+"\t("+str(round(float(C)/N,3))+")"
print "        "+sorted(hap)[3]+": "+str(D)+"\t("+str(round(float(D)/N,3))+")"
print ""

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
	p=1

print "        D': "+str(round(abs(D_prime),4))
print "        R2: "+str(round(r2,4))
print "    Chi-sq: "+str(round(chisq,3))
print "   p-value: "+str(round(p,4))
print ""

# Find Correlated Alleles
if p<0.05 and r2>0.1:
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
		print snp1+"("+sorted(hap)[0][0]+") allele is correlated with "+snp2+"("+sorted(hap)[0][1]+") allele"
		print snp1+"("+sorted(hap)[2][0]+") allele is correlated with "+snp2+"("+sorted(hap)[1][1]+") allele\n"
		corr1=snp1+"("+sorted(hap)[0][0]+") allele is correlated with "+snp2+"("+sorted(hap)[0][1]+") allele"
		corr2=snp1+"("+sorted(hap)[2][0]+") allele is correlated with "+snp2+"("+sorted(hap)[1][1]+") allele"
		corr_alleles=[corr1,corr2]
	else:
		print snp1+"("+sorted(hap)[0][0]+") allele is correlated with "+snp2+"("+sorted(hap)[1][1]+") allele"
		print snp1+"("+sorted(hap)[2][0]+") allele is correlated with "+snp2+"("+sorted(hap)[0][1]+") allele\n"
		corr1=snp1+"("+sorted(hap)[0][0]+") allele is correlated with "+snp2+"("+sorted(hap)[1][1]+") allele"
		corr2=snp1+"("+sorted(hap)[2][0]+") allele is correlated with "+snp2+"("+sorted(hap)[0][1]+") allele"
		corr_alleles=[corr1,corr2]
else:
	print snp1+" and "+snp2+" are in linkage equilibrium.\n"
	corr_alleles=snp1+" and "+snp2+" are in linkage equilibrium"



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


table={}
cells={}
cells["11"]=str(A)
cells["12"]=str(B)
cells["21"]=str(C)
cells["22"]=str(D)
table["cells"]=cells
table["total"]=str(N)
output["table"]=table


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
statistics["d_prime"]=str(round(abs(D_prime),4))
statistics["r2"]=str(round(r2,4))
statistics["chisq"]=str(round(chisq,3))
statistics["p"]=str(round(p,4))
output["statistics"]=statistics

output["corr_alleles"]=corr_alleles
json.dump(output, out, sort_keys=True, indent=2)


duration=time.time()-start
print "Run time: "+str(duration)+" seconds\n"

subprocess.call("rm snp1_"+random+".vcf", shell=True)
subprocess.call("rm snp1_no_dups_"+random+".vcf", shell=True)
subprocess.call("rm snp2_"+random+".vcf", shell=True)
subprocess.call("rm snp2_no_dups_"+random+".vcf", shell=True)
