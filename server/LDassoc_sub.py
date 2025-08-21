import csv
import logging
import subprocess
import sys
import time
from datetime import datetime
from LDcommon import checkS3File, retrieveAWSCredentials, genome_build_vars, connectMongoDBReadOnly
from LDcommon import set_alleles, get_dbsnp_coord, get_coords, get_regDB, get_forgeDB
from LDutilites import get_config

# Configure module logger
param_list = get_config()
log_level = getattr(logging, param_list["log_level"].upper(), logging.DEBUG)
logger = logging.getLogger("ldassoc_sub")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[ldassoc_sub] [%(asctime)s] [%(levelname)s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)

snp = sys.argv[1]
chr = sys.argv[2]
coords = sys.argv[3]
request = sys.argv[4]
genome_build = sys.argv[5]
process = sys.argv[6]

# Log function entry and parameters
logger.info(
    f'ldassoc_sub params {{"snp": "{snp}", "chr": "{chr}", "request": "{request}", "genome_build": "{genome_build}", "process": "{process}", "coords_count": {len(coords.split("_"))}}}'
)
logger.debug("Starting LDassoc_sub subprocess")

start_time = time.time()

# Set data directories using config.yml
param_list = get_config()
data_dir = param_list["data_dir"]
tmp_dir = param_list["tmp_dir"]
genotypes_dir = param_list["genotypes_dir"]
aws_info = param_list["aws_info"]

logger.debug(f"Loaded configuration - data_dir: {data_dir}, tmp_dir: {tmp_dir}")

export_s3_keys = retrieveAWSCredentials()

# Get population ids
try:
    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
    ids = []
    for i in range(len(pop_list)):
        ids.append(pop_list[i].strip())

    pop_ids = list(set(ids))
    logger.debug(f"Loaded {len(pop_ids)} population IDs from {tmp_dir}pops_{request}.txt")
except FileNotFoundError as e:
    logger.error(f"Population file not found: {tmp_dir}pops_{request}.txt - {str(e)}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error loading population IDs: {str(e)}")
    sys.exit(1)

# Get VCF region
vcf_filePath = "%s/%s%s/%s" % (
    aws_info["data_subfolder"],
    genotypes_dir,
    genome_build_vars[genome_build]["1000G_dir"],
    genome_build_vars[genome_build]["1000G_file"] % (chr),
)
vcf_query_snp_file = "s3://%s/%s" % (aws_info["bucket"], vcf_filePath)

logger.debug(f"Checking S3 VCF file: {vcf_query_snp_file}")
try:
    checkS3File(aws_info, aws_info["bucket"], vcf_filePath)
    logger.debug("S3 VCF file check completed successfully")
except Exception as e:
    logger.error(f"S3 file check failed for {vcf_query_snp_file}: {str(e)}")
    sys.exit(1)

coordinates = coords.replace("_", " ")
logger.debug(
    f"Processing coordinates: {coordinates[:100]}..."
    if len(coordinates) > 100
    else f"Processing coordinates: {coordinates}"
)


def LD_calcs(hap, allele, allele_n):
    # Extract haplotypes
    A = hap["00"]
    B = hap["01"]
    C = hap["10"]
    D = hap["11"]

    N = A + B + C + D
    delta = float(A * D - B * C)
    Ms = float((A + C) * (B + D) * (A + B) * (C + D))

    # Minor allele frequency
    maf_q = min((A + B) / float(N), (C + D) / float(N))
    maf_p = min((A + C) / float(N), (B + D) / float(N))

    if Ms != 0:

        # D prime
        if delta < 0:
            D_prime = abs(delta / min((A + C) * (A + B), (B + D) * (C + D)))
        else:
            D_prime = abs(delta / min((A + C) * (C + D), (A + B) * (B + D)))

        # R2
        r2 = (delta**2) / Ms

        equiv = "="

        # Find Correlated Alleles
        if str(r2) != "NA" and float(r2) > 0.1:
            Ac = hap[sorted(hap)[0]]
            Bc = hap[sorted(hap)[1]]
            Cc = hap[sorted(hap)[2]]
            Dc = hap[sorted(hap)[3]]

            if (Ac * Dc) / max((Bc * Cc), 0.01) > 1:
                match = (
                    allele_n[sorted(hap)[0][0]]
                    + equiv
                    + allele[sorted(hap)[0][1]]
                    + ","
                    + allele_n[sorted(hap)[3][0]]
                    + equiv
                    + allele[sorted(hap)[3][1]]
                )
            else:
                match = (
                    allele_n[sorted(hap)[1][0]]
                    + equiv
                    + allele[sorted(hap)[1][1]]
                    + ","
                    + allele_n[sorted(hap)[2][0]]
                    + equiv
                    + allele[sorted(hap)[2][1]]
                )
        else:
            match = "NA"

        return [maf_q, maf_p, D_prime, r2, match]


# Connect to Mongo snp database
logger.debug("Connecting to MongoDB for SNP data")
try:
    db = connectMongoDBReadOnly(True)
    logger.debug("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    sys.exit(1)


# Import SNP VCF files
logger.debug(f"Reading VCF file: {tmp_dir}snp_no_dups_{request}.vcf")
try:
    vcf = open(tmp_dir + "snp_no_dups_" + request + ".vcf").readlines()
    h = 0
    while vcf[h][0:2] == "##":
        h += 1
    vcf = vcf[h + 1 :]

    geno = vcf[0].strip().split()
    geno[0] = geno[0].lstrip("chr")
    logger.debug(f"Successfully loaded VCF file with {len(vcf)} records")
except FileNotFoundError as e:
    logger.error(f"VCF file not found: {tmp_dir}snp_no_dups_{request}.vcf - {str(e)}")
    sys.exit(1)
except (IndexError, ValueError) as e:
    logger.error(f"Error parsing VCF file format: {str(e)}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error reading VCF file: {str(e)}")
    sys.exit(1)

new_alleles = set_alleles(geno[3], geno[4])
allele = {"0": new_alleles[0], "1": new_alleles[1]}
chr = geno[0]
bp = geno[1]
rs = snp
al = "(" + new_alleles[0] + "/" + new_alleles[1] + ")"

# Import Window around SNP
tabix_snp = export_s3_keys + " cd {2}; tabix -fhD {0} {1} | grep -v -e END".format(
    vcf_query_snp_file, coordinates, data_dir + genotypes_dir + genome_build_vars[genome_build]["1000G_dir"]
)
logger.debug(f"Executing tabix command for coordinate window")
try:
    process = subprocess.Popen(tabix_snp, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        logger.error(f"Tabix command failed with return code {process.returncode}: {stderr.decode('utf-8')}")
        sys.exit(1)

    vcf = csv.reader([x.decode("utf-8") for x in stdout.splitlines()], dialect="excel-tab")
    logger.debug("Successfully executed tabix command and loaded VCF data")
except Exception as e:
    logger.error(f"Error executing tabix command: {str(e)}")
    sys.exit(1)

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
    geno_n[0] = geno_n[0].lstrip("chr")
    if "," not in geno_n[3] and "," not in geno_n[4]:
        new_alleles_n = set_alleles(geno_n[3], geno_n[4])
        allele_n = {"0": new_alleles_n[0], "1": new_alleles_n[1]}
        hap = {"00": 0, "01": 0, "10": 0, "11": 0}
        for i in index:
            hap0 = geno[i][0] + geno_n[i][0]
            if hap0 in hap:
                hap[hap0] += 1

            if len(geno[i]) == 3 and len(geno_n[i]) == 3:
                hap1 = geno[i][2] + geno_n[i][2]
                if hap1 in hap:
                    hap[hap1] += 1

        out_stats = LD_calcs(hap, allele, allele_n)
        if out_stats != None:
            maf_q, maf_p, D_prime, r2, match = out_stats

            chr_n = geno_n[0]
            bp_n = geno_n[1]
            rs_n = geno_n[2]
            al_n = "(" + new_alleles_n[0] + "/" + new_alleles_n[1] + ")"
            dist = str(int(geno_n[1]) - int(geno[1]))

            # Get RegulomeDB score
            score = get_regDB(db, genome_build, "chr" + geno_n[0], geno_n[1])

            # Get dbSNP function
            if rs_n[0:2] == "rs":
                snp_coord = get_coords(db, rs_n)

                if snp_coord != None:
                    funct = snp_coord["function"]
                else:
                    funct = "."
            elif rs_n[0:2] != "rs":
                snp_coord = get_dbsnp_coord(db, chr_n, bp_n, genome_build)

                if snp_coord != None:
                    funct = snp_coord["function"]
                    # Retrieve rsid from dbsnp if missing from 1000G data
                    if len(snp_coord["id"]) > 0:
                        rs_n = "rs" + snp_coord["id"]
                    else:
                        rs_n = "."
                else:
                    funct = "."
                    rs_n = "."
            else:
                funct = "."
            score_forage = get_forgeDB(db, rs_n)
            temp = [
                rs,
                al,
                "chr" + chr + ":" + bp,
                rs_n,
                al_n,
                "chr" + chr_n + ":" + bp_n,
                dist,
                D_prime,
                r2,
                match,
                score_forage,
                score,
                maf_q,
                maf_p,
                funct,
            ]
            out.append(temp)

# Calculate and log execution time
execution_time = round(time.time() - start_time, 2)
logger.debug(f"LDassoc_sub process completed ({execution_time}s) - processed {len(out)} variants")

for i in range(len(out)):
    print("\t".join(str(j) for j in out[i]))
