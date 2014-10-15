#!/usr/bin/env python
import math,operator,sqlite3,subprocess,sys,time
start_time=time.time()

# Import LDLink options
if len(sys.argv)==3:
	snp=sys.argv[1]
	pop =sys.argv[2]
	print "\n   command: " + " ".join(sys.argv)
else:
	raise ValueError("Correct useage is: LDProxy.py snp population")



# Find coordinates (GRCh37/hg19) for SNP RS number
# Connect to snp138 database
conn=sqlite3.connect("/DCEG/Home/machielamj/programs/LDlink/snp138/snp138.db")
conn.text_factory=str
cur=conn.cursor()
print "  database: snp138"

# Find RS number in snp138 database
cur.execute('SELECT * FROM snps WHERE rsnumber=?', (snp,))
snp_coord=cur.fetchone()
if snp_coord!=None:
	print "       snp: "+snp_coord[0]+" chr"+snp_coord[1]+":"+snp_coord[2]+"-"+snp_coord[2]+" (GRCh37/hg19)"
else:
	raise ValueError("%s is not a valid RS number for query SNP." % snp)



# Select desired ancestral population
if pop in ["ALL","AFR","AMR","EAS","EUR","SAS","ACB","ASW","BEB","CDX","CEU","CHB","CHS","CLM","ESN","FIN","GBR","GIH","GWD","IBS","ITU","JPT","KHV","LWK","MSL","MXL","PEL","PJL","PUR","STU","TSI","YRI"]:
	pop_list=open("/DCEG/Home/machielamj/programs/LDlink/1000G/Phase3/samples/"+pop+".txt").readlines()
	pop_ids=[]
	for i in range(len(pop_list)):
		pop_ids.append(pop_list[i].strip())
	print "population: " + pop+" (Individuals="+str(len(pop_ids))+", Haplotypes="+str(2*len(pop_ids))+")\n"

else:
	raise ValueError("%s is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI." % pop)


# Extract 1000 Genomes phased genotypes around SNP
window=5000
vcf_file="/DCEG/Home/machielamj/programs/LDlink/1000G/Phase3/genotypes/ALL.chr"+snp_coord[1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snp="tabix -fh {0} {1}:{2}-{3} > {4}".format(vcf_file, snp_coord[1], int(snp_coord[2])-window, int(snp_coord[2])+window, "snps.vcf")
subprocess.call(tabix_snp, shell=True)
grep_remove_dups="grep -v -e END snps.vcf > snps_no_dups.vcf"
subprocess.call(grep_remove_dups, shell=True)


# Import SNP VCF file
vcf=open("snps_no_dups.vcf").readlines()
h=0
while vcf[h][0:2]=="##":
	h+=1

head=vcf[h].strip().split()

s=h+1
while vcf[s].strip().split()[2]!=snp:
	s+=1

geno_ref=vcf[s].strip().split()
if geno_ref[3] in ["A","C","G","T"] and geno_ref[4] in ["A","C","G","T"]:
	allele_ref={"0|0":geno_ref[3]+geno_ref[3],"0|1":geno_ref[3]+geno_ref[4],"1|0":geno_ref[4]+geno_ref[3],"1|1":geno_ref[4]+geno_ref[4],"./.":""}
	geno={}
	for i in range(9,len(head)):
		ind_geno=geno_ref[i].strip().split(":")[0]
		geno[head[i]]=[allele_ref[ind_geno],""]
	
else:
	raise ValueError("%s is not a biallelic SNP." % snp)


# Create LD function
def LD_calcs(n,geno,pop_ids,curr):
	geno_n=vcf[n].strip().split()
	if geno_n[3] in ["A","C","G","T"] and geno_n[4] in ["A","C","G","T"]:
		allele_n={"0|0":geno_n[3]+geno_n[3],"0|1":geno_n[3]+geno_n[4],"1|0":geno_n[4]+geno_n[3],"1|1":geno_n[4]+geno_n[4],"./.":""}
		for i in range(9,len(head)):
			ind_geno=geno_n[i].strip().split(":")[0]
			if head[i] in geno:
				geno[head[i]][1]=allele_n[ind_geno]
			else:
				geno[head[i]]=["",allele_n[ind_geno]]
		
		# Extract haplotypes
		hap={}
		for ind in pop_ids:
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
			snp1_a=[geno_ref[3],geno_ref[4]]
			snp2_a=[geno_n[3],geno_n[4]]
			haps=[snp1_a[0]+snp2_a[0],snp1_a[0]+snp2_a[1],snp1_a[1]+snp2_a[0],snp1_a[1]+snp2_a[1]]
			for i in haps:
				if i not in hap:
					hap[i]=0
		
		# Sort haplotypes
		A=hap[sorted(hap)[0]]
		B=hap[sorted(hap)[1]]
		C=hap[sorted(hap)[2]]
		D=hap[sorted(hap)[3]]
		
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
			
			# Find Correlated Alleles
			if p<0.05 and r2>0.1:
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
				match="  -"
				
			# Get RegulomeDB score
			t=("chr"+geno_n[0]+":"+geno_n[1],)
			curr.execute('SELECT * FROM regdb WHERE position=?', t)
			score=curr.fetchone()
			if score==None:
				score="."
			else:
				score=score[2]
			
			return [snp,"("+geno_ref[3]+"/"+geno_ref[4]+")","chr"+snp_coord[1]+":"+snp_coord[2],geno_n[2],"("+geno_n[3]+"/"+geno_n[4]+")","chr"+geno_n[0]+":"+geno_n[1],int(geno_n[1])-int(geno_ref[1]),D_prime,r2,match,score]


# Open Connection to RegulomeDB
con=sqlite3.connect("/DCEG/Home/machielamj/programs/LDlink/regulomedb/regulomedb.db")
con.row_factory = sqlite3.Row
con.text_factory = str  # Change unicode text to string
curr=con.cursor()

# Iterate over VCF File
out=[]
for n in range(h+1,s):
	result=LD_calcs(n,geno,pop_ids,curr)
	if result!=None:
		out.append(result)

for n in range(s+1,len(vcf)):
	result=LD_calcs(n,geno,pop_ids,curr)
	if result!=None:
		out.append(result)


# Sort output
out_dist_sort=sorted(out, key=operator.itemgetter(6))
out_ld_sort=sorted(out_dist_sort, key=operator.itemgetter(8), reverse=True)


# Print output
#print "Query_SNP\tProxy_SNP\tProxy_Coord\tProxy_Dist\tDprime\tR2\tCorr_Alleles\tRegulomeDB"
print "Query_SNP\tQuery_Alleles\tQuery_Coord\tProxy_SNP\tProxy_Alleles\tProxy_Coord\tProxy_Dist\tDprime\tR2\tCorr_Alleles\tRegulomeDB"
for i in range(len(out)):
	print "\t".join([str(t) for t in out_ld_sort[i]])


# Generate plot
from bokeh.plotting import *
from bokeh.objects import Range1d,HoverTool
from collections import OrderedDict


q_rs=[]
q_allele=[]
q_coord=[]
p_rs=[]
p_allele=[]
p_coord=[]
dist=[]
d_prime=[]
r2=[]
corr_alleles=[]
regdb=[]
for i in range(len(out_ld_sort)):
	q_rs_i,q_allele_i,q_coord_i,p_rs_i,p_allele_i,p_coord_i,dist_i,d_prime_i,r2_i,corr_alleles_i,regdb_i=out_ld_sort[i]
	q_rs.append(q_rs_i)
	q_allele.append(q_allele_i)
	q_coord.append(float(q_coord_i.split(":")[1])/1000000)
	p_rs.append(p_rs_i)
	p_allele.append(p_allele_i)
	p_coord.append(float(p_coord_i.split(":")[1])/1000000)
	dist.append(dist_i)
	d_prime.append(d_prime_i)
	r2.append(float(r2_i))
	corr_alleles.append(corr_alleles_i)
	regdb.append(regdb_i)

x=p_coord
y=r2

source = ColumnDataSource(
    data=dict(
        qrs=q_rs,
        prs=p_rs,
        dist=dist,
        r=r2,
        d=d_prime,
        alleles=corr_alleles,
        regdb=regdb,
    )
)

output_file("scatter.html")
figure(
    title="",
    x_axis_label="Chromosomal Position (Mb)",
    y_axis_label="R2",
    plot_width=800,
    plot_height=400,
    tools=""
)

hold()
TOOLS="hover"
yr=Range1d(start=-0.19, end=1.03)

scatter(x, y, size=12, source=source, color="red", alpha=0.5, y_range=yr, tools=TOOLS)
text(x, y, text=regdb, alpha=0.5, text_font_size="5pt",
     text_baseline="middle", text_align="center", angle=0)

hover = curplot().select(dict(type=HoverTool))
hover.tooltips = OrderedDict([
    ("Query SNP", "@qrs"),
    ("Proxy SNP", "@prs"),
    ("Distance", "@dist"),
    ("R2", "@r"),
    ("D\'", "@d"),
    ("Alleles", "@alleles"),
    ("RegulomeDB", "@regdb"),
])

save()



duration=time.time() - start_time
print "\nRun time: "+str(duration)+" seconds\n"

subprocess.call("rm snps.vcf", shell=True)
#subprocess.call("rm snps_no_dups.vcf", shell=True)