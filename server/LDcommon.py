import json
import math
import re
import shutil
import subprocess
from collections import OrderedDict
from bson import json_util
import boto3
import botocore
from pymongo import MongoClient
from LDutilites import get_config

# retrieve config
config = get_config()
aws_info = config['aws_info']
population_samples_dir = config['population_samples_dir']
data_dir = config['data_dir']
tmp_dir = config['tmp_dir']
genotypes_dir = config['genotypes_dir']

genome_build_vars = {
    "vars": ['grch37', 'grch38', 'grch38_high_coverage'],
    "grch37": {
        "title": "GRCh37",
        "title_hg": "hg19",
        "chromosome": "chromosome_grch37",
        "position": "position_grch37",
        "gene_begin": "begin_grch37",
        "gene_end": "end_grch37",
        "refGene": "refGene_grch37",
        "1000G_dir": "GRCh37",
        "1000G_file": "ALL.chr%s.phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz",
        "1000G_chr_prefix": "",
        "ldassoc_example_file": "prostate_example_grch37.txt"
    },
    "grch38": {
        "title": "GRCh38",
        "title_hg": "hg38",
        "chromosome": "chromosome_grch38",
        "position": "position_grch38",
        "gene_begin": "begin_grch38",
        "gene_end": "end_grch38",
        "refGene": "refGene_grch38",
        "1000G_dir": "GRCh38",
        "1000G_file": "ALL.chr%s.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.vcf.gz",
        "1000G_chr_prefix": "",
        "ldassoc_example_file": "prostate_example_grch38.txt"
    },
    "grch38_high_coverage": {
        "title": "GRCh38 High Coverage",
        "title_hg": "hg38_HC",
        "chromosome": "chromosome_grch38",
        "position": "position_grch38",
        "gene_begin": "begin_grch38",
        "gene_end": "end_grch38",
        "refGene": "refGene_grch38",
        "1000G_dir": "GRCh38_High_Coverage",
        "1000G_file": "CCDG_14151_B01_GRM_WGS_2020-08-05_chr%s.filtered.shapeit2-duohmm-phased.vcf.gz",
        "1000G_chr_prefix": "chr",
        "ldassoc_example_file": "prostate_example_grch38.txt"
    }
}

def checkS3File(aws_info, bucket, filePath):
    try:
        boto3.client('s3').head_object(Bucket=bucket, Key=filePath)
        return True
    except botocore.exceptions.ClientError as e:
        raise Exception(f"{bucket} {filePath} not found in AWS S3.")
        # return False

def retrieveAWSCredentials():
    credentials = get_aws_credentials()
    return ' '.join([ f"export {k}={v};" for k, v in credentials.items() ])

def connectMongoDBReadOnly(readonly=True, api=False, connect_db_server=False):
    return MongoClient(
        host = config['mongodb_host'],
        port = config['mongodb_port'],
        username = config['mongodb_username'],
        password = config['mongodb_password'],
        authSource = config['mongodb_database'],
    )[config['mongodb_database']]

def get_aws_credentials():
    frozen_credentials = boto3.Session().get_credentials().get_frozen_credentials()
    credentials = {
        "AWS_ACCESS_KEY_ID": frozen_credentials.access_key,
        "AWS_SECRET_ACCESS_KEY": frozen_credentials.secret_key,
        "AWS_SESSION_TOKEN": frozen_credentials.token,
    }
    return { k: v for k, v in credentials.items() if v is not None }


def get_command_output(*cmd, **subprocess_args):
    output = subprocess.check_output(cmd, **subprocess_args)
    return [line.decode("utf-8") for line in output.splitlines()]

def tabix(*tabix_args, **subprocess_args):
    tabix_path = shutil.which("tabix")
    cmd = [tabix_path, *tabix_args]
    args = {"env": get_aws_credentials(), **subprocess_args}
    return get_command_output(*cmd, **args)

def get_1000g_data(snp_pos, snp_coords, genome_build, query_dir):
    vcf_filepath, tabix_coords, query_file = get_vcf_snp_params(snp_pos, snp_coords, genome_build)
    checkS3File(aws_info, aws_info['bucket'], vcf_filepath)

    # ensure tabix_coords is a list
    tabix_coords = re.split('\s+', tabix_coords.strip())
    output = tabix("-fhD", "--separate-regions", query_file, *tabix_coords, cwd=query_dir)
    vcf = [line for line in output if "END" not in line]

    return get_head(vcf)

def get_1000g_data_single(vcf_pos, snp_coord, genome_build, query_dir, request, write_output):
    vcf_filepath, tabix_coords, query_file = get_vcf_snp_params([vcf_pos], [snp_coord], genome_build)
    checkS3File(aws_info, aws_info['bucket'], vcf_filepath)

    tabix_coords = re.split('\s+', tabix_coords.strip())
    output = tabix("-fhD", query_file, *tabix_coords, cwd=query_dir)
    vcf = [line for line in output if "END" not in line]

    if write_output:
        temp_filepath = tmp_dir + "snp_no_dups_" + request + ".vcf"
        with open(temp_filepath, "w") as f:
            f.write("\n".join(vcf))
            
    return get_head(vcf)

def retrieveTabix1000GData(snp_pos, snp_coords, genome_build,query_dir):
    vcf_filePath,tabix_coords,query_file = get_vcf_snp_params(snp_pos,snp_coords,genome_build)
    checkS3File(aws_info, aws_info['bucket'], vcf_filePath)
    export_s3_keys = retrieveAWSCredentials()
    tabix_snps = export_s3_keys + " cd {2}; tabix -fhD --separate-regions {0}{1} | grep -v -e END".format(
        query_file, tabix_coords, query_dir)
    # print("tabix_snps", tabix_snps)
    vcf = [x.decode('utf-8') for x in subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE).stdout.readlines()]
    vcf,head = get_head(vcf)
    return vcf,head

def retrieveTabix1000GDataSingle(vcf_pos,snp_coord,genome_build, query_dir,request,is_output):
    vcf_filePath,tabix_coords,query_file=get_vcf_snp_params([vcf_pos],[snp_coord],genome_build)
    checkS3File(aws_info, aws_info['bucket'], vcf_filePath)
    export_s3_keys = retrieveAWSCredentials()
    if is_output:
        retrieve_command = " cd {2}; tabix -fhD  {0}{1} | grep -v -e END > {3}".format(query_file, tabix_coords, query_dir,tmp_dir + "snp_no_dups_" + request + ".vcf")
    else:
        retrieve_command = " cd {2}; tabix -fhD  {0}{1} | grep -v -e END".format(query_file, tabix_coords, query_dir)

    tabix_snps = export_s3_keys + retrieve_command
    vcf = [x.decode('utf-8') for x in subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE).stdout.readlines()]
    if is_output:
        vcf = open(tmp_dir+"snp_no_dups_"+request+".vcf").readlines()
      
    vcf,head = get_head(vcf)
    return vcf,head

# Query genomic coordinates
def get_rsnum(db, coord, genome_build):
    temp_coord = coord.strip("chr").split(":")
    if len(temp_coord)<=1:
        return 
    chro = temp_coord[0]
    pos = temp_coord[1]
    query_results = db.dbsnp.find({"chromosome": chro.upper() if chro == 'x' or chro == 'y' else str(chro), genome_build_vars[genome_build]['position']: str(pos)})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def processCollapsedTranscript(genes_same_name):
    chrom = genes_same_name[0]["chrom"]
    txStart = genes_same_name[0]["txStart"]
    txEnd = genes_same_name[0]["txEnd"]
    exonStarts = genes_same_name[0]["exonStarts"].split(",")
    exonEnds = genes_same_name[0]["exonEnds"].split(",")
    name = genes_same_name[0]["name"]
    name2 = genes_same_name[0]["name2"]
    transcripts = [name] * len(list(filter(lambda x: x != "",genes_same_name[0]["exonStarts"].split(","))))


    for gene in genes_same_name[1:]:
        txStart = gene['txStart'] if gene['txStart'] < txStart else txStart
        txEnd = gene['txEnd'] if gene['txEnd'] > txEnd else txEnd
        exonStarts = list(filter(lambda x: x != "", gene["exonStarts"].split(","))) + exonStarts
        exonEnds = list(filter(lambda x: x != "", gene["exonEnds"].split(","))) + exonEnds
        transcripts = transcripts + ([gene['name']] * len(list(filter(lambda x: x != "", gene["exonStarts"].split(",")))))
    return {
        "chrom": chrom,
        "txStart": txStart,
        "txEnd": txEnd,
        "exonStarts": ",".join(exonStarts),
        "exonEnds": ",".join(exonEnds),
        "name2": name2,
        "transcripts": ",".join(transcripts)
    }

def getRefGene(db, filename, chromosome, begin, end, genome_build, collapseTranscript):
    query_results = db[genome_build_vars[genome_build]['refGene']].find({
        "chrom": "chr" + chromosome, 
        "$or": [
            {
                "txStart": {"$lte": int(begin)}, 
                "txEnd": {"$gte": int(end)}
            }, 
            {
                "txStart": {"$gte": int(begin)}, 
                "txEnd": {"$lte": int(end)}
            },
            {
                "txStart": {"$lte": int(begin)}, 
                "txEnd": {"$gte": int(begin), "$lte": int(end)}
            },
            {
                "txStart": {"$gte": int(begin), "$lte": int(end)}, 
                "txEnd": {"$gte": int(end)}
            }
        ]
    })#.sort([("cdsEnd",1),("txStart",1)])
    if collapseTranscript:
        query_results_sanitized = json.loads(json_util.dumps(query_results)) 
        #print("$$$$$$",query_results_sanitized)
        group_by_gene_name = {}
        for gene in query_results_sanitized:
            # new gene name
            if gene['name2'] not in group_by_gene_name:
                group_by_gene_name[gene['name2']] = []
                group_by_gene_name[gene['name2']].append(gene)
            # same gene name as another's
            else:
                group_by_gene_name[gene['name2']].append(gene)
        #print(json.dumps(group_by_gene_name, indent=4, sort_keys=False))
        query_results_sanitized = []
        for gene_name_key in group_by_gene_name.keys():
            #print("#",gene_name_key)
            query_results_sanitized.append(processCollapsedTranscript(group_by_gene_name[gene_name_key]))
        # print(json.dumps(query_results_sanitized, indent=4, sort_keys=True))
    else:
        query_results_sanitized = json.loads(json_util.dumps(query_results)) 
    #temp = query_results_sanitized.pop(0)
    #query_results_sanitized.append(temp)
    #print(query_results_sanitized)
    with open(filename, "w") as f:
        for x in query_results_sanitized:
            f.write(json.dumps(x) + '\n')
    return query_results_sanitized

def getRecomb(db, filename, chromosome, begin, end, genome_build):
    recomb_results = db.recomb.find({
		genome_build_vars[genome_build]['chromosome']: str(chromosome), 
		genome_build_vars[genome_build]['position']: {
            "$gte": int(begin), 
            "$lte": int(end)
        }
	})
    recomb_results_sanitized = json.loads(json_util.dumps(recomb_results)) 

    with open(filename, "w") as f:
        for recomb_obj in recomb_results_sanitized:
            f.write(json.dumps({
                "rate": recomb_obj['rate'],
                genome_build_vars[genome_build]['position']: recomb_obj[genome_build_vars[genome_build]['position']]
            }) + '\n')
    return recomb_results_sanitized

def getEmail():
    return  config['email_smtp_host']

#################################################################
#define common functions to Validate & retrieve SNP coordinates #
#################################################################
def validsnp(snplst,genome_build,snp_limits):
    # Validate genome build param
    output = {}
    if genome_build not in genome_build_vars['vars']:
        output["error"] = "Invalid genome build. Please specify either " + ", ".join(genome_build_vars['vars']) + "."
        return(json.dumps(output, sort_keys=True, indent=2))
    # print(snplst)
    # Open Inputted SNPs list file
    # if the input list is in a text file 
    if snplst:
         # for ldexpress, the snplst is array, not file path
        try:
            snps_raw = open(snplst).readlines()
        except:
            try:
                snps_raw = snplst.split("+")
            except: # for ldpair post input as array
                snps_raw = snplst

        if snp_limits:
            if len(snps_raw) > snp_limits:
                output["error"] = "Maximum variant list is "+ str(snp_limits) +"  RS numbers or coordinates. Your list contains " + \
                    str(len(snps_raw))+" entries."
                return(json.dumps(output, sort_keys=True, indent=2))

        # Remove duplicate RS numbers and cast to lower case
        snps = []
        for snp_raw in snps_raw:
            if type(snp_raw) is str:
                snp = snp_raw.lower().strip().split()
                if snp not in snps:
                    snps.append(snp)
            else:
                snps.append(snp_raw)
        return snps
    return 

def get_coords(db, rsid):
    rsid = rsid.strip("rs")
    query_results = db.dbsnp.find_one({"id": rsid})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def get_coords_gene(gene_raw, db,genome_build):
    gene=gene_raw.upper()
    mongoResult = db.genes_name_coords.find_one({"name": gene})

    #format mongo output
    if mongoResult != None:
        geneResult = [mongoResult["name"], mongoResult[genome_build_vars[genome_build]['chromosome']], mongoResult[genome_build_vars[genome_build]['gene_begin']], mongoResult[genome_build_vars[genome_build]['gene_end']]]
        return geneResult
    else:
        return None


# def get_dbsnp_coord(db, chromosome, position):
#     query_results = db.dbsnp.find_one({"chromosome": str(chromosome), genome_build_vars[genome_build]['position']: str(position)})
#     query_results_sanitized = json.loads(json_util.dumps(query_results))
#     return query_results_sanitized

# Replace input genomic coordinates with variant ids (rsids)
def replace_coord_rsid(db, snp,genome_build,output):
    if snp[0:2] == "rs":
        return snp
    else:
        snp_info_lst = get_rsnum(db, snp, genome_build)
        if snp_info_lst != None:
            if len(snp_info_lst) > 1:
                var_id = "rs" + snp_info_lst[0]['id']
                ref_variants = []
                for snp_info in snp_info_lst:
                    if snp_info['id'] == snp_info['ref_id']:
                        ref_variants.append(snp_info['id'])
                if len(ref_variants) > 1:
                    var_id = "rs" + ref_variants[0]
                    if "warning" in output:
                        output["warning"] = output["warning"] + \
                        ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                    else:
                        output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                elif len(ref_variants) == 0 and len(snp_info_lst) > 1:
                    var_id = "rs" + snp_info_lst[0]['id']
                    if "warning" in output:
                        output["warning"] = output["warning"] + \
                        ". Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                    else:
                        output["warning"] = "Multiple rsIDs (" + ", ".join(["rs" + ref_id for ref_id in ref_variants]) + ") map to genomic coordinates " + snp
                else:
                    var_id = "rs" + ref_variants[0]
                return var_id
            elif len(snp_info_lst) == 1:
                var_id = "rs" + snp_info_lst[0]['id']
                return var_id
            else:
                return snp
        else:
            return snp
    return snp


def replace_coords_rsid_list(db, snp_lst,genome_build,output):
    new_snp_lst = []
    for snp_raw_i in snp_lst:
        if len(snp_raw_i) > 0:
            snp = snp_raw_i[0]
            var_id = replace_coord_rsid(db, snp, genome_build,output)
            if snp != var_id:
                new_snp_lst.append([var_id])
            else:
                new_snp_lst.append(snp_raw_i)
    return new_snp_lst

##############################################
### common function to retrieve population ###
##############################################
def get_population(pop, request,output):
    # Select desired ancestral populations
    pops = pop.split("+")
    pop_dirs = []
    for pop_i in pops:
        if pop_i in ["ALL", "AFR", "AMR", "EAS", "EUR", "SAS", "ACB", "ASW", "BEB", "CDX", "CEU", "CHB", "CHS", "CLM", "ESN", "FIN", "GBR", "GIH", "GWD", "IBS", "ITU", "JPT", "KHV", "LWK", "MSL", "MXL", "PEL", "PJL", "PUR", "STU", "TSI", "YRI"]:
            pop_dirs.append(data_dir + population_samples_dir + pop_i + ".txt")
        else:
            output["error"] = pop_i + " is not an ancestral population. Choose one of the following ancestral populations: AFR, AMR, EAS, EUR, or SAS; or one of the following sub-populations: ACB, ASW, BEB, CDX, CEU, CHB, CHS, CLM, ESN, FIN, GBR, GIH, GWD, IBS, ITU, JPT, KHV, LWK, MSL, MXL, PEL, PJL, PUR, STU, TSI, or YRI."
            return(json.dumps(output, sort_keys=True, indent=2))

    get_pops = "cat " + " ".join(pop_dirs) + " > " + tmp_dir + "pops_" + request + ".txt"
    subprocess.call(get_pops, shell=True)

    pop_list = open(tmp_dir + "pops_" + request + ".txt").readlines()
    ids = [i.strip() for i in pop_list]
    pop_ids = list(set(ids))

    return pop_ids
 
 #####################################################
 ##   Define function to correct indel alleles     ###
 #####################################################
def set_alleles(a1, a2):
    if len(a1) == 1 and len(a2) == 1:
        a1_n = a1
        a2_n = a2
    elif len(a1) == 1 and len(a2) > 1:
        a1_n = "-"
        a2_n = a2[1:]
    elif len(a1) > 1 and len(a2) == 1:
        a1_n = a1[1:]
        a2_n = "-"
    elif len(a1) > 1 and len(a2) > 1:
        a1_n = a1[1:]
        a2_n = a2[1:]
    return(a1_n, a2_n)

#################################################
# get the genotype ###
#################################################
def get_query_variant_c(snp_coord, pop_ids, request, genome_build, is_output,output={}):
    queryVariantWarnings = []
    #vcf1_pos: 60697654; snp_coord: ['rs4672393', '2', '60697654']
    tmp_coord = [str(x) for x in snp_coord]
    tabix_query_snp_out,head = get_1000g_data_single(str(snp_coord[2]),tmp_coord, genome_build, data_dir + genotypes_dir + genome_build_vars[genome_build]['1000G_dir'],request, is_output)
    # Validate error
    if len(tabix_query_snp_out) == 0:
        # print("ERROR", "len(tabix_query_snp_out) == 0")
        # handle error: snp + " is not in 1000G reference panel."
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not in 1000G reference panel."])
        output["error"] = snp_coord[0]+" Variant is not in 1000G reference panel." + str(output["error"] if "error" in output else "")
        #output["warning"] = snp_coord[0]+" Variant is not in 1000G reference panel." + str(output["warning"] if "warning" in output else "")
        if is_output:
            subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
            subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
        return (None, None, queryVariantWarnings)
    elif len(tabix_query_snp_out) > 1:
        geno = []
        for i in range(len(tabix_query_snp_out)):
            # if tabix_query_snp_out[i].strip().split()[2] == snp_coord[0]:
            geno = tabix_query_snp_out[i].strip().split()
            geno[0] = geno[0].lstrip('chr')
            #skip the geno did not on the same chromesome??
            #if not (geno[0] == snp_coord[1] and geno[1] == snp_coord[2]):
            #        geno = []
        if geno == []:
            # print("ERROR", "geno == []")
            # handle error: snp + " is not in 1000G reference panel."
            queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not in 1000G reference panel."])
            output["error"] = "Variant is not in 1000G reference panel." + str(output["error"] if "error" in output else "")
            #output["warning"] = snp_coord[0]+" Variant is not in 1000G reference panel." + str(output["warning"] if "warning" in output else "")
            if is_output:
                subprocess.call("rm " + tmp_dir + "pops_" + request + ".txt", shell=True)
                subprocess.call("rm " + tmp_dir + "*" + request + "*.vcf", shell=True)
            return (None,None, queryVariantWarnings)
    else:
        geno = tabix_query_snp_out[0].strip().split()
        geno[0] = geno[0].lstrip('chr')
    if geno[2] != snp_coord[0] and "rs" in geno[2]:
            queryVariantWarnings.append([snp_coord[0], geno[2], "Genomic position does not match RS number at 1000G position (chr" + geno[0] + ":" + geno[1] + " = " + geno[2] + ")."])
            output["warning"] = "Genomic position does not match RS number at 1000G position (chr" + geno[0] + ":" + geno[1] + " = " + geno[2] + ")." + str(output["warning"] if "warning" in output else "")

    if "," in geno[3] or "," in geno[4]:
        #print('handle error: snp + " is not a biallelic variant."')
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is not a biallelic."])
        output["error"]= snp_coord[0] + " variant is not a biallelic." + str(output["warning"] if "warning" in output else "")
  
    index = []
    for i in range(9, len(head)):
        if head[i] in pop_ids:
            index.append(i)

    genotypes = {"0": 0, "1": 0}
    for i in index:
        sub_geno = geno[i].split("|")
        for j in sub_geno:
            if j in genotypes:
                genotypes[j] += 1
            else:
                genotypes[j] = 1

    if genotypes["0"] == 0 or genotypes["1"] == 0:
        # print('handle error: snp + " is monoallelic in the " + pop + " population."')
        queryVariantWarnings.append([snp_coord[0], "NA", "Variant is monoallelic in the chosen population(s)."])
     
    return(geno,head,queryVariantWarnings)

###################################################
######## parse vcf using --separate-regions   #####
###################################################
#def parse_vcf(vcf,snp_coords,output,genome_build,is_multi):
def parse_vcf(vcf,snp_coords,output,genome_build,ifsorted):
    delimiter = "#"
    snp_lists = str('**'.join(vcf)).split(delimiter)
    snp_dict = {}
    snp_rs_dict = {}
    missing_rs = []    
    snp_found_list = [] 
    #print(vcf)
    #print(snp_lists)
    for snp in snp_lists[1:]:
        snp_tuple = snp.split("**")
        snp_key = snp_tuple[0].split("-")[-1].strip()
        vcf_list = [] 
        #print(snp_tuple)
        match_v = ''
        for v in snp_tuple[1:]:#choose the matched one for dup; if no matched, choose first
            if len(v) > 0:
                match_v = v
                geno = v.strip().split()
                if geno[1] == snp_key:
                    match_v = v
                # if is_multi:
                #     vcf_list.append(v)
                #     snp_found_list.append(snp_key)  
                # else:
                #     match_v = v
                #     geno = v.strip().split()
                #     if geno[1] == snp_key:
                #         match_v = v
        if len(match_v) > 0:
            vcf_list.append(match_v)
            snp_found_list.append(snp_key)        
        #create snp_key as chr7:pos_rs4
        snp_dict[snp_key] = vcf_list
    
    missing_rs_snp = []
    for snp_coord in snp_coords:
        if snp_coord[-1] not in snp_found_list:
            missing_rs.append(snp_coord[0])
            missing_rs_snp.append([snp_coord[0],"chr"+snp_coord[1]+":"+snp_coord[2]])
        else:
            s_key = "chr"+snp_coord[1]+":"+snp_coord[2]+"_"+snp_coord[0]
            snp_rs_dict[s_key] = snp_dict[snp_coord[2]]      
    if output != None:
        if len(missing_rs) == len(snp_coords):
            output["error"] = "Input variant list does not contain any valid RS numbers or coordinates. " + str(output["warning"] if "warning" in output else "")
            return "","",output
        if len(missing_rs) > 0:
            output["warning"] = "Query variant " + " ".join(missing_rs) + " is missing from 1000G (" + genome_build_vars[genome_build]['title'] + ") data. " + str(output["warning"] if "warning" in output else "")
    
    del snp_dict
       
    sorted_snp_rs = snp_rs_dict
    if ifsorted:
        sorted_snp_rs = OrderedDict(sorted(snp_rs_dict.items(),key=customsort))

    #print(sorted_snp_rs)
    return sorted_snp_rs,missing_rs_snp,output

def customsort(key_snp1):
    k = key_snp1[0].split("_")[0].split(':')[1]
    k = int(k)
    return k

def get_vcf_snp_params(snp_pos,snp_coords,genome_build):
     # Sort coordinates and make tabix formatted coordinates
    snp_pos_int = [int(i) for i in snp_pos]
    snp_pos_int.sort()
    tabix_coords=""
    for i in range(len(snp_pos_int)):
        snp_coord_str = [genome_build_vars[genome_build]['1000G_chr_prefix'] + snp_coords[i][1] + ":" + snp_coords[i][2] + "-" + snp_coords[i][2]]
        tabix_coords = tabix_coords+" " + " ".join(snp_coord_str)
    # # Extract 1000 Genomes phased genotypes
    vcf_filePath = "%s/%s%s/%s" % (aws_info['data_subfolder'], genotypes_dir, genome_build_vars[genome_build]['1000G_dir'], genome_build_vars[genome_build]['1000G_file'] % (snp_coords[0][1]))
    vcf_query_snp_file = "s3://%s/%s" % (aws_info['bucket'], vcf_filePath)
    #print("vcf_filePath",vcf_filePath,"snp_coords",snp_coords)
    return vcf_filePath,tabix_coords,vcf_query_snp_file

def LD_calcs(hap, allele_n):
    # Extract haplotypes
    A = hap["00"]
    B = hap["01"]
    C = hap["10"]
    D = hap["11"]
    N = A + B + C + D
    delta = float(A*D-B*C)
    Ms = float((A+C)*(B+D)*(A+B)*(C+D))
    if Ms != 0:
        # D prime
        if delta < 0:
            D_prime = abs(delta/min((A+C)*(A+B), (B+D)*(C+D)))
        else:
            D_prime = abs(delta/min((A+C)*(C+D), (A+B)*(B+D)))
        # R2
        r2 = (delta**2)/Ms
        # Non-effect and Effect Alleles and their Allele Frequencies
        allele1 = str(allele_n["0"])
        allele1_freq = str(round(float(A + C) / N, 3)) if N > float(A + C) else "NA"

        allele2 = str(allele_n["1"])
        allele2_freq = str(round(float(B + D) / N, 3)) if N > float(B + D) else "NA"
        return [r2, D_prime, "=".join([allele1, allele1_freq]), "=".join([allele2, allele2_freq])]

def get_dbsnp_coord(db, chromosome, position,genome_build):
    query_results = db.dbsnp.find_one({"chromosome": str(chromosome), genome_build_vars[genome_build]['position']: str(position)})
    query_results_sanitized = json.loads(json_util.dumps(query_results))
    return query_results_sanitized

def check_same_chromosome(snp_coords,output):
    # Check SNPs are all on the same chromosome
    for i in range(len(snp_coords)):
        if snp_coords[0][1] != snp_coords[i][1]:
            output["error"] = "Not all input variants are on the same chromosome: "+snp_coords[i-1][0]+"=chr" + \
                str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0] + \
                "=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+". " + str(output["warning"] if "warning" in output else "")
            return(json.dumps(output, sort_keys=True, indent=2))
    return

def check_allele(geno):
    if len(geno[3]) == 1 and len(geno[4]) == 1:
        snp_a1 = geno[3]
        snp_a2 = geno[4]
    elif len(geno[3]) == 1 and len(geno[4]) > 1:
        snp_a1 = "-"
        snp_a2 = geno[4][1:]
    elif len(geno[3]) > 1 and len(geno[4]) == 1:
        snp_a1 = geno[3][1:]
        snp_a2 = "-"
    elif len(geno[3]) > 1 and len(geno[4]) > 1:
        snp_a1 = geno[3][1:]
        snp_a2 = geno[4][1:]

    allele = {"0|0": [snp_a1, snp_a1], "0|1": [snp_a1, snp_a2], "1|0": [snp_a2, snp_a1], "1|1": [
        snp_a2, snp_a2], "0": [snp_a1, "."], "1": [snp_a2, "."], "./.": [".", "."], ".": [".", "."]}
    return allele,snp_a1,snp_a2

def get_head(vcf):
    h = 0
    while vcf[h][0:2] == "##":
        h += 1
    head = vcf[h].strip().split() 
    vcf = vcf[h+1:]
    return vcf, head

def get_geno(vcf,snp):
    vcf,h = get_head(vcf)
    if len(vcf) > 1:
        for i in range(len(vcf)):
            #if vcf[i].strip().split()[2] == snp:
            geno = vcf[i].strip().split()
            geno[0] = geno[0].lstrip('chr')     
    else:
        geno = vcf[0].strip().split()
        geno[0] = geno[0].lstrip('chr')
    return geno

def chunkWindow(pos, window, num_subprocesses):
    if (pos - window <= 0):
        minPos = 0
    else:
        minPos = pos - window
    maxPos = pos + window
    windowRange = maxPos - minPos
    chunks = []
    newMin = minPos
    newMax = 0
    for _ in range(num_subprocesses):
        newMax = newMin + (windowRange / num_subprocesses)
        chunks.append([math.ceil(newMin), math.ceil(newMax)])
        newMin = newMax + 1
    return chunks

# collect output in parallel
def get_output(process):
    return process.communicate()[0].splitlines()

def get_forgeDB(db,rs):
    result = db.forge_score.find_one({"snp_id": str(rs)})
    if result is None:
        return ""   
    else:
        return result["score"]
def get_regDB(db,genome_build,chr, pos):
    result = db.regulome.find_one({genome_build_vars[genome_build]['chromosome']: str(chr), genome_build_vars[genome_build]['position']: int(pos)})
    if result is None:
        return "."   
    else:
        return result["score"]
#################
def ldproxy_figure(out_ld_sort, r2_d,coord1,coord2,snp,pop,request,db,snp_coord,genome_build,collapseTranscript,annotate):
    q_rs = []
    q_allele = []
    q_coord = []
    q_maf = []
    p_rs = []
    p_allele = []
    p_coord = []
    p_maf = []
    dist = []
    d_prime = []
    d_prime_round = []
    r2 = []
    r2_round = []
    corr_alleles = []
    regdb = []
    forgedb = []
    funct = []
    color = []
    size = []
    for i in range(len(out_ld_sort)):
        q_rs_i, q_allele_i, q_coord_i, p_rs_i, p_allele_i, p_coord_i, dist_i, d_prime_i, r2_i, corr_alleles_i, forgedb_i,regdb_i,q_maf_i, p_maf_i, funct_i, dist_abs = out_ld_sort[
            i]

        if float(r2_i) > 0.01:
            q_rs.append(q_rs_i)
            q_allele.append(q_allele_i)
            q_coord.append(float(q_coord_i.split(":")[1]) / 1000000)
            q_maf.append(str(round(float(q_maf_i), 4)))
            if p_rs_i == ".":
                p_rs_i = p_coord_i
            p_rs.append(p_rs_i)
            p_allele.append(p_allele_i)
            p_coord.append(float(p_coord_i.split(":")[1]) / 1000000)
            p_maf.append(str(round(float(p_maf_i), 4)))
            dist.append(str(round(dist_i / 1000000.0, 4)))
            d_prime.append(float(d_prime_i))
            d_prime_round.append(str(round(float(d_prime_i), 4)))
            r2.append(float(r2_i))
            r2_round.append(str(round(float(r2_i), 4)))
            corr_alleles.append(corr_alleles_i)

            # Correct Missing Annotations
            if regdb_i == ".":
                regdb_i = ""
            regdb.append(regdb_i)
            forgedb.append(forgedb_i)
            if funct_i == ".":
                funct_i = ""
            if funct_i == "NA":
                funct_i = "none"
            funct.append(funct_i)

            # Set Color
            if i == 0:
                color_i = "blue"
            elif funct_i != "none" and funct_i != "":
                color_i = "red"
            else:
                color_i = "orange"
            color.append(color_i)

            # Set Size
            size_i = 9 + float(p_maf_i) * 14.0
            size.append(size_i)

    # Begin Bokeh Plotting
    from collections import OrderedDict
    from bokeh.embed import components, file_html
    from bokeh.layouts import gridplot
    from bokeh.models import HoverTool, LinearAxis, Range1d
    from bokeh.plotting import ColumnDataSource, curdoc, figure, output_file, reset_output, save
    from bokeh.resources import CDN

    reset_output()
    plot_h_pix = 0
    # Proxy Plot
    x = p_coord
    if r2_d == "r2":
        y = r2
    else:
        y = d_prime
    whitespace = 0.01
    xr = Range1d(start=coord1 / 1000000.0 - whitespace,
                end=coord2 / 1000000.0 + whitespace)
    yr = Range1d(start=-0.03, end=1.03)
    sup_2 = "\u00B2"

    proxy_plot = figure(
        title="Proxies for " + snp + " in " + pop,
        min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, 
        width=900,
        height=600,
        x_range=xr, y_range=yr,
        tools="hover,tap,pan,box_zoom,box_select,undo,redo,reset,save", 
        toolbar_location="above")

    proxy_plot.title.align = "center"

    # Add recombination rate
    recomb_file = tmp_dir + "recomb_" + request + ".json"
    recomb_json = getRecomb(db, recomb_file, snp_coord['chromosome'], coord1 - whitespace, coord2 + whitespace, genome_build)

    recomb_x = []
    recomb_y = []

    for recomb_obj in recomb_json:
        recomb_x.append(int(recomb_obj[genome_build_vars[genome_build]['position']]) / 1000000.0)
        recomb_y.append(float(recomb_obj['rate']) / 100.0)

    data = {
        'x': x,
        'y': y,
        'qrs': q_rs,
        'q_alle': q_allele,
        'q_maf': q_maf,
        'prs': p_rs,
        'p_alle': p_allele,
        'p_maf': p_maf,
        'dist': dist,
        'r': r2_round,
        'd': d_prime_round,
        'alleles': corr_alleles,
        'forgedb':forgedb,
        'regdb': regdb,
        'funct': funct,
        'size': size,
        'color': color
    }
    source = ColumnDataSource(data)

    proxy_plot.line(recomb_x, recomb_y, line_width=1, color="black", alpha=0.5)
 # Add scatter plot with specific hover tool
    scatter_renderer = proxy_plot.scatter(x='x', y='y', size='size',
                                        color='color', alpha=0.5, source=source)

    # Create specific hover tool for scatter points only
    hover_tool = HoverTool(
        renderers=[scatter_renderer],
        tooltips=OrderedDict([
            ("Query Variant", "@qrs @q_alle"),
            ("Proxy Variant", "@prs @p_alle"),
            ("Distance (Mb)", "@dist"),
            ("MAF (Query,Proxy)", "@q_maf,@p_maf"),
            ("R" + sup_2, "@r"),
            ("D\'", "@d"),
            ("Correlated Alleles", "@alleles"),
            ("FORGEdb Score", "@forgedb"),
            ("RegulomeDB Rank", "@regdb"),
            ("Functional Class", "@funct"),
        ])
    )
    
    # Remove the default hover tool and add our specific one
    proxy_plot.tools = [tool for tool in proxy_plot.tools if not isinstance(tool, HoverTool)]
    proxy_plot.add_tools(hover_tool)

    if annotate == "regulome":
        proxy_plot.text(x, y, text=regdb, alpha=1, text_font_size="7pt",
                    text_baseline="middle", text_align="center", angle=0)
    elif annotate == "forge":
        proxy_plot.text(x, y, text=forgedb, alpha=1, text_font_size="7pt",
                    text_baseline="middle", text_align="center", angle=0)
   
    if r2_d == "r2":
        proxy_plot.yaxis.axis_label = "R" + sup_2
    else:
        proxy_plot.yaxis.axis_label = "D\'"

    proxy_plot.extra_y_ranges = {"y2_axis": Range1d(start=-3, end=103)}
    proxy_plot.add_layout(LinearAxis(y_range_name="y2_axis",
                                    axis_label="Combined Recombination Rate (cM/Mb)"), "right")

    # Rug Plot
    y2_ll = [-0.03] * len(x)
    y2_ul = [1.03] * len(x)
    yr_rug = Range1d(start=-0.03, end=1.03)

    data_rug = {
        'x': x,
        'y': y,
        'y2_ll': y2_ll,
        'y2_ul': y2_ul,
        'qrs': q_rs,
        'q_alle': q_allele,
        'q_maf': q_maf,
        'prs': p_rs,
        'p_alle': p_allele,
        'p_maf': p_maf,
        'dist': dist,
        'r': r2_round,
        'd': d_prime_round,
        'alleles': corr_alleles,
        'forgedb':forgedb,
        'regdb': regdb,
        'funct': funct,
        'size': size,
        'color': color
    }
    source_rug = ColumnDataSource(data_rug)

    rug = figure(
        x_range=xr, y_range=yr_rug, border_fill_color='white', y_axis_type=None,
        title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, 
        width=900, height=50, tools="xpan,tap")

    rug.segment(x0='x', y0='y2_ll', x1='x', y1='y2_ul', source=source_rug,
                color='color', alpha=0.5, line_width=1)
    rug.toolbar_location = None
    if collapseTranscript == "false":
        # Gene Plot (All Transcripts)
        print("Making request to export service for high quality images for all transcripts")
        genes_file = tmp_dir + "genes_" + request + ".json"
        genes_json = getRefGene(db, genes_file, snp_coord['chromosome'], int(coord1), int(coord2), genome_build, False)
        #genes_json = open(genes_file).readlines()
        genes_plot_start = []
        genes_plot_end = []
        genes_plot_y = []
        genes_plot_name = []
        exons_plot_x = []
        exons_plot_y = []
        exons_plot_w = []
        exons_plot_h = []
        exons_plot_name = []
        exons_plot_id = []
        exons_plot_exon = []
        lines = [0]
        gap = 80000
        tall = 0.75
        if genes_json != None and len(genes_json) > 0:
            for gene_obj in genes_json:
                bin = gene_obj["bin"]
                name_id = gene_obj["name"]
                chrom = gene_obj["chrom"]
                strand = gene_obj["strand"]
                txStart = gene_obj["txStart"]
                txEnd = gene_obj["txEnd"]
                cdsStart = gene_obj["cdsStart"]
                cdsEnd = gene_obj["cdsEnd"]
                exonCount = gene_obj["exonCount"]
                exonStarts = gene_obj["exonStarts"]
                exonEnds = gene_obj["exonEnds"]
                score = gene_obj["score"]
                name2 = gene_obj["name2"]
                cdsStartStat = gene_obj["cdsStartStat"]
                cdsEndStat = gene_obj["cdsEndStat"] 
                exonFrames = gene_obj["exonFrames"]
                name = name2
                id = name_id
                e_start = exonStarts.split(",")
                e_end = exonEnds.split(",")

                # Determine Y Coordinate
                i = 0
                y_coord = None
                while y_coord == None:
                    if i > len(lines) - 1:
                        y_coord = i + 1
                        lines.append(int(txEnd))
                    elif int(txStart) > (gap + lines[i]):
                        y_coord = i + 1
                        lines[i] = int(txEnd)
                    else:
                        i += 1

                genes_plot_start.append(int(txStart) / 1000000.0)
                genes_plot_end.append(int(txEnd) / 1000000.0)
                genes_plot_y.append(y_coord)
                genes_plot_name.append(name + "  ")

                for i in range(len(e_start) - 1):
                    if strand == "+":
                        exon = i + 1
                    else:
                        exon = len(e_start) - 1 - i

                    width = (int(e_end[i]) - int(e_start[i])) / 1000000.0
                    x_coord = int(e_start[i]) / 1000000.0 + (width / 2)

                    exons_plot_x.append(x_coord)
                    exons_plot_y.append(y_coord)
                    exons_plot_w.append(width)
                    exons_plot_h.append(tall)
                    exons_plot_name.append(name)
                    exons_plot_id.append(id)
                    exons_plot_exon.append(exon)

        n_rows = len(lines)
        genes_plot_yn = [n_rows - x + 0.5 for x in genes_plot_y]
        exons_plot_yn = [n_rows - x + 0.5 for x in exons_plot_y]
        yr2 = Range1d(start=0, end=n_rows)

        data_gene_plot = {
            'exons_plot_x': exons_plot_x,
            'exons_plot_yn': exons_plot_yn,
            'exons_plot_w': exons_plot_w,
            'exons_plot_h': exons_plot_h,
            'exons_plot_name': exons_plot_name,
            'exons_plot_id': exons_plot_id,
            'exons_plot_exon': exons_plot_exon
        }

        source_gene_plot = ColumnDataSource(data_gene_plot)
        
        if len(lines) < 3:
            plot_h_pix = 250
        else:
            plot_h_pix = 250 + (len(lines) - 2) * 50

        gene_plot = figure(
            x_range=xr, y_range=yr2, border_fill_color='white',
            title="", min_border_top=2, min_border_bottom=2, min_border_left=60, min_border_right=60, 
            width=900, height=plot_h_pix, tools="hover,tap,xpan,box_zoom,undo,redo,reset,save")

        gene_plot.segment(genes_plot_start, genes_plot_yn, genes_plot_end,
                        genes_plot_yn, color="black", alpha=1, line_width=2)

        gene_plot.rect(x='exons_plot_x', y='exons_plot_yn', width='exons_plot_w', height='exons_plot_h',
                    source=source_gene_plot, fill_color="grey", line_color="grey")
        gene_plot.xaxis.axis_label = "Chromosome " + snp_coord['chromosome'] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_plot.yaxis.axis_label = "Genes (All Transcripts)"
        gene_plot.ygrid.grid_line_color = None
        gene_plot.yaxis.axis_line_color = None
        gene_plot.yaxis.minor_tick_line_color = None
        gene_plot.yaxis.major_tick_line_color = None
        gene_plot.yaxis.major_label_text_color = None

        hover = gene_plot.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ("Gene", "@exons_plot_name"),
            ("ID", "@exons_plot_id"),
            ("Exon", "@exons_plot_exon"),
        ])

        gene_plot.text(genes_plot_start, genes_plot_yn, text=genes_plot_name, alpha=1, text_font_size="7pt",
                    text_font_style="bold", text_baseline="middle", text_align="right", angle=0)

        gene_plot.toolbar_location = "below"

        # Combine plots into a grid
        out_grid = gridplot([proxy_plot, rug, gene_plot], ncols=1, toolbar_options=dict(logo=None))
        return (out_grid,proxy_plot,gene_plot,rug,plot_h_pix)
    # Gene Plot (Collapsed)                        
    else:
        genes_c_file = tmp_dir + "genes_c_" + request + ".json"
        genes_c_json = getRefGene(db, genes_c_file, snp_coord['chromosome'], int(coord1), int(coord2), genome_build, True)
        #genes_c_json = open(genes_c_file).readlines()
        genes_c_plot_start=[]
        genes_c_plot_end=[]
        genes_c_plot_y=[]
        genes_c_plot_name=[]
        exons_c_plot_x=[]
        exons_c_plot_y=[]
        exons_c_plot_w=[]
        exons_c_plot_h=[]
        exons_c_plot_name=[]
        exons_c_plot_id=[]
        message_c = ["Too many genes to plot."]
        lines_c=[0]
        gap=80000
        tall=0.75
        if genes_c_json != None and len(genes_c_json) > 0:
            for gene_c_obj in genes_c_json:
                #gene_c_obj = json.loads(gene_c_raw_obj)
                chrom = gene_c_obj["chrom"]
                txStart = gene_c_obj["txStart"]
                txEnd = gene_c_obj["txEnd"]
                exonStarts = gene_c_obj["exonStarts"]
                exonEnds = gene_c_obj["exonEnds"]
                name2 = gene_c_obj["name2"]
                transcripts = gene_c_obj["transcripts"]
                name = name2
                e_start = exonStarts.split(",")
                e_end = exonEnds.split(",")
                e_transcripts=transcripts.split(",")

                # Determine Y Coordinate
                i=0
                y_coord=None
                while y_coord==None:
                    if i>len(lines_c)-1:
                        y_coord=i+1
                        lines_c.append(int(txEnd))
                    elif int(txStart)>(gap+lines_c[i]):
                        y_coord=i+1
                        lines_c[i]=int(txEnd)
                    else:
                        i+=1

                genes_c_plot_start.append(int(txStart)/1000000.0)
                genes_c_plot_end.append(int(txEnd)/1000000.0)
                genes_c_plot_y.append(y_coord)
                genes_c_plot_name.append(name+"  ")

                # for i in range(len(e_start)):
                for i in range(len(e_start)-1):
                    width=(int(e_end[i])-int(e_start[i]))/1000000.0
                    x_coord=int(e_start[i])/1000000.0+(width/2)

                    exons_c_plot_x.append(x_coord)
                    exons_c_plot_y.append(y_coord)
                    exons_c_plot_w.append(width)
                    exons_c_plot_h.append(tall)
                    exons_c_plot_name.append(name)
                    exons_c_plot_id.append(e_transcripts[i].replace("-",","))


        n_rows_c=len(lines_c)
        genes_c_plot_yn=[n_rows_c-x+0.5 for x in genes_c_plot_y]
        exons_c_plot_yn=[n_rows_c-x+0.5 for x in exons_c_plot_y]
        yr2_c=Range1d(start=0, end=n_rows_c)

        data_gene_c_plot = {'exons_c_plot_x': exons_c_plot_x, 'exons_c_plot_yn': exons_c_plot_yn, 'exons_c_plot_w': exons_c_plot_w, 'exons_c_plot_h': exons_c_plot_h, 'exons_c_plot_name': exons_c_plot_name, 'exons_c_plot_id': exons_c_plot_id}
        source_gene_c_plot=ColumnDataSource(data_gene_c_plot)

        max_genes_c = 40
        # if len(lines_c) < 3 or len(genes_c_raw) > max_genes_c:
        if len(lines_c) < 3:
            plot_h_pix = 250
        else:
            plot_h_pix = 250 + (len(lines_c) - 2) * 50

        gene_c_plot = figure(min_border_top=2, min_border_bottom=0, min_border_left=100, min_border_right=5,
                        x_range=xr, y_range=yr2_c, border_fill_color='white',
                        title="",  
                        width=900, height=plot_h_pix, tools="hover,xpan,box_zoom,wheel_zoom,tap,undo,redo,reset,save")

        # if len(genes_c_raw) <= max_genes_c:
        gene_c_plot.segment(genes_c_plot_start, genes_c_plot_yn, genes_c_plot_end,
                            genes_c_plot_yn, color="black", alpha=1, line_width=2)
        gene_c_plot.rect(x='exons_c_plot_x', y='exons_c_plot_yn', width='exons_c_plot_w', height='exons_c_plot_h',
                        source=source_gene_c_plot, fill_color="grey", line_color="grey")
        gene_c_plot.text(genes_c_plot_start, genes_c_plot_yn, text=genes_c_plot_name, alpha=1, text_font_size="7pt",
                        text_font_style="bold", text_baseline="middle", text_align="right", angle=0)
        hover = gene_c_plot.select(dict(type=HoverTool))
        hover.tooltips = OrderedDict([
            ("Gene", "@exons_c_plot_name"),
            ("Transcript IDs", "@exons_c_plot_id"),
        ])

        # else:
        # 	x_coord_text = coord1/1000000.0 + (coord2/1000000.0 - coord1/1000000.0) / 2.0
        # 	gene_c_plot.text(x_coord_text, n_rows_c / 2.0, text=message_c, alpha=1,
        # 				   text_font_size="12pt", text_font_style="bold", text_baseline="middle", text_align="center", angle=0)

        gene_c_plot.xaxis.axis_label = "Chromosome " + snp_coord['chromosome'] + " Coordinate (Mb)(" + genome_build_vars[genome_build]['title'] + ")"
        gene_c_plot.yaxis.axis_label = "Genes (Transcripts Collapsed)"
        gene_c_plot.ygrid.grid_line_color = None
        gene_c_plot.yaxis.axis_line_color = None
        gene_c_plot.yaxis.minor_tick_line_color = None
        gene_c_plot.yaxis.major_tick_line_color = None
        gene_c_plot.yaxis.major_label_text_color = None

        gene_c_plot.toolbar_location = "below"
        
        out_grid = gridplot([proxy_plot, rug, gene_c_plot], ncols=1, toolbar_options=dict(logo=None))
        return (out_grid,proxy_plot,gene_c_plot,rug,plot_h_pix)
