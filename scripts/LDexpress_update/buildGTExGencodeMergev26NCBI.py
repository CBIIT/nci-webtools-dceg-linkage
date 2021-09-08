import sys
import os
import json
from timeit import default_timer as timer

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId

# This script requires Gencode v26-v35 gene_id and gene_name mapping from buildGTExGencodeMergev26v35.py
# This script requires ncbi_id and gene_name mapping from buildGTExGencode.NCBI.py

def buildRecord(exportFile, gene_id_v26, gene_name_v26, ncbi_id):
    record = {
        "gene_id_v26": gene_id_v26,
        "gene_name_v26": gene_name_v26,
        "ncbi_id": ncbi_id
    } 
    exportFile.write(json.dumps(record) + '\n')
    
def main():
    print("start script")
    start = timer()
    filename_v26v35 = sys.argv[1]
    print("filename_v26v35", filename_v26v35)

    client = MongoClient()
    db = client['LDLink']

    # if export file already exists, delete
    if (os.path.exists("tmp/export.genes.merge.json")):
        print("export.genes.merge.json already exists, deleting...")
        os.remove("tmp/export.genes.merge.json")

    # if debug problematic out files already exist, delete
    if (os.path.exists("tmp/problematic.genes.merge.txt")):
        print("problematic.genes.merge.txt already exists, deleting...")
        os.remove("tmp/problematic.genes.merge.txt")

    # print("parsing and inserting...")

    inserted = 0
    problematic = 0
    notFound = 0

    with open(filename_v26v35, 'r') as f_v26v35_in, open("tmp/problematic.genes.merge.txt", 'a') as problematicFile, open("tmp/export.genes.merge.json", 'a') as exportFile:
        for v26v35_line in f_v26v35_in:
            v26v35_json = json.loads(v26v35_line)
            v26_gene_id = v26v35_json['gene_id_v26']
            v26_gene_name = v26v35_json['gene_name_v26']
            ncbi_query_v26 = db.gtex_genes_ncbi.find_one({"gene_name": v26_gene_name})
            print("ncbi_query_v26", ncbi_query_v26)
            if ncbi_query_v26 is not None:
                inserted += 1
                buildRecord(exportFile, v26_gene_id, v26_gene_name, ncbi_query_v26['ncbi_id'])
            else:
                v35_gene_name = v26v35_json['gene_name_v35']
                if v35_gene_name != "NA":
                    ncbi_query_v35 = db.gtex_genes_ncbi.find_one({"gene_name": v35_gene_name})
                    if ncbi_query_v35 is not None:
                        inserted += 1
                        buildRecord(exportFile, v26_gene_id, v26_gene_name, ncbi_query_v35['ncbi_id'])
                    else:
                        notFound += 1
                        buildRecord(exportFile, v26_gene_id, v26_gene_name, "NA")
                else:
                    notFound += 1
                    buildRecord(exportFile, v26_gene_id, v26_gene_name, "NA")
            

    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("# inserted", inserted)
    print("# notFound", notFound)
            

if __name__ == "__main__":
    main()