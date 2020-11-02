import sys
import os
import json
# import gzip
from timeit import default_timer as timer

def buildRecord(exportFile, gene_id, entrez_id):
    record = {
        "gene_id": gene_id,
        "entrez_id": entrez_id,
    } 
    exportFile.write(json.dumps(record) + '\n')
    
def main():
    print("start script")
    start = timer()
    filename = sys.argv[1]
    print("filename", filename)

    # if export file already exists, delete
    if (os.path.exists("tmp/export.genes.entrez.json")):
        print("export.genes.entrez.json already exists, deleting...")
        os.remove("tmp/export.genes.entrez.json")

    # if debug problematic out files already exist, delete
    if (os.path.exists("tmp/problematic.genes.entrez.txt")):
        print("problematic.genes.entrez.txt already exists, deleting...")
        os.remove("tmp/problematic.genes.entrez.txt")

    # print("parsing and inserting...")

    inserted = 0
    problematic = 0

    with open(filename, 'r') as f_in, open("tmp/problematic.genes.entrez.txt", 'a') as problematicFile, open("tmp/export.genes.entrez.json", 'a') as exportFile:
        # skip first row in file since its the header
        next(f_in)
        for line in f_in:
            row = line.strip().split('\t')
            if (len(row) >= 3):
                gene_id = row[0]
                entrez_id = row[1]
                if (len(gene_id) >= 1 and len(entrez_id) >= 1):
                    buildRecord(exportFile, gene_id, entrez_id)
                    inserted += 1
                else:
                    problematic += 1
                    row += ["Missing column(s)."]
                    # write to file
                    problematicFile.write(str(row) + '\n')
            else:
                problematic += 1
                row += ["Missing column(s)."]
                # write to file
                problematicFile.write(str(row) + '\n')
            
    print("finish export for", filename)
    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("# inserted", inserted)
    print("# problematic", problematic)
            

if __name__ == "__main__":
    main()