#!/usr/bin/env python

###########
# SNPchip #
###########

from pymongo import MongoClient
import os
import bson.regex
import json
import json,operator,sqlite3,os

# Create SNPchip function
def calculate_chip(snplst,request):
	contents=open("SNP_Query_loginInfo.txt").read().split('\n')
	username=contents[0].split('=')[1]
	password=contents[1].split('=')[1]
	Database=contents[2].split('=')[1]
	# Set data directories
	data_dir="/local/content/ldlink/data/"
	snp_dir=data_dir+"snp142/snp142_annot_2.db"
	array_dir=data_dir+"arrays/snp142_arrays.db"
	tmp_dir="./tmp/"
	
	# Ensure tmp directory exists
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)
	
	# Create JSON output
	out_json=open(tmp_dir+'proxy'+request+".json","w")
	output={}
	
	# Open SNP list file
	snps_raw=open(snplst).readlines()
	if len(snps_raw)>1000:
		output["error"]="Maximum SNP list is 1,000 RS numbers. Your list contains "+str(len(snps_raw))+" entries."
		return(json.dumps(output, sort_keys=True, indent=2))
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
						if snp_coord[1]=="X":
							chr=23
						elif snp_coord[1]=="Y":
							chr=24
						else:
							chr=int(snp_coord[1])
						temp=[snp_i[0],chr,int(snp_coord[2])]
						snp_coords.append(temp)
					else:
						warn.append(snp_i[0])
				else:
					warn.append(snp_i[0])
			else:
				warn.append(snp_i[0])
	
	
	if warn!=[]:
		output["warning"]="The following RS numbers were not found in dbSNP 142: "+",".join(warn)
	
	if len(rs_nums)==0:
		output["error"]="Input SNP list does not contain any valid RS numbers that are in dbSNP 142."
		return(json.dumps(output, sort_keys=True, indent=2))
		raise
	

	# Sort by chromosome and then position
	snp_coords_sort=sorted(snp_coords, key=operator.itemgetter(1,2))
	
	# Convert chromosome 23 and 24 back to X and Y
	for i in range(len(snp_coords_sort)):
		if snp_coords_sort[i][1]==23:
			snp_coords_sort[i][1]="X"
		elif snp_coords_sort[i][1]==24:
			snp_coords_sort[i][1]="Y"
		else:
			snp_coords_sort[i][1]=str(snp_coords_sort[i][1])
	
	
	client = MongoClient()
	client = MongoClient('localhost', 27017)
	
        client.admin.authenticate(username, password, mechanism='SCRAM-SHA-1')
	db = client[Database]

	#Quering MongoDB to get platforms for position/chromsome pairs 
	for k in range(len(snp_coords_sort)):
		position=str(snp_coords_sort[k][2])
		Chr=str(snp_coords_sort[k][1])
		cursor=db.snp_col.find( {'$and':[{"pos": position},{"data.chr":Chr},{"data.platform": { '$regex': '.*'}}]} ) #Json object that stores all the results
		platforms=[]
		#Parsing each docuemnt to retrieve platforms 
		for document in cursor:	
			for z in range(0,len(document["data"])):
				if(document["data"][z]["chr"]==Chr):
					platforms.append(document["data"][z]["platform"])
		output['snp_'+str(k)]=[str(snp_coords_sort[k][0]),snp_coords_sort[k][1]+":"+str(snp_coords_sort[k][2]),','.join(platforms)]
	# Output JSON file
	json_output=json.dumps(output, sort_keys=True, indent=2)
	print >> out_json, json_output
	return json_output
	out_json.close()


def main():
	import json,sys
	
	# Import SNPchip options
	if len(sys.argv)==3:
		snplst=sys.argv[1]
		request=sys.argv[2]
	else:
		print "Correct useage is: SNPclip.py snplst request"
		sys.exit()
		
	
	# Run function
	calculate_chip(snplst,request)
	
	
	# Print output
	with open("./tmp/proxy"+request+".json") as out_json:
		json_dict=json.load(out_json)
	
	
	try:
		json_dict["error"]
	
	except KeyError:
		print ""
		header=["SNP","Position (GRCh37)","Arrays"]
		print "\t".join(header)
		for k in sorted(json_dict.keys()):
			if k!="error" and k!="warning":
				print "\t".join(json_dict[k])

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
