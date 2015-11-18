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
	contents=open("platforms_abbr.txt").read().split('\n')
	dictionary = {}
	#Storing abbreviations in a dictionary to store in database
	for i in range(len(contents)):
		desciption=contents[i].split('\t')[0]
		abbr=contents[i].split('\t')[1]
		dictionary[desciption] = abbr
	if(multiple==True):
		Multi(input,db,dictionary)              
	else:
		Single(input,db,dictionary)
	
#if inserting a folder
def Multi(folder,db,dictionary):
	
	# Manifest Info
	manifest_file=os.listdir(folder)
	manifest=[]
	for k in range(0,len(manifest_file)):
		file_name=os.path.splitext(manifest_file[k])[0]
		manifest.append(file_name)
		manifest_file[k]=folder+manifest_file[k]

	for i in range(len(manifest)):
		Insert(manifest_file[i],db,dictionary)			
		
#If inserting a single file
def Single(file,db,dictionary):
	Insert(file,db)

def Insert_Platform(platform,dictionary,db):
	db.platforms.update(
		{ "platform": platform},
		{ "$set" : { "code":"" }},
		upsert=True,
	)
	if platform in dictionary:
		db.platforms.update(
			{ "platform": platform},
			{ "$set" : { "code" : dictionary[platform]} },
			upsert=True,
		)
	
#Insert function: Inserts position and chromsome/platform pairs for each position
def Insert(file,db,dictionary):
	db.snp_col.create_index("pos")
	snp_data=csv.reader(open(file))
	platform=(os.path.splitext(os.path.basename(file))[0])
	platform=platform[:-8]
	print platform
	Insert_Platform(platform,dictionary,db)
#	for coord in snp_data:
#		Chr=coord[0].split(":")[0].strip("chr")
#		position=coord[0].split("-")[1]
#		db.snp_col.update(
#    		{ "pos": position },
#    		{ "$addToSet" : { "data" : { "$each" :[ { "chr" : Chr, "platform" :platform} ] } } },
#    		upsert=True,
#		)
#	print "finished "+platform

main(sys.argv[1:])


