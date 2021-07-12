import sys
import json
import bz2
import shutil
# from pymongo import MongoClient, ASCENDING
# from pymongo.errors import ConnectionFailure
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
    return list(set(annotations))


# find variant type
def getVariantType(primary_refsnp):
    variant_type = 'NA'
    try:
        variant_type = primary_refsnp['variant_type']
    except:
        pass
    return variant_type


# find GRCh37 genomic position
def getPositions(primary_refsnp, variant_type):
    try:
        for i in primary_refsnp['placements_with_allele']:
            if len(i['placement_annot']['seq_id_traits_by_assembly']) > 0:
                assembly = i['placement_annot']['seq_id_traits_by_assembly'][0]['assembly_name']
                is_chrom = i['placement_annot']['seq_id_traits_by_assembly'][0]['is_chromosome']
                pos = i['alleles'][0]['allele']['spdi']['position']

                ######## parse position from GRCh37.p13
                if is_chrom == True and assembly == "GRCh37.p13":
                    if variant_type == "delins":
                        position_grch37 = str(pos)
                    elif variant_type == "del":
                        position_grch37 = str(pos)
                    elif variant_type == "ins":
                        position_grch37 = str(pos)
                    else:
                        position_grch37 = str(int(pos) + 1)
                    position_hgvs_grch37 = re.sub(r"\D", "", str(i['alleles'][0]['hgvs'].split(':')[1].split('.')[1]))

                ######## parse position from GRCh38.p13
                if is_chrom == True and assembly == "GRCh38.p13":
                    if variant_type == "delins":
                        position_grch38 = str(pos)
                    elif variant_type == "del":
                        position_grch38 = str(pos)
                    elif variant_type == "ins":
                        position_grch38 = str(pos)
                    else:
                        position_grch38 = str(int(pos) + 1)
                    position_hgvs_grch38 = re.sub(r"\D", "", str(i['alleles'][0]['hgvs'].split(':')[1].split('.')[1]))
    except:
        position_grch37 = '',
        position_hgvs_grch37 = '',
        position_grch38 = '',
        position_hgvs_grch38 = '',

    return {
        "position_grch37": position_grch37,
        "position_hgvs_grch37": position_hgvs_grch37,
        "position_grch38": position_grch38,
        "position_hgvs_grch38": position_hgvs_grch38,
    }


# write output from parsing json files
def createRecord(rsids, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file):
    if len(rsids) > 0:
        for rsid in rsids:
            if len(rsid) > 0 and len(chromosome) > 0 and len(positions['position_grch37']) > 0 and len(positions['position_hgvs_grch37']) > 0 and len(positions['position_grch38']) > 0 and len(positions['position_hgvs_grch38']) > 0 and len(annotations) > 0 and len(variant_type) > 0:
                writeJSON(rsid, chromosome, positions, ','.join(annotations), variant_type, ref_id, tmp_path, out_path, result_file)
                # insertMongoDB(rsid, chromosome, position, ','.join(annotations), variant_type)
            elif len(rsid) > 0 and len(chromosome) > 0 and len(positions) > 0 and len(annotations) == 0 and len(variant_type) > 0:
                # if no annotations, insert NA
                writeJSON(rsid, chromosome, positions, 'NA', variant_type, ref_id, tmp_path, out_path, result_file)
                # insertMongoDB(rsid, chromosome, position, 'NA', variant_type)
            else:
                pass


def writeJSON(rsid, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file):
    record = {
        "id": rsid,
        "chromosome": chromosome,
        "position_grch37": positions['position_grch37'],
        "position_hgvs_grch37": positions['position_hgvs_grch37'],
        "position_grch38": positions['position_grch38'],
        "position_hgvs_grch38": positions['position_hgvs_grch38'],
        "function": annotations,
        "type": variant_type,
        "ref_id": ref_id
    }
    with open(os.path.join(out_path, result_file) if tmp_path is None else os.path.join(tmp_path, result_file), 'a') as outfile:
        json.dump(record, outfile)
        outfile.write('\n')


def main():
    file_path = sys.argv[1]
    out_path = sys.argv[2]
    tmp_path = sys.argv[3] if len(sys.argv) > 3 else None

    print("Starting to parse " + file_path + "...")

    print("file_path", file_path)
    print("out_path", out_path)
    print("tmp_path", tmp_path)

    file_basename = os.path.basename(file_path)

    # copy file to hpc tmp scratch space if specified
    if tmp_path is not None:
        print("Copying data to tmp scratch space...")
        shutil.copy(file_path, tmp_path)

    print("Begin parsing...")
    with bz2.open(file_path if tmp_path is None else os.path.join(tmp_path, file_basename), 'rb') as f_in:
        # limit lines read per file
        # cnt = 0
        for line in f_in:
            rs_obj = json.loads(line.decode('utf-8'))
            # print("rs_obj", rs_obj)
            if 'primary_snapshot_data' in rs_obj:
                rsids, ref_id = getRSIDs(rs_obj)
                chromosome = getChromosome(file_basename)
                result_file = 'chr_' + chromosome + '_filtered.json'
                annotations = getAnnotations(rs_obj['primary_snapshot_data'])
                variant_type = getVariantType(rs_obj['primary_snapshot_data'])
                positions = getPositions(rs_obj['primary_snapshot_data'], variant_type)
                createRecord(rsids, chromosome, positions, annotations, variant_type, ref_id, tmp_path, out_path, result_file)
    #             # limit lines read per file
    #             # cnt = cnt + 1
    #             # if (cnt > 10):
    #             #     break
            else:
                # ERROR PIPE
                print("ERROR OBJ", rs_obj)

    print("Parsing completed...")

    # copy parsed results json from hpc tmp scratch space to output dir if specified
    if tmp_path is not None:
        print("Copying results from tmp scratch space to output directory...")
        shutil.copy(os.path.join(tmp_path, result_file), out_path)
    
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    main()
