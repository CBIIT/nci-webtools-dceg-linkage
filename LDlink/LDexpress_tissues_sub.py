import yaml
import csv
import json
from pymongo import MongoClient
from bson import json_util, ObjectId
import subprocess
import sys
import requests

web = sys.argv[1]
request = sys.argv[2]
subprocess_id = sys.argv[3]
p_threshold = sys.argv[4]
tissues = sys.argv[5]

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

windowSNPs = []

with open(tmp_dir + 'express_ld_' + str(subprocess_id) + '_' + str(request) + '.txt') as snpsLDFile: 
    lines = snpsLDFile.readlines() 
    for line in lines: 
        windowSNPs.append(line.strip().split("\t"))

def getGTExTissueMongoDB(db, chromosome, position, tissues):
    if "gtex_tissue_eqtl" in db.list_collection_names():
        tissue_ids_query = []
        for tissue in tissues.split("+"):
            tissue_ids_query.append({
                "tissueSiteDetailId": tissue
            })
        pipeline = [
            {
                "$match": {
                    "tissueSiteDetailId": {
                        "$in": tissues.split("+")
                    },
                    "chr_b37": str(chromosome),
                    "variant_pos_b37": str(position)
                }
            },
            {
                "$lookup": {
                    "from": "gtex_tissues", 
                    "localField": "tissueSiteDetailId", 
                    "foreignField": "tissueSiteDetailId", 
                    "as": "tissue_info"
                }
            },
            {   
                '$unwind' : "$tissue_info" 
            },
            {
                "$lookup": {
                    "from": "gtex_genes", 
                    "localField": "gene_id", 
                    "foreignField": "gene_id", 
                    "as": "gene_info"
                }
            },
            {   
                '$unwind' : "$gene_info" 
            },
            {   
                "$project" : {
                    "gene_id": 1,
                    "tissueSiteDetailId": 1,
                    "slope": 1,
                    "pval_nominal": 1,
                    "tissueSiteDetail": "$tissue_info.tissueSiteDetail",
                    "gene_name": "$gene_info.gene_name"
                } 
            },
        ]

        documents = list(db.gtex_tissue_eqtl.aggregate(pipeline))

        tissues = {
            "singleTissueEqtl": documents
        }
        # json_output = json.dumps(tissues, default=json_util.default, sort_keys=True, indent=2)
        return tissues
    else:
        return None

def getGTExTissueAPI(snp, tissue_ids):
    PAYLOAD = {
        "format" : "json",
        "snpId": snp,
        "tissueSiteDetailId": ",".join(tissue_ids),
        "datasetId": "gtex_v8"
    }
    REQUEST_URL = "https://gtexportal.org/rest/v1/association/singleTissueEqtl"
    r = requests.get(REQUEST_URL, params=PAYLOAD)
    # print(json.loads(r.text))
    return (json.loads(r.text))

def get_tissues(web, windowSNPs, p_threshold, tissues):
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

    gtexQueryRequestCount = 0
    gtexQueryReturnCount = 0
    out = []
    for snp in windowSNPs:
        rs_n = snp[0]
        chromosome = snp[1]
        position = snp[2]
        r2 = snp[3]
        D_prime = snp[4]
        allele_1 = snp[5]
        allele_2 = snp[6]
        geno_n_chr_bp = "chr" + str(chromosome) + ":" + str(position)
        gtexQueryRequestCount += 1
        ###### RETRIEVE GTEX TISSUE INFO FROM API ######
        # (tissue_stats) = getGTExTissueAPI(rs_n, tissues.split("+"))
        ###### RETRIEVE GTEX TISSUE INFO FROM MONGODB ######
        (tissue_stats) = getGTExTissueMongoDB(db, chromosome, position, tissues)
        if tissue_stats != None and len(tissue_stats['singleTissueEqtl']) > 0:
            gtexQueryReturnCount += 1
            for tissue_obj in tissue_stats['singleTissueEqtl']:
                if (float(tissue_obj['pval_nominal']) if 'pval_nominal' in tissue_obj else float(tissue_obj['pValue'])) < float(p_threshold):
                    temp = [
                        rs_n, 
                        geno_n_chr_bp, 
                        r2, 
                        D_prime,
                        tissue_obj['gene_name'] if 'gene_name' in tissue_obj else tissue_obj['geneSymbol'] if 'geneSymbol' in tissue_obj else 'NA',
                        tissue_obj['gene_id'] if 'gene_id' in tissue_obj else tissue_obj['gencodeId'],
                        tissue_obj['tissueSiteDetail'] + "__" + tissue_obj['tissueSiteDetailId'] if 'tissueSiteDetail' in tissue_obj else tissue_obj['tissueSiteDetailId'],
                        allele_1,
                        allele_2,
                        tissue_obj['slope'] + "__" + rs_n if 'slope' in tissue_obj else tissue_obj['nes'],
                        tissue_obj['pval_nominal'] + "__" + rs_n if 'pval_nominal' in tissue_obj else tissue_obj['pValue']
                    ]
                    out.append(temp)
    # print("get_tissues out length", len(out))
    # print("# of gtex queries made (gtexQueryRequestCount)", gtexQueryRequestCount)
    # print("# of gtex queries returned (gtexQueryReturnCount)", gtexQueryReturnCount)
    return out

out = get_tissues(web, windowSNPs, p_threshold, tissues)

for line in out:
    print("\t".join([str(val) for val in line]))