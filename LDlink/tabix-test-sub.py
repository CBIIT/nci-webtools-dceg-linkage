import subprocess
import sys
import json

snp_coords_file = sys.argv[1]

tabix_calls = []
with open(snp_coords_file) as tabix_coords_file: 
    tabix_calls = json.loads(tabix_coords_file.readlines()[0])

tabix_results_pooled = []
# Construct Tabix call
for tabix_call in tabix_calls:
    vcf = [x.decode('utf-8') for x in subprocess.Popen(tabix_call, shell=True, stdout=subprocess.PIPE).stdout.readlines()]
    if len(vcf) >= 1:
        tabix_results_pooled.append(vcf[0])
print(json.dumps(tabix_results_pooled))