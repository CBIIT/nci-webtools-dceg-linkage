import sys
import os
import json
import gzip
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
from timeit import default_timer as timer

def insertRecord(db, record):
    gtex_tissue_eqtl = db['gtex_tissue_eqtl']
    gtex_tissue_eqtl.insert_one(record)

def buildRecord(db, header, row):
    record = dict(zip(header, row)) 
    # print("record", record)
    # insert into table
    insertRecord(db, record)

def convertGenomeAssembly(db, chr_b38, variant_pos_b38):
    gtex_snps = db['gtex_snps']
    record = gtex_snps.find_one({"chr": str(chr_b38), "variant_pos": str(variant_pos_b38)})
    if record is None:
        return None
    else:
        return [record['chr_b37'], record['variant_pos_b37']]
    
def main():
    print("start script")
    start = timer()
    filename = sys.argv[1]
    print("filename", filename)
    tissueSiteDetailId = os.path.basename(filename).split('.')[0]
    print("tissueSiteDetailId", tissueSiteDetailId)

    client = MongoClient()
    db = client['LDLink']

    # halt script if mongo collection gtex_snps does not exist
    if "gtex_snps" not in db.list_collection_names():
        print("gtex_snps mongo collection does not exist...")
        print("halting script...")
        exit()

    # if mongo collection already exists, drop
    if "gtex_tissue_eqtl" in db.list_collection_names():
        print("gtex_tissue_eqtl mongo collection already exists, dropping")
        db['gtex_tissue_eqtl'].drop()

    # if debug problematic out files already exist, delete
    if (os.path.exists("tmp/problematic." + tissueSiteDetailId + ".txt")):
        print("problematic." + tissueSiteDetailId + ".txt already exists, deleting...")
        os.remove("tmp/problematic." + tissueSiteDetailId + ".txt")
    if (os.path.exists("tmp/problematicNA." + tissueSiteDetailId + ".txt")):
        print("problematicNA." + tissueSiteDetailId + ".txt already exists, deleting...")
        os.remove("tmp/problematicNA." + tissueSiteDetailId + ".txt")

    # print("parsing and inserting...")

    inserted = 0
    problematicNA = 0
    problematic = 0
    # count = 0
    with gzip.open(filename, 'rb') as f_in:
        header = next(f_in).decode("utf-8").strip().split('\t') + ["chr_b37", "variant_pos_b37", "tissueSiteDetailId"]
        # print("header", header)
        for line in f_in:
            row = line.decode("utf-8").strip().split('\t')
            # print("row", row)
            chr_pos_b38 = row[0].split('_')
            if (chr_pos_b38[0] == "NA"):
                problematicNA += 1
                row += ["NA variant_id_b38 column."]
                # write to file
                with open("tmp/problematicNA." + tissueSiteDetailId + ".txt", 'a') as problematicNAFile:
                    problematicNAFile.write(str(row) + '\n')
            else:
                if ("." in chr_pos_b38[0]):
                    chr_b38 = chr_pos_b38[0].split(".")[1]
                else:
                    chr_b38 = chr_pos_b38[0]
                variant_pos_b38 = chr_pos_b38[1]
                # print(chr_pos_b38)
                # check if chromosome is 1-22, X, or Y and check if position is numeric
                if (((chr_b38.strip('chr').isnumeric() and int(chr_b38.strip('chr')) in range(1, 22 + 1)) or (chr_b38.strip('chr') in ["X", "Y"])) and variant_pos_b38.isnumeric()):
                    # create record and insert into mongo collection
                    if (len(row) is 12):
                        # convert b38 chr:pos to b37 via 'gtex_snps' collection in MongoDB
                        chr_pos_b37 = convertGenomeAssembly(db, chr_b38, variant_pos_b38)
                        if chr_pos_b37 is None:
                            problematic += 1
                            row += ["GRCh37 genomic positon not found in gtex_snps."]
                            with open("tmp/problematic." + tissueSiteDetailId + ".txt", 'a') as problematicFile:
                                problematicFile.write(str(row) + '\n')
                        else:
                            chr_b37 = chr_pos_b37[0]
                            variant_pos_b37 = chr_pos_b37[1]
                            buildRecord(db, header, row + [chr_b37, variant_pos_b37, tissueSiteDetailId])
                            inserted += 1
                    else:
                        problematic += 1
                        row += ["Missing column(s)."]
                        # write to file
                        with open("tmp/problematic." + tissueSiteDetailId + ".txt", 'a') as problematicFile:
                            problematicFile.write(str(row) + '\n')
                else:
                    # capture problematic rows
                    problematic += 1
                    row += ["Invalid variant_id_b38 column."]
                    # write to file
                    with open("tmp/problematic." + tissueSiteDetailId + ".txt", 'a') as problematicFile:
                        problematicFile.write(str(row) + '\n')
            # count += 1
            # if (count == 20):
            #     break
            
            
    # # create compound index on chr_b37, variant_pos_b37
    print("creating indexes...")
    db.gtex_tissue_eqtl.create_index([("tissueSiteDetailId", ASCENDING), ("chr_b37", ASCENDING), ("variant_pos_b37", ASCENDING)])

    print("finish script")
    end = timer()	
    print("TIME ELAPSED:", str(end - start) + "(s)")	
    print("# inserted", inserted)
    print("# problematic", problematic)
    print("# problematic b/c NA", problematicNA)

if __name__ == "__main__":
    main()