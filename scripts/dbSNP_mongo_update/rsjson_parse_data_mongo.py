# LAST UPDATED 07/16/2021 FOR dbSNP b155

import sys
import json
import bz2
import shutil
import time
import os.path
import re
start_time = time.time()  # measure script's run time


# find merged rs numbers
def getRSIDs(primary_refsnp):
    rsids = []
    # append rsid reference
    ref_id = primary_refsnp['refsnp_id']
    rsids.append(ref_id)
    # append rsid merges
    for i in primary_refsnp['dbsnp1_merges']:
        rsids.append(i['merged_rsid'])
    return rsids, ref_id


# find chromosome
def getChromosome(file_basename):
    try:
        if file_basename.split('.')[0].split('-')[1] == "merged":
            chromosome = "merged"
        else:
            chromosome = file_basename.split('.')[0].split('-')[1].split('chr')[1] or "TEST"
    except IndexError:
        chromosome = "TEST"
    return chromosome   


# find sequence change annotations
def getAnnotations(primary_refsnp):
    annotations = []
    for i in primary_refsnp['allele_annotations']:
        try:
            a = i['assembly_annotation'][0]['genes'][0]['rnas'][0]['protein']['sequence_ontology'][0]['name']
            # clean up text by trimming off '_variant'
            annotations.append(a.replace('_variant', ''))
        except:
            continue
    return ','.join(list(set(annotations))) if len(list(set(annotations))) > 0 else "NA"


# find variant type
def getVariantType(primary_refsnp):
    variant_type = 'NA'
    try:
        variant_type = primary_refsnp['variant_type']
    except:
        pass
    return variant_type


# find GRCh37 and GRCh38 genomic positions
def getPositions(primary_refsnp):
    position_hgvs_grch37 = "NA"
    position_hgvs_grch38 = "NA"
    
    for i in primary_refsnp['placements_with_allele']:
        if len(i['placement_annot']['seq_id_traits_by_assembly']) > 0:
            assembly = i['placement_annot']['seq_id_traits_by_assembly'][0]['assembly_name']
            is_chrom = i['placement_annot']['seq_id_traits_by_assembly'][0]['is_chromosome']
            pos = i['alleles'][0]['allele']['spdi']['position']

            ######## parse position from GRCh37.p13
            if assembly == "GRCh37.p13" and is_chrom == True: 
                try:
                    position_hgvs_grch37 = re.sub(r"\D", "", str(i['alleles'][0]['hgvs'].split(':')[1].split('.')[1].split("_")[0]))
                except:
                    position_hgvs_grch37 = "NA"

            ######## parse position from GRCh38.p13
            if is_chrom == True and assembly == "GRCh38.p13":
                try:
                    position_hgvs_grch38 = re.sub(r"\D", "", str(i['alleles'][0]['hgvs'].split(':')[1].split('.')[1].split("_")[0]))
                except:
                    position_hgvs_grch38 = "NA"

    positions = {
        "position_hgvs_grch37": position_hgvs_grch37,
        "position_hgvs_grch38": position_hgvs_grch38,
    }
    return positions


# write output from parsing json files
def createRecord(rsids, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file, error_file):
    if len(rsids) > 0:
        for rsid in rsids:
            # check if fields are all populated
            if len(rsid) > 0 and \
                len(chromosome) > 0 and \
                (positions['position_hgvs_grch37'] != "NA" or positions['position_hgvs_grch38'] != "NA") and \
                len(annotations) > 0 and \
                len(variant_type) > 0:
                writeJSON(rsid, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file)
            else:
                error_data = {
                    "id": rsid,
                    "chromosome": chromosome,
                    "position_hgvs_grch37": positions['position_hgvs_grch37'],
                    "position_hgvs_grch38": positions['position_hgvs_grch38'],
                    "function": annotations,
                    "type": variant_type,
                    "ref_id": ref_id
                }
                writeError(out_path, tmp_path, error_file, "Missing data fields", error_data)

# find merged rs numbers
def getRSID(primary_refsnp):
    rsid = primary_refsnp['refsnp_id']
    return rsid

# find sequence change annotations
def getMerges(primary_refsnp):
    merges = primary_refsnp['merged_into']
    return merges


def writeJSON(rsid, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file):
    record = {
        "id": rsid,
        "chromosome": chromosome,
        "position_grch37": positions['position_hgvs_grch37'],
        "position_grch38": positions['position_hgvs_grch38'],
        "function": annotations,
        "type": variant_type,
        "ref_id": ref_id
    }
    with open(os.path.join(out_path, result_file) if tmp_path == None else os.path.join(tmp_path, result_file), 'a') as outfile:
        json.dump(record, outfile)
        outfile.write('\n')

def writeJSONMerged(rsid, merges, tmp_path, out_path, result_file):
    record = {
        "id": rsid,
        "merged_into": merges
    }
    with open(os.path.join(out_path, result_file) if tmp_path == None else os.path.join(tmp_path, result_file), 'a') as outfile:
        json.dump(record, outfile)
        outfile.write('\n')


def writeError(out_path, tmp_path, error_file, error_msg, data):
    with open(os.path.join(out_path, error_file) if tmp_path == None else os.path.join(tmp_path, error_file), 'a') as errorfile:
        json.dump({
            "error_msg": error_msg,
            "data": data
        }, errorfile)
        errorfile.write('\n')


def main():
    file_path = sys.argv[1]
    out_path = sys.argv[2]
    tmp_path = sys.argv[3] if len(sys.argv) > 3 else None

    print("Starting to parse " + file_path + "...")

    print("file_path", file_path)
    print("out_path", out_path)
    print("tmp_path", tmp_path)

    file_basename = os.path.basename(file_path)
    chromosome = getChromosome(file_basename)

    # process "merged" variants data file
    if chromosome == "merged":
        result_file = 'merged_filtered.json'
        error_file =  'merged_filtered.ERROR.json'

        # copy file to hpc tmp scratch space if specified
        if tmp_path != None:
            print("Copying data to tmp scratch space...")
            shutil.copy(file_path, tmp_path)

        print("Begin parsing...")
        with bz2.open(file_path if tmp_path == None else os.path.join(tmp_path, file_basename), 'rb') as f_in:
            # limit lines read per file
            cnt = 0
            for line in f_in:
                try:
                    rs_obj = json.loads(line.decode('utf-8'))
                    try:
                        if 'merged_snapshot_data' in rs_obj:
                            # print("rs_obj", rs_obj)
                            rsid = getRSID(rs_obj)
                            merges = getMerges(rs_obj['merged_snapshot_data'])
                            writeJSONMerged(rsid, merges, tmp_path, out_path, result_file)
                            cnt = cnt + 1
                            if cnt % 10000 == 0:
                                print(str(cnt) + " JSON records parsed [" + str(time.time() - start_time) + " seconds elapsed]...")
                            # limit lines read per file
                            # if (cnt > 10):
                            #     break
                        else:
                            # ERROR PIPE
                            writeError(out_path, tmp_path, error_file, "No merged_snapshot_data", rs_obj)
                    except Exception as err:
                        writeError(out_path, tmp_path, error_file, err, rs_obj)
                except:
                    writeError(out_path, tmp_path, error_file, "Cannot parse line to JSON", line)
                    
    # process chr 1-22, X and Y variants data file
    else:
        result_file = 'chr_' + chromosome + '_filtered.json'
        error_file =  'chr_' + chromosome + '_filtered.ERROR.json'

        # copy file to hpc tmp scratch space if specified
        if tmp_path != None:
            print("Copying data to tmp scratch space...")
            shutil.copy(file_path, tmp_path)

        print("Begin parsing...")
        with bz2.open(file_path if tmp_path == None else os.path.join(tmp_path, file_basename), 'rb') as f_in:
            # limit lines read per file
            cnt = 0
            for line in f_in:
                # print("rs_obj", rs_obj)
                try:
                    rs_obj = json.loads(line.decode('utf-8'))
                    try:
                        if 'primary_snapshot_data' in rs_obj:
                            rsids, ref_id = getRSIDs(rs_obj)
                            annotations = getAnnotations(rs_obj['primary_snapshot_data'])
                            variant_type = getVariantType(rs_obj['primary_snapshot_data'])
                            positions = getPositions(rs_obj['primary_snapshot_data'])
                            createRecord(rsids, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file, error_file)
                            cnt = cnt + 1
                            if cnt % 10000 == 0:
                                print(str(cnt) + " JSON records parsed [" + str(time.time() - start_time) + " seconds elapsed]...")
                            # limit lines read per file
                            # if (cnt > 10):
                            #     break
                        else:
                            # ERROR PIPE
                            writeError(out_path, tmp_path, error_file, "No primary_snapshot_data", rs_obj)
                    except Exception as err:
                        writeError(out_path, tmp_path, error_file, err, rs_obj)
                except:
                    writeError(out_path, tmp_path, error_file, "Cannot parse line to JSON", line)

    print("Parsing completed...")


    # copy parsed results json from hpc tmp scratch space to output dir if specified
    if tmp_path != None:
        if os.path.exists(os.path.join(tmp_path, result_file)):
            print("Copying results from tmp scratch space to output directory...")
            shutil.copy(os.path.join(tmp_path, result_file), out_path)
        if os.path.exists(os.path.join(tmp_path, error_file)):
            print("Copying error output from tmp scratch space to output directory...")
            shutil.copy(os.path.join(tmp_path, error_file), out_path)
    
    print("--- %s seconds ---" % str(time.time() - start_time))


if __name__ == "__main__":
    main()
