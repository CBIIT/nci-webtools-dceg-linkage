import sys
import os
import json
# import gzip
from timeit import default_timer as timer

def buildRecord(exportFile, gene_id, gene_name):
    record = {
        "gene_id": gene_id,
        "gene_name": gene_name,
    } 
    exportFile.write(json.dumps(record) + '\n')
    
def main():
    print("start script")
    start = timer()
    filename = sys.argv[1]
    print("filename", filename)

    # if export file already exists, delete
    if (os.path.exists("tmp/export.genes.json")):
        print("export.genes.json already exists, deleting...")
        os.remove("tmp/export.genes.json")

    # if debug problematic out files already exist, delete
    if (os.path.exists("tmp/problematic.genes.txt")):
        print("problematic.genes.txt already exists, deleting...")
        os.remove("tmp/problematic.genes.txt")

    # print("parsing and inserting...")

    inserted = 0
    problematic = 0
    # count = 0
    # with gzip.open(filename, 'rb') as f_in, open("tmp/problematic.genes.txt", 'a') as problematicFile, open("tmp/export.genes.json", 'a') as exportFile:
    with open(filename, 'r') as f_in, open("tmp/problematic.genes.txt", 'a') as problematicFile, open("tmp/export.genes.json", 'a') as exportFile:
        # skip first 6 rows in file since they are metadata info
        for _ in range(6):
            next(f_in)
        for line in f_in:
            # print(line)
            # row = line.decode("utf-8").strip().split('\t')
            row = line.strip().split('\t')
            if (len(row) >= 3):
                if (row[2] == "gene"):
                    details = row[8].split(";")
                    idCol = details[1].strip().split("=")
                    if (details[3].strip().split("=")[0] == "gene_status"):
                        nameCol = details[4].strip().split("=")
                    else:
                        nameCol = details[3].strip().split("=")
                    if (len(details) >= 3 and idCol[0] == "gene_id" and nameCol[0] == "gene_name"):
                        # print("row", row)
                        # print("idCol", idCol)
                        # print("nameCol", nameCol)
                        # buildRecord(exportFile, idCol[1].strip('\"'), nameCol[1].strip('\"'))
                        buildRecord(exportFile, idCol[1].split(".")[0], nameCol[1])
                        inserted += 1
                        # count += 1
                        # if count == 5:
                        #     break
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