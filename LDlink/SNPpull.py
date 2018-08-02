import yaml
#!/usr/bin/env python

###########
# SNPpull #  Pull a list of SNPs from a VCF file
###########

# Create SNPpull function
def calculate_pull(snplst,request):
	import json,math,operator,os,sqlite3,subprocess,sys

	# Set data directories
	# data_dir="/local/content/ldlink/data/"
	# gene_dir=data_dir+"refGene/sorted_refGene.txt.gz"
	# snp_dir=data_dir+"snp142/snp142_annot_2.db"
	# pop_dir=data_dir+"1000G/Phase3/samples/"
	# vcf_dir=data_dir+"1000G/Phase3/genotypes/ALL.chr"

	# Set data directories using config.yml
	with open('config.yml', 'r') as f:
		config = yaml.load(f)
	gene_dir=config['data']['gene_dir']
	snp_dir=config['data']['snp_dir']
	pop_dir=config['data']['pop_dir']
	vcf_dir=config['data']['vcf_dir']

	tmp_dir="./tmp/"


	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)


	# Create JSON output
	out_json=open(tmp_dir+"pull"+request+".json","w")
	output={}


	# Open SNP list file
	snps_raw=open(snplst).readlines()
	max_list=5000
	if len(snps_raw)>max_list:
		output["error"]="Maximum SNP list is "+str(max_list)+" RS numbers. Your list contains "+str(len(snps_raw))+" entries."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("","","")
		raise
	
	# Remove duplicate RS numbers
	snps=[]
	for snp_raw in snps_raw:
		snp=snp_raw.strip().split()
		if snp not in snps:
			snps.append(snp)
	
	# Connect to snp142 database
	conn=sqlite3.connect(snp_dir)
	conn.text_factory=str
	cur=conn.cursor()
	
	def get_coords(rs):
		id=rs.strip("rs")
		t=(id,)
		cur.execute("SELECT * FROM tbl_"+id[-1]+" WHERE id=?", t)
		return cur.fetchone()


	# Find RS numbers in snp142 database
	details={}
	rs_nums=[]
	snp_pos=[]
	snp_coords=[]
	warn=[]
	tabix_coords=""
	for snp_i in snps:
		if len(snp_i)>0:
			if len(snp_i[0])>2:
				if snp_i[0][0:2]=="rs" and snp_i[0][-1].isdigit():
					snp_coord=get_coords(snp_i[0])
					if snp_coord!=None:
						rs_nums.append(snp_i[0])
						snp_pos.append(snp_coord[2])
						temp=[snp_i[0],snp_coord[1],snp_coord[2]]
						snp_coords.append(temp)
					else:
						warn.append(snp_i[0])
						details[snp_i[0]]="SNP not found in dbSNP142, SNP removed."
				else:
					warn.append(snp_i[0])
					details[snp_i[0]]="Not an RS number, query removed."
			else:
				warn.append(snp_i[0])
				details[snp_i[0]]="Not an RS number, query removed."
		else:
			warn.append(snp_i[0])
			details[snp_i[0]]="Not an RS number, query removed."

	# Close snp142 connection
	cur.close()
	conn.close()
	
	if warn!=[]:
		output["warning"]="The following RS number(s) or coordinate(s) were not found in dbSNP 142: "+",".join(warn)
			
	
	if len(rs_nums)==0:
		output["error"]="Input SNP list does not contain any valid RS numbers that are in dbSNP 142."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("","","")
		raise		
	
	# Check SNPs are all on the same chromosome
	for i in range(len(snp_coords)):
		if snp_coords[0][1]!=snp_coords[i][1]:
			output["error"]="Not all input SNPs are on the same chromosome: "+snp_coords[i-1][0]+"=chr"+str(snp_coords[i-1][1])+":"+str(snp_coords[i-1][2])+", "+snp_coords[i][0]+"=chr"+str(snp_coords[i][1])+":"+str(snp_coords[i][2])+"."
			json_output=json.dumps(output, sort_keys=True, indent=2)
			print >> out_json, json_output
			out_json.close()
			return("","","")
			raise
	
	
	# Sort coordinates and make tabix formatted coordinates
	snp_pos_int=[int(i) for i in snp_pos]
	snp_pos_int.sort()
	snp_coord_str=[snp_coords[0][1]+":"+str(i)+"-"+str(i) for i in snp_pos_int]
	tabix_coords=" "+" ".join(snp_coord_str)
	

	# Extract 1000 Genomes phased genotypes
	vcf_file=vcf_dir+snp_coords[0][1]+".phase3_shapeit2_mvncall_integrated_v5.20130502.genotypes.vcf.gz"
	tabix_snps="tabix -fh {0}{1} | grep -v -e END".format(vcf_file, tabix_coords)
	proc=subprocess.Popen(tabix_snps, shell=True, stdout=subprocess.PIPE)
	
	
	# Import SNP VCF files
	vcf=proc.stdout.readlines()
	
	
	# Return output
	json_output=json.dumps(output, sort_keys=True, indent=2)
	print >> out_json, json_output
	out_json.close()
	return(snps,vcf)


def main():
	import json,sys
	tmp_dir="./tmp/"

	# Import SNPclip options
	if len(sys.argv)==3:
		snplst=sys.argv[1]
		request=sys.argv[2]
	else:
		print "Correct useage is: SNPpull.py snplst request"
		sys.exit()


	# Run function
	snps,vcf=calculate_pull(snplst,request)


	# Print output
	with open(tmp_dir+"pull"+request+".json") as f:
		json_dict=json.load(f)

	try:
		json_dict["error"]

	except KeyError:
		for line in vcf:
			print line.strip("\n")
		
		try:
			json_dict["warning"]

		except KeyError:
			print ""
		else:
			print ""
			print "WARNING: "+json_dict["warning"]+"!"
			print ""

	else:
		print ""
		print json_dict["error"]
		print ""

if __name__ == "__main__":
	main()
