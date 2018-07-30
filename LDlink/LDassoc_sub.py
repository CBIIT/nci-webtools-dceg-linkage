import csv,sqlite3,subprocess,sys
import yaml

snp=sys.argv[1]
chr=sys.argv[2]
coords=sys.argv[3]
request=sys.argv[4]
process=sys.argv[5]


# Set data directories
# data_dir="/local/content/ldlink/data/"
# snp_dir=data_dir+"snp142/snp142_annot_2.db"
# pop_dir=data_dir+"1000G/Phase3/samples/"
# vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"
# reg_dir=data_dir+"regulomedb/regulomedb.db"

# Set data directories using config.yml
with open('config.yml', 'r') as f:
    config = yaml.load(f)
snp_dir=config['data']['snp_dir']
pop_dir=config['data']['pop_dir']
vcf_dir=config['data']['vcf_dir']
reg_dir=config['data']['reg_dir']

tmp_dir="./tmp/"


# Get population ids
pop_list=open(tmp_dir+"pops_"+request+".txt").readlines()
ids=[]
for i in range(len(pop_list)):
	ids.append(pop_list[i].strip())

pop_ids=list(set(ids))



# Get VCF region
vcf_file=vcf_dir+chr+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
coordinates=coords.replace("_"," ")
tabix_snp="tabix -fh {0} {1} | grep -v -e END".format(vcf_file, coordinates)
proc=subprocess.Popen(tabix_snp, shell=True, stdout=subprocess.PIPE)


# Define function to calculate LD metrics
def set_alleles(a1,a2):
	if len(a1)==1 and len(a2)==1:
		a1_n=a1
		a2_n=a2
	elif len(a1)==1 and len(a2)>1:
		a1_n="-"
		a2_n=a2[1:]
	elif len(a1)>1 and len(a2)==1:
		a1_n=a1[1:]
		a2_n="-"
	elif len(a1)>1 and len(a2)>1:
		a1_n=a1[1:]
		a2_n=a2[1:]
	return(a1_n,a2_n)

def LD_calcs(hap,allele,allele_n):
	# Extract haplotypes
	A=hap["00"]
	B=hap["01"]
	C=hap["10"]
	D=hap["11"]
	
	N=A+B+C+D
	delta=float(A*D-B*C)
	Ms=float((A+C)*(B+D)*(A+B)*(C+D))
	
	# Minor allele frequency
	maf_q=min((A+B)/float(N),(C+D)/float(N))
	maf_p=min((A+C)/float(N),(B+D)/float(N))
	
	if Ms!=0:
		
		# D prime
		if delta<0:
			D_prime=abs(delta/min((A+C)*(A+B),(B+D)*(C+D)))
		else:
			D_prime=abs(delta/min((A+C)*(C+D),(A+B)*(B+D)))
		
		# R2
		r2=(delta**2)/Ms
		
		# Find Correlated Alleles
		equiv="="
		if r2>0.1:
			
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
				match=allele_n["0"]+equiv+allele["0"]+","+allele_n["1"]+equiv+allele["1"]
			else:
				match=allele_n["1"]+equiv+allele["0"]+","+allele_n["0"]+equiv+allele["1"]
			
		else:
			match="NA"
	
		return [maf_q,maf_p,D_prime,r2,match]


# Open Connection to RegulomeDB
con=sqlite3.connect(reg_dir)
con.row_factory=sqlite3.Row
con.text_factory=str
curr=con.cursor()

def get_regDB(chr,pos):
	t=(pos,)
	curr.execute("SELECT * FROM "+chr+" WHERE position=?", t)
	a=curr.fetchone()
	if a==None:
		return "."
	else:
		return a[1]


# Open Connection to SNP142
con2=sqlite3.connect(snp_dir)
con2.row_factory=sqlite3.Row
con2.text_factory=str
curr2=con2.cursor()

def get_coords(rs):
	id=rs.strip("rs")
	t=(id,)
	curr2.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
	return curr2.fetchone()


# Import SNP VCF files
vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()
geno=vcf[0].strip().split()

new_alleles=set_alleles(geno[3],geno[4])
allele={"0":new_alleles[0],"1":new_alleles[1]}
chr=geno[0]
bp=geno[1]
rs=snp
al="("+new_alleles[0]+"/"+new_alleles[1]+")"


# Import Window around SNP
vcf=csv.reader(proc.stdout.readlines(), dialect="excel-tab")

# Loop past file information and find header
head=next(vcf,None)
while head[0][0:2]=="##":
	head=next(vcf,None)

# Create Index of Individuals in Population
index=[]
for i in range(9,len(head)):
	if head[i] in pop_ids:
		index.append(i)

# Loop through SNPs
out=[]
for geno_n in vcf:
	if "," not in geno_n[3] and "," not in geno_n[4]:
		new_alleles_n=set_alleles(geno_n[3],geno_n[4])
		allele_n={"0":new_alleles_n[0],"1":new_alleles_n[1]}
		hap={"00":0,"01":0,"10":0,"11":0}
		for i in index:
			hap0=geno[i][0]+geno_n[i][0]
			if hap0 in hap:
				hap[hap0]+=1
			
			if len(geno[i])==3 and len(geno_n[i])==3:
				hap1=geno[i][2]+geno_n[i][2]
				if hap1 in hap:	
					hap[hap1]+=1
		
		out_stats=LD_calcs(hap,allele,allele_n)
		if out_stats!=None:
			maf_q,maf_p,D_prime,r2,match=out_stats
		
			bp_n=geno_n[1]
			rs_n=geno_n[2]
			al_n="("+new_alleles_n[0]+"/"+new_alleles_n[1]+")"
			dist=str(int(geno_n[1])-int(geno[1]))
			
			
			# Get RegulomeDB score
			score=get_regDB("chr"+geno_n[0],geno_n[1])
			
			# Get dbSNP function
			if rs_n[0:2]=="rs":
				snp_coord=get_coords(rs_n)
				
				if snp_coord!=None:
					funct=snp_coord[3]
				else:
					funct="."
			else:
				funct="."
			
			temp=[rs,al,"chr"+chr+":"+bp,rs_n,al_n,"chr"+chr+":"+bp_n,dist,D_prime,r2,match,score,maf_q,maf_p,funct]
			out.append(temp)


for i in range(len(out)):
	print "\t".join(str(j) for j in out[i])


# Close SQLite connections
curr.close()
con.close()
curr2.close()
con2.close()