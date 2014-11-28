import csv,sqlite3,subprocess,sys

snp=sys.argv[1]
chr=sys.argv[2]
start=sys.argv[3]
stop=sys.argv[4]
request=sys.argv[5]
process=sys.argv[6]

print "Process "+str(int(process)+1)+" initialized."


# Set data directories
data_dir="/local/content/ldlink/data/"
snp_dir=data_dir+"snp141/snp141.db"
pop_dir=data_dir+"1000G/Phase3/samples/"
vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"
reg_dir=data_dir+"regulomedb/regulomedb.db"
tmp_dir="./tmp/"


# Get population ids
pop_list=open(tmp_dir+"pops_"+request+".txt").readlines()
ids=[]
for i in range(len(pop_list)):
	ids.append(pop_list[i].strip())

pop_ids=list(set(ids))



# Get VCF region
vcf_file=vcf_dir+chr+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snp="tabix -fh {0} {1}:{2}-{3} > {4}".format(vcf_file, chr, start, stop, tmp_dir+"snps_"+request+"_"+process+".vcf")
subprocess.call(tabix_snp, shell=True)
grep_remove_dups="grep -v -e END "+tmp_dir+"snps_"+request+"_"+process+".vcf > "+tmp_dir+"snps_no_dups_"+request+"_"+process+".vcf"
subprocess.call(grep_remove_dups, shell=True)


# Define function to calculate LD metrics
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
			D_prime=delta/min((A+C)*(A+B),(B+D)*(C+D))
		else:
			D_prime=delta/min((A+C)*(C+D),(A+B)*(B+D))
		
		# R2
		r2=(delta**2)/Ms
		
		# Find Correlated Alleles
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
				match=allele["0"]+"-"+allele_n["0"]+","+allele["1"]+"-"+allele_n["1"]
			else:
				match=allele["0"]+"-"+allele_n["1"]+","+allele["1"]+"-"+allele_n["0"]
			
		else:
			match=" - , - "
	
	else:
		D_prime="--"
		r2="--"
		match=" - , - "
	
	return [maf_q,maf_p,D_prime,r2,match]


# Open Connection to RegulomeDB
con=sqlite3.connect(reg_dir)
con.row_factory=sqlite3.Row
con.text_factory=str
curr=con.cursor()


# Open Connection to SNP141
con2=sqlite3.connect(snp_dir)
con2.row_factory=sqlite3.Row
con2.text_factory=str
curr2=con2.cursor()


# Import SNP VCF files
vcf=open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()
geno=vcf[len(vcf)-1].strip().split()
allele={"0":geno[3],"1":geno[4]}
chr=geno[0]
bp=geno[1]
rs=snp
al="("+geno[3]+"/"+geno[4]+")"


# Import Window around SNP
vcf=csv.reader(open(tmp_dir+"snps_no_dups_"+request+"_"+process+".vcf"),dialect="excel-tab")

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
	if geno_n[3] in ["A","C","G","T"] and geno_n[4] in ["A","C","G","T"]:
		allele_n={"0":geno_n[3],"1":geno_n[4]}
		hap={"00":0,"01":0,"10":0,"11":0}
		for i in index:
			hap0=geno[i][0]+geno_n[i][0]
			hap1=geno[i][2]+geno_n[i][2]
			hap[hap0]+=1
			hap[hap1]+=1
		
		maf_q,maf_p,D_prime,r2,match=LD_calcs(hap,allele,allele_n)
		
		bp_n=geno_n[1]
		rs_n=geno_n[2]
		al_n="("+geno_n[3]+"/"+geno_n[4]+")"
		dist=str(int(geno_n[1])-int(geno[1]))
		
		score="."
		funct="."
		if r2!="--":
			# Get RegulomeDB score
			t=("chr"+geno_n[0]+":"+geno_n[1],)
			curr.execute('SELECT * FROM regdb WHERE position=?', t)
			score=curr.fetchone()
			if score==None:
				score="."
			else:
				score=score[2]
			
			# Get dbSNP function
			id="99"+(13-len(rs_n))*"0"+rs_n.strip("rs")
			curr2.execute('SELECT * FROM snps WHERE id=?', (id,))
			snp_coord=curr2.fetchone()
			if snp_coord!=None:
				funct=snp_coord[4]
			else:
				funct="."
		
		temp=[rs,al,"chr"+chr+":"+bp,rs_n,al_n,"chr"+chr+":"+bp_n,dist,D_prime,r2,match,score,maf_q,maf_p,funct]
		out.append(temp)
			

output=open(tmp_dir+request+"_"+process+".out","w")
for i in range(len(out)):
	print >> output, "\t".join(str(j) for j in out[i])


output.close()