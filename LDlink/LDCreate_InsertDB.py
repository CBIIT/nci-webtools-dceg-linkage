from pymongo import MongoClient
import os
import csv
import sys, getopt



#Usr input: File (---file) or Folder (--folder)
#User input: user name for mongo (--user) and password (--password)

def main(argv):


	# Open Database
	user=""
	password=""
	multiple=False
	input=""
	opts, args = getopt.getopt(argv,"upf:upd",["file=","folder=","user=","password="])
	for opt, arg in opts:                
	        if opt in ("d","--folder"):
    			multiple=True
    			input=arg
	        elif opt in ("f","--file"):
	        	multiple=False
	        	input=arg 
	        elif opt in ("u","--user"): 
	            user=arg
	        elif opt in ("p","--password"): 
	            password=arg
	client = MongoClient('localhost', 27017)
	client.admin.authenticate(user, password, mechanism='SCRAM-SHA-1')
	db = client.LDLink_sandbox

	if(multiple==True):
		Multi(input,db)              
	else:
		Single(input,db)
	
#if inserting a folder
def Multi(folder,db):
	
	# Manifest Info
	manifest_file=os.listdir(folder)
	manifest=[]
	for k in range(0,len(manifest_file)):
		file_name=os.path.splitext(manifest_file[k])[0]
		manifest.append(file_name)
		manifest_file[k]=folder+manifest_file[k]

	for i in range(len(manifest)):
		Insert(manifest_file[i],manifest[i],db)			
		
#If inserting a single file
def Single(file,db):
	file_name=os.path.splitext(file)[0]
	Insert(file,file_name,db)

#Insert function: Inserts position and chromsome/platform pairs for each position
def Insert(file,platform,db):
	db.snp_col.create_index("pos")
	snp_data=csv.reader(open(file))			
	for coord in snp_data:
		Chr=coord[0].split(":")[0].strip("chr")
		position=coord[0].split("-")[1]
		db.snp_col.update(
    		{ "pos": position },
    		{ "$addToSet" : { "data" : { "$each" :[ { "chr" : Chr, "platform" :platform} ] } } },
    		upsert=True,
		)

main(sys.argv[1:])
