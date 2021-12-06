import yaml
import csv
import json
from pymongo import MongoClient
from bson import json_util, ObjectId
import boto3
import botocore
import subprocess
import sys
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars

web = sys.argv[1]
snp = sys.argv[2]
chromosome = sys.argv[3]
start = sys.argv[4]
stop = sys.argv[5]
request = sys.argv[6]
subprocess_id = sys.argv[7]
r2_d = sys.argv[8]
r2_d_threshold = sys.argv[9]
genome_build = sys.argv[10]

# Set data directories using config.yml
with open('config.yml', 'r') as yml_file:
    config = yaml.load(yml_file)
env = config['env']
api_mongo_addr = config['api']['api_mongo_addr']
data_dir = config['data']['data_dir']
tmp_dir = config['data']['tmp_dir']
genotypes_dir = config['data']['genotypes_dir']
# reg_dir = config['data']['reg_dir']
aws_info = config['aws']
mongo_username = config['database']['mongo_user_readonly']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']

export_s3_keys = retrieveAWSCredentials()

# Get population ids
pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
ids = []
for i in range(len(pop_list)):
    ids.append(pop_list[i].strip())

pop_ids = list(set(ids))

# Get VCF region
vcf_filePath = "%s/%s%s/%s" % (config['aws']['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (chromosome))
vcf_query_snp_file = "s3://%s/%s" % (config['aws']['bucket'], vcf_filePath)

checkS3File(aws_info, config['aws']['bucket'], vcf_filePath)

# Define function to calculate LD metrics
def set_alleles(a1, a2):
    if len(a1) >= 1:
        a1_n = a1
    else:
        a1_n = "-"
    if len(a2) >= 1:
        a2_n = a2
    else:
        a2_n = "_"
    return(a1_n, a2_n)

def LD_calcs(hap, allele_n):
    # Extract haplotypes
    A = hap["00"]
    B = hap["01"]
    C = hap["10"]
    D = hap["11"]
    N = A + B + C + D
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
        # Non-effect and Effect Alleles and their Allele Frequencies
        allele1 = str(allele_n["0"])
        allele1_freq = str(round(float(A + C) / N, 3)) if N > float(A + C) else "NA"

        allele2 = str(allele_n["1"])
        allele2_freq = str(round(float(B + D) / N, 3)) if N > float(B + D) else "NA"
        return [r2, D_prime, "=".join([allele1, allele1_freq]), "=".join([allele2, allele2_freq])]


# Connect to Mongo database
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

def get_dbsnp_coord(db, chromosome, position):
    query_results = db.dbsnp.find_one({"chromosome": str(chromosome), genome_build_vars[genome_build]['position']: str(position)})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

# Import SNP VCF files
vcf = open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()

if len(vcf) > 1:
    for i in range(len(vcf)):
        if vcf[i].strip().split()[2] == snp:
            geno = vcf[i].strip().split()
            geno[0] = geno[0].lstrip('chr')
            
else:
    geno = vcf[0].strip().split()
    geno[0] = geno[0].lstrip('chr')

# Import Window around SNP
tabix_snp = export_s3_keys + " cd {4}; tabix -fhD {0} {1}:{2}-{3} | grep -v -e END".format(vcf_query_snp_file, genome_build_vars[genome_build]['1000G_chr_prefix'] + chromosome, start, stop, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])
vcf = csv.reader([x.decode('utf-8') for x in subprocess.Popen(tabix_snp, shell=True, stdout=subprocess.PIPE).stdout.readlines()], dialect="excel-tab")

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

        out_stats = LD_calcs(hap, allele_n)
        if out_stats != None:
            if ((r2_d == "r2" and out_stats[0] >= float(r2_d_threshold)) or (r2_d == "d" and out_stats[1] >= float(r2_d_threshold))):
                bp_n = geno_n[1]
                if geno_n[2][0:2] == "rs":
                    rs_n = geno_n[2]
                else: 
                    snp_coord = get_dbsnp_coord(db, chromosome, bp_n)
                    if snp_coord is not None:
                        rs_n = "rs" + snp_coord['id']
                    else: 
                        rs_n = "."
                out.append([snp, rs_n, chromosome, bp_n, out_stats[0], out_stats[1], out_stats[2], out_stats[3]])

for line in out:
    print("\t".join([str(val) for val in line]))
