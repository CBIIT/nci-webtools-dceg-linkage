import yaml
import csv
import json
from pymongo import MongoClient
from bson import json_util, ObjectId
import boto3
import botocore
import subprocess
import sys
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars,connectMongoDBReadOnly
from LDutilites import get_config
from LDcommon import set_alleles,LD_calcs,get_dbsnp_coord


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
param_list = get_config()
data_dir = param_list['data_dir']
tmp_dir = param_list['tmp_dir']
genotypes_dir = param_list['genotypes_dir']
aws_info = param_list['aws_info']

export_s3_keys = retrieveAWSCredentials()

# Get population ids
pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
ids = []
for i in range(len(pop_list)):
    ids.append(pop_list[i].strip())

pop_ids = list(set(ids))

# Get VCF region
vcf_filePath = "%s/%s%s/%s" % (aws_info['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (chromosome))
vcf_query_snp_file = "s3://%s/%s" % (aws_info['bucket'], vcf_filePath)

checkS3File(aws_info, aws_info['bucket'], vcf_filePath)

# Connect to Mongo database
db = connectMongoDBReadOnly(True)

# Import SNP VCF files
vcf = open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()
h = 0
while vcf[h][0:2] == "##":
    h += 1
vcf = vcf[h+1:]
if len(vcf) > 1:
    for i in range(len(vcf)):
        # if vcf[i].strip().split()[2] == snp:
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
                    snp_coord = get_dbsnp_coord(db, chromosome, bp_n,genome_build)
                    if snp_coord is not None:
                        rs_n = "rs" + snp_coord['id']
                    else: 
                        rs_n = "."
                out.append([snp, rs_n, chromosome, bp_n, out_stats[0], out_stats[1], out_stats[2], out_stats[3]])

for line in out:
    print("\t".join([str(val) for val in line]))
