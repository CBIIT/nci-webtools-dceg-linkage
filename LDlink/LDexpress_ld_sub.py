import yaml
import csv
import json
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys

web = sys.argv[1]
snp = sys.argv[2]
chromosome = sys.argv[3]
start = sys.argv[4]
stop = sys.argv[5]
request = sys.argv[6]
subprocess_id = sys.argv[7]
r2_d = sys.argv[8]
r2_d_threshold = sys.argv[9]


# Set data directories using config.yml
with open('config.yml', 'r') as f:
    config = yaml.load(f)
env = config['env']
api_mongo_addr = config['api']['api_mongo_addr']
pop_dir = config['data']['pop_dir']
vcf_dir = config['data']['vcf_dir']
reg_dir = config['data']['reg_dir']
mongo_username = config['database']['mongo_user_readonly']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']

tmp_dir = "./tmp/"

# Get population ids
pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
ids = []
for i in range(len(pop_list)):
    ids.append(pop_list[i].strip())

pop_ids = list(set(ids))

# Get VCF region
vcf_file = vcf_dir + chromosome + ".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
tabix_snp = "tabix -fh {0} {1}:{2}-{3} | grep -v -e END".format(vcf_file, chromosome, start, stop)
proc = subprocess.Popen(tabix_snp, shell=True, stdout=subprocess.PIPE)

# Define function to calculate LD metrics
def set_alleles(a1, a2):
    if len(a1) == 1 and len(a2) == 1:
        a1_n = a1
        a2_n = a2
    elif len(a1) == 1 and len(a2) > 1:
        a1_n = "-"
        a2_n = a2[1:]
    elif len(a1) > 1 and len(a2) == 1:
        a1_n = a1[1:]
        a2_n = "-"
    elif len(a1) > 1 and len(a2) > 1:
        a1_n = a1[1:]
        a2_n = a2[1:]
    return(a1_n, a2_n)

def LD_calcs(hap, allele, allele_n):
    # Extract haplotypes
    A = hap["00"]
    B = hap["01"]
    C = hap["10"]
    D = hap["11"]
    delta = float(A*D-B*C)
    Ms = float((A+C)*(B+D)*(A+B)*(C+D))
    if Ms != 0:
        # D prime
        if delta < 0:
            D_prime = abs(delta/min((A+C)*(A+B), (B+D)*(C+D)))
        else:
            D_prime = abs(delta/min((A+C)*(C+D), (A+B)*(B+D)))
        # R2
        r2 = (delta**2)/Ms
        return [r2, D_prime]


# Connect to Mongo snp database
if env == 'local':
    mongo_host = api_mongo_addr
else: 
    mongo_host = 'localhost'
if web == "True":
    client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
else:
    if env == 'local':
        client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host+'/admin', mongo_port)
    else:
        client = MongoClient('localhost', mongo_port)
db = client["LDLink"]

def get_coords(db, rsid):
    rsid = rsid.strip("rs")
    query_results = db.dbsnp151.find_one({"id": rsid})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

# Import SNP VCF files
vcf = open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()

if len(vcf) > 1:
    for i in range(len(vcf)):
        if vcf[i].strip().split()[2] == snp:
            geno = vcf[i].strip().split()
else:
    geno = vcf[0].strip().split()

new_alleles = set_alleles(geno[3], geno[4])
allele = {"0": new_alleles[0], "1": new_alleles[1]}
chr = geno[0]
bp = geno[1]
rs = snp
al = "("+new_alleles[0]+"/"+new_alleles[1]+")"


# Import Window around SNP
vcf = csv.reader([x.decode('utf-8') for x in proc.stdout.readlines()], dialect="excel-tab")

# Loop past file information and find header
head = next(vcf, None)
while head[0][0:2] == "##":
    head = next(vcf, None)

# Create Index of Individuals in Population
index = []
for i in range(9, len(head)):
    if head[i] in pop_ids:
        index.append(i)

# Loop through SNPs
out = []
for geno_n in vcf:
    if "," not in geno_n[3] and "," not in geno_n[4]:
        new_alleles_n = set_alleles(geno_n[3], geno_n[4])
        allele_n = {"0": new_alleles_n[0], "1": new_alleles_n[1]}
        hap = {"00": 0, "01": 0, "10": 0, "11": 0}
        for i in index:
            hap0 = geno[i][0]+geno_n[i][0]
            if hap0 in hap:
                hap[hap0] += 1

            if len(geno[i]) == 3 and len(geno_n[i]) == 3:
                hap1 = geno[i][2]+geno_n[i][2]
                if hap1 in hap:
                    hap[hap1] += 1

        out_stats = LD_calcs(hap, allele, allele_n)
        if out_stats != None:
            if ((r2_d == "r2" and out_stats[0] >= float(r2_d_threshold)) or (r2_d == "d" and out_stats[1] >= float(r2_d_threshold))):
                bp_n = geno_n[1]
                rs_n = geno_n[2]
                out.append([rs_n, chromosome, bp_n, out_stats[0], out_stats[1]])

for line in out:
    print("\t".join([str(val) for val in line]))
