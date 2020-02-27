import sys
import json
import gzip
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
import time
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
def getChromosome(f_in):
    return f_in.name.split('.')[0].split('-')[1][3:]


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
def getPosition(primary_refsnp, variant_type):
    position = ''
    for i in primary_refsnp['placements_with_allele']:
        if len(i['placement_annot']['seq_id_traits_by_assembly']) > 0:
            assembly = i['placement_annot']['seq_id_traits_by_assembly'][0]['assembly_name']
            is_chrom = i['placement_annot']['seq_id_traits_by_assembly'][0]['is_chromosome']
            pos = i['alleles'][0]['allele']['spdi']['position']
            # only choose bp from GRCh37.p13
            if is_chrom == True and assembly == "GRCh37.p13":
                if variant_type == "delins":
                    position = str(pos)
                elif variant_type == "del":
                    position = str(pos)
                elif variant_type == "ins":
                    position = str(pos)
                else:
                    position = str(int(pos) + 1)
    return position


# write output from parsing json files
def createRecord(rsids, chromosome, position, annotations, variant_type, ref_id):
    if len(rsids) > 0:
        for rsid in rsids:
            if len(rsid) > 0 and len(chromosome) > 0 and len(position) > 0 and len(annotations) > 0 and len(variant_type) > 0:
                writeJSON(rsid, chromosome, position, ','.join(annotations), variant_type, ref_id)
                # insertMongoDB(rsid, chromosome, position, ','.join(annotations), variant_type)
            elif len(rsid) > 0 and len(chromosome) > 0 and len(position) > 0 and len(annotations) == 0 and len(variant_type) > 0:
                # if no annotations, insert NA
                writeJSON(rsid, chromosome, position, 'NA', variant_type, ref_id)
                # insertMongoDB(rsid, chromosome, position, 'NA', variant_type)
            else:
                pass


def writeJSON(rsid, chromosome, position, annotations, variant_type, ref_id):
    record = {
        "id": rsid,
        "chromosome": chromosome,
        "position": position,
        "function": annotations,
        "type": variant_type,
        "ref_id": ref_id
    }
    with open('chr_' + chromosome + '_filtered.json', 'a') as outfile:
        json.dump(record, outfile)
        outfile.write('\n')


def main():
    print "Start creating json file(s) with filtered records. db: LDLink, collection: dbsnp151"
    filename = sys.argv[1]
    print filename
    input_dir = 'json_refsnp/'
    with gzip.open(input_dir + filename, 'rb') as f_in:
        # limit lines read per file
        # cnt = 0
        for line in f_in:
            rs_obj = json.loads(line.decode('utf-8'))
            if 'primary_snapshot_data' in rs_obj:
                rsids, ref_id = getRSIDs(rs_obj)
                chromosome = getChromosome(f_in)
                annotations = getAnnotations(rs_obj['primary_snapshot_data'])
                variant_type = getVariantType(rs_obj['primary_snapshot_data'])
                position = getPosition(rs_obj['primary_snapshot_data'], variant_type)
                createRecord(rsids, chromosome, position, annotations, variant_type, ref_id)
                # limit lines read per file
                # cnt = cnt + 1
                # if (cnt > 10):
                #     break
    print "JSON file(s) completed."

    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    main()
