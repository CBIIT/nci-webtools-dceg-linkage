import sys
import os
import json
from timeit import default_timer as timer

# This script requires "Homo_sapiens.gene_info" from NCBI in same directory
# Download here: https://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz

def buildRecord(exportFile, gene_name, ncbi_id):
    record = {
        "gene_name": gene_name,
        "ncbi_id": ncbi_id,
    } 
    exportFile.write(json.dumps(record) + '\n')
    
def main():
    print("start script")
    start = timer()
    filename = sys.argv[1]
    print("filename", filename)

    # if export file already exists, delete
    if (os.path.exists("tmp/export.genes.NCBI.json")):
        print("export.genes.NCBI.json already exists, deleting...")
        os.remove("tmp/export.genes.NCBI.json")

    # if debug problematic out files already exist, delete
    if (os.path.exists("tmp/problematic.genes.NCBI.txt")):
        print("problematic.genes.NCBI.txt already exists, deleting...")
        os.remove("tmp/problematic.genes.NCBI.txt")

    # print("parsing and inserting...")

    inserted = 0
    problematic = 0

    with open(filename, 'r') as f_in, open("tmp/problematic.genes.NCBI.txt", 'a') as problematicFile, open("tmp/export.genes.NCBI.json", 'a') as exportFile:
        # skip first row in file since its the header
        next(f_in)
        for line in f_in:
            row = line.strip().split('\t')
            if len(row) == 16:
                ncbi_id = row[1]
                gene_name = [row[2]]
                synonyms = row[4].split('|') if row[4] != '-' else []
                gene_names = gene_name + synonyms
                print(ncbi_id, gene_names)
                if len(gene_names) > 0:
                    for name in gene_names:
                        buildRecord(exportFile, name, ncbi_id)
                        inserted += 1
                else:
                    problematic += 1
                    row += ["Missing gene_names."]
                    # write to file
                    problematicFile.write(str(row) + '\n')
            else:
                problematic += 1
                row += ["Missing/additional column(s)."]
                # write to file
                problematicFile.write(str(row) + '\n')
            
    print("finish export for", filename)
    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("# inserted", inserted)
    print("# problematic", problematic)
            

if __name__ == "__main__":
    main()