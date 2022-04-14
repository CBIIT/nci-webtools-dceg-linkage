from LDutilites import get_config
from LDcommon import genome_build_vars, retrieveAWSCredentials, connectMongoDBReadOnly, get_coords
import subprocess
from multiprocessing.dummy import Pool
import time
import numpy as np
import json
import sys

param_list = get_config()
data_dir = param_list['data_dir']
genotypes_dir = param_list['genotypes_dir']
aws_info = param_list['aws_info']
tmp_dir = param_list['tmp_dir']

num_subprocesses = 8

genome_build = 'grch37'
chromosome = "6"

tabix_s3_path = "%s/%s%s/%s" % (aws_info['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (chromosome))
tabix_s3_uri = "s3://%s/%s" % (aws_info['bucket'], tabix_s3_path)
export_s3_keys = retrieveAWSCredentials()
tabix_index_dir = "cd %s;" % (data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'])

snp_file = sys.argv[1]

print("Finding coordsinates for all SNPs in " + snp_file + "...")
db = connectMongoDBReadOnly(True)
snp_lst = open(snp_file).readlines()
snp_coords = []
for snp_raw in snp_lst:
    snp_rsid = snp_raw.lower().strip()
    print("snp_rsid", snp_rsid)
    dbsnp_coord = get_coords(db, snp_rsid)
    if dbsnp_coord != None:
        snp_coords.append(dbsnp_coord['chromosome'] + ":" + dbsnp_coord[genome_build_vars[genome_build]['position']] + "-" + dbsnp_coord[genome_build_vars[genome_build]['position']])

print("Found " + str(len(snp_coords)) + " coordinates in dbSNP " + genome_build + ".")

# collect output in parallel
def get_output(process):
    return process.communicate()[0].splitlines()

def constructTabixCall(tabix_coords):
    tabix_precall = [export_s3_keys, tabix_index_dir]
    tabix_flags = "-fD"
    tabix_post_condition = "| grep -v -e END"
    tabix_call = tabix_precall + ["tabix", tabix_flags, tabix_s3_uri, tabix_coords, tabix_post_condition]
    # print("tabix_call", tabix_call)
    return " ".join(tabix_call)

def tabixBatch():
    print("##### EXECUTE TABIX BATCH #####")
    tabix_coords = " ".join(snp_coords)    
    tabix_call = constructTabixCall(tabix_coords)
    vcf = [x.decode('utf-8') for x in subprocess.Popen(tabix_call, shell=True, stdout=subprocess.PIPE).stdout.readlines()]
    print("# vcf returned rows (without header) = ", len(vcf))

def tabixSingle():
    print("##### EXECUTE TABIX SINGLE #####")
    tabix_results_pooled = []
    # Construct Tabix call
    for snp_coord in snp_coords:
        tabix_call = constructTabixCall(snp_coord)        
        vcf = [x.decode('utf-8') for x in subprocess.Popen(tabix_call, shell=True, stdout=subprocess.PIPE).stdout.readlines()]
        if len(vcf) >= 1:
            tabix_results_pooled.append(vcf[0])
    print("# vcf returned rows (without header) = ", len(tabix_results_pooled))

def tabixSingleParallel():
    subprocess.call("rm " + tmp_dir + "tabix_snp_coords_*" + ".txt", shell=True)
    print("##### EXECUTE TABIX SINGLE PARALLEL #####")
    tabix_calls = []
    # Construct Tabix calls
    for snp_coord in snp_coords:
        tabix_calls.append(constructTabixCall(snp_coord))
        # tabix_calls.append(constructTabixCall(snp_coord).replace(" ", "__").replace(';', "@").replace('|', '##'))
    tabix_calls_subprocess_chunks = np.array_split(tabix_calls, num_subprocesses)
    tabix_subprocess_commands = []
    # write snp_coords to tmp files to be picked up by tabix subprocesses
    for subprocess_id in range(len(tabix_calls_subprocess_chunks)):
        if len(tabix_calls_subprocess_chunks[subprocess_id]) > 0:
            with open(tmp_dir + 'tabix_snp_coords_' + str(subprocess_id) + '.txt', 'w') as tabix_coords_file:
                tabix_coords_file.write(json.dumps(list(tabix_calls_subprocess_chunks[subprocess_id])))

    for subprocess_id in range(len(tabix_calls_subprocess_chunks)):
        if (len(list(tabix_calls_subprocess_chunks[subprocess_id])) > 0):
            tabix_subprocess_commands.append("python3 tabix-test-sub.py " + tmp_dir + 'tabix_snp_coords_' + str(subprocess_id) + '.txt')

    print("# of subprocesses kicked-off = ", len(tabix_subprocess_commands))
    tabix_subprocesses = [subprocess.Popen(command, shell=True, stdout=subprocess.PIPE) for command in tabix_subprocess_commands]
    # collect output in parallel
    pool = Pool(len(tabix_subprocesses))
    tabix_results_subsets = pool.map(get_output, tabix_subprocesses)
    pool.close()
    pool.join()
    # flatten pooled tabix results
    tabix_results_pooled = []
    for subprocess_id in range(len(tabix_results_subsets)):
        tabix_results_pooled += json.loads(tabix_results_subsets[subprocess_id][0])
    print("# vcf returned rows (without header) = ", len(tabix_results_pooled))        

def main():
    start_time = time.time()
    tabixBatch()
    print("--- %s seconds ---" % (time.time() - start_time))

    # start_time = time.time()
    # tabixSingle()
    # print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()
    tabixSingleParallel()
    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == "__main__":
    main()
