import yaml
#!/usr/bin/env python

# SNPcoord
# Locate genomic location and SNP annotation

# Create SNPcoord function
def calculate_tip(snplst,request):
	import json,math,operator,os,sqlite3,subprocess,sys
	max_list=500000

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
	out_json=open(tmp_dir+"matrix"+request+".json","w")
	output={}


	# Open SNP list file
	snps_raw=open(snplst).readlines()
	if len(snps_raw)>max_list:
		output["error"]="Maximum SNP list is "+str(max_list)+" RS numbers. Your list contains "+str(len(snps_raw))+" entries."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("")
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
	snp_coords=[]
	warn=[]
	for snp_i in snps:
		if len(snp_i)>0:
			if len(snp_i[0])>2:
				if snp_i[0][0:2]=="rs" and snp_i[0][-1].isdigit():
					snp_coord=get_coords(snp_i[0])
					if snp_coord!=None:
						chr=snp_coord[1]
						if chr=="X":
							chr="23"
						if chr=="Y":
							chr="24"
						temp=[snp_i[0],int(chr),int(snp_coord[2])]
						snp_coords.append(temp)
					else:
						warn.append(snp_i[0])
				else:
					warn.append(snp_i[0])
			else:
				warn.append(snp_i[0])
	
	# Close snp142 connection
	cur.close()
	conn.close()
	
	if warn!=[]:
		output["warning"]="The following RS numbers were not found in dbSNP 142: "+",".join(warn)
	
	if len(snp_coords)==0:
		output["error"]="Input SNP list does not contain any valid RS numbers that are in dbSNP 142."
		json_output=json.dumps(output, sort_keys=True, indent=2)
		print >> out_json, json_output
		out_json.close()
		return("")
		raise		
	
	# Sort by chromosome and position
	from operator import itemgetter
	snp_sorted=sorted(snp_coords, key=itemgetter(1,2))
	
	# Convert back to X and Y
	snp_sorted_chr=[]
	for i in snp_sorted:
		if i[1]==23:
			chr="X"
		elif i[1]==24:
			chr="Y"
		else:
			chr=i[1]
		temp=[i[0],str(chr),str(i[2])]
		snp_sorted_chr.append(temp)
	
	
	# Return output
	json_output=json.dumps(output, sort_keys=True, indent=2)
	print >> out_json, json_output
	out_json.close()
	return(snp_sorted_chr)



def main():
	import json,sys
	tmp_dir="./tmp/"

	# Import LDmatrix options
	if len(sys.argv)==3:
		snplst=sys.argv[1]
		request=sys.argv[2]
	else:
		print "Correct useage is: SNPcoord.py snplst request"
		sys.exit()


	# Run function
	out_info=calculate_tip(snplst,request)


	# Print output
	with open(tmp_dir+"matrix"+request+".json") as f:
		json_dict=json.load(f)

	try:
		json_dict["error"]

	except KeyError:
		print ""
		header="RS Number\tChromosome\tPosition(GRCh37)"
		print header
		for i in out_info:
			print "\t".join(i)

		try:
			json_dict["warning"]

		except KeyError:
			print ""
		else:
			print ""
			print "WARNING: "+json_dict["warning"]+"."
			print ""

	else:
		print ""
		print json_dict["error"]
		print ""

if __name__ == "__main__":
	main()