#!/usr/bin/env python
import csv,json,operator,sqlite3,subprocess,sys,time
start_time=time.time()

# Import LDLink options
if len(sys.argv)==4:
	snp=sys.argv[1]
	pop=sys.argv[2]
	request=sys.argv[3]
else:
	print "Correct useage is: LDproxy.py snp populations request"
	sys.exit()


# Set data directories
data_dir="/local/content/ldlink/data/"
snp_dir=data_dir+"snp141/snp141.db"
pop_dir=data_dir+"1000G/Phase3/samples/"
vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"

# Create output JSON file
out=open(request+".json","w")
output={}


# Find coordinates (GRCh37/hg19) for SNP RS number
# Connect to snp141 database
conn=sqlite3.connect(snp_dir)
conn.text_factory=str
cur=conn.cursor()

# Find RS number in snp141 database
id="99"+(13-len(snp))*"0"+snp.strip("rs")
cur.execute('SELECT * FROM snps WHERE id=?', (id,))
snp_coord=cur.fetchone()
if snp_coord==None:
	output["error"]=snp+" is not a valid RS number for query SNP."
	json.dump(output, out)
	sys.exit()


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


# Extract 1000 Genomes phased genotypes around SNP
vcf_file=vcf_dir+snp_coord[2]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snp="tabix -fh {0} {1}:{2}-{2} > {3}".format(vcf_file, snp_coord[2], snp_coord[3], "snp_"+request+".vcf")
subprocess.call(tabix_snp, shell=True)
grep_remove_dups="grep -v -e END snp_"+request+".vcf > snp_no_dups_"+request+".vcf"
subprocess.call(grep_remove_dups, shell=True)

window=500000
coord1=int(snp_coord[3])-window
if coord1<0:
	coord1=0
coord2=int(snp_coord[3])+window


# Run in parallel
vcf=open("snp_no_dups_"+request+".vcf").readlines()
geno=vcf[len(vcf)-1].strip().split()
if geno[3] in ["A","C","G","T"] and geno[4] in ["A","C","G","T"]:
	threads=4
	block=(2*window)/4
	commands=[]
	for i in range(threads):
		if i==min(range(threads)) and i==max(range(threads)):
			command="python LDproxy_sub.py "+snp+" "+snp_coord[2]+" "+str(coord1)+" "+str(coord2)+" "+request+" "+str(i)
		elif i==min(range(threads)):
			command="python LDproxy_sub.py "+snp+" "+snp_coord[2]+" "+str(coord1)+" "+str(coord1+block)+" "+request+" "+str(i)
		elif i==max(range(threads)):
			command="python LDproxy_sub.py "+snp+" "+snp_coord[2]+" "+str(coord1+(block*i)+1)+" "+str(coord2)+" "+request+" "+str(i)
		else:
			command="python LDproxy_sub.py "+snp+" "+snp_coord[2]+" "+str(coord1+(block*i)+1)+" "+str(coord1+(block*(i+1)))+" "+request+" "+str(i)
		commands.append(command)

	processes=[subprocess.Popen(command, shell=True) for command in commands]
	for p in processes:
		p.wait()

else:
	output["error"]=snp+" is not a biallelic SNP."
	json.dump(output, out)
	sys.exit()


# Aggregate output
get_out="cat "+request+"_*.out > "+request+"_all.out"
subprocess.call(get_out, shell=True)
out_raw=open(request+"_all.out").readlines()
out_prox=[]
for i in range(len(out_raw)):
	col=out_raw[i].strip().split("\t")
	col[6]=int(col[6])
	col[8]=float(col[8])
	col.append(abs(int(col[6])))
	out_prox.append(col)


# Sort output
out_dist_sort=sorted(out_prox, key=operator.itemgetter(11))
out_ld_sort=sorted(out_dist_sort, key=operator.itemgetter(8), reverse=True)
for i in range(200):
	print out_ld_sort[i]


# Populate JSON output
query_snp={}
query_snp["RS"]=out_ld_sort[0][0]
query_snp["Alleles"]=out_ld_sort[0][1]
query_snp["Coord"]=out_ld_sort[0][2]
query_snp["Dist"]=out_ld_sort[0][6]
query_snp["Dprime"]=out_ld_sort[0][7]
query_snp["R2"]=out_ld_sort[0][8]
query_snp["Corr_Alleles"]=out_ld_sort[0][9]
query_snp["RegulomeDB"]=out_ld_sort[0][10]

output["query_snp"]=query_snp

proxies={}
digits=len(str(len(out_ld_sort)))
for i in range(1,len(out_ld_sort)):
	if float(out_ld_sort[i][8])>0.1:
		proxy_info={}
		proxy_info["RS"]=out_ld_sort[i][3]
		proxy_info["Alleles"]=out_ld_sort[i][4]
		proxy_info["Coord"]=out_ld_sort[i][5]
		proxy_info["Dist"]=out_ld_sort[i][6]
		proxy_info["Dprime"]=out_ld_sort[i][7]
		proxy_info["R2"]=out_ld_sort[i][8]
		proxy_info["Corr_Alleles"]=out_ld_sort[i][9]
		proxy_info["RegulomeDB"]=out_ld_sort[i][10]
		
		proxies["proxy_"+(digits-len(str(i)))*"0"+str(i)]=proxy_info

output["proxy_snps"]=proxies

# Save JSON output
json.dump(output, out, sort_keys=True, indent=2)


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
	q_rs_i,q_allele_i,q_coord_i,p_rs_i,p_allele_i,p_coord_i,dist_i,d_prime_i,r2_i,corr_alleles_i,regdb_i,dist_abs=out_ld_sort[i]
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

source=ColumnDataSource(
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

output_file(request+"_scatter.html")
figure(
	title="",
	plot_width=800,
	plot_height=400,
	tools=""
)

hold()
TOOLS="hover,pan,box_zoom,wheel_zoom,reset,previewsave"
xr=Range1d(start=coord1/1000000.0, end=coord2/1000000.0)
yr=Range1d(start=-0.03, end=1.03)

scatter(x, y, size=12, source=source, color="red", alpha=0.5, x_range=xr, y_range=yr, tools=TOOLS)
text(x, y, text=regdb, alpha=1, text_font_size="6pt",
	 text_baseline="middle", text_align="center", angle=0)

xaxis().axis_label="Chromosomal Position (Mb)"
yaxis().axis_label="R2"

hover=curplot().select(dict(type=HoverTool))
hover.tooltips=OrderedDict([
	("Query SNP", "@qrs"),
	("Proxy SNP", "@prs"),
	("Distance", "@dist"),
	("R2", "@r"),
	("D\'", "@d"),
	("Alleles", "@alleles"),
	("RegulomeDB", "@regdb"),
])

save()


# Print run time
duration=time.time() - start_time
print "\nRun time: "+str(duration)+" seconds\n"

# Remove temporary files
subprocess.call("rm pops_"+request+".txt", shell=True)
subprocess.call("rm *"+request+"*.vcf", shell=True)
subprocess.call("rm "+request+"*.out", shell=True)
