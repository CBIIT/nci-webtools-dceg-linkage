from platform import platform
from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['snp_col']
#print(db.list_collection_names())
#print(collections)
i = 0
#choose the csv file to open
with open('/users/yaox5/workspace/analysistools/rawData/GSAv3Confluence_20032937X371431_A2.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        #can remove -> just prints the first 8 rows
        if(line_count < 8):
            print('################ROW NUMBER ', line_count, '#####################')
            print(row)

        #this is where the data starts, change based on file
        if(line_count >= 8 and len(row) > 10):
            temp = {}
            newplatform = 'Illumina Global Screening version 3_Confluence'
            chr = row[9]
            genomebuild=row[8]
            pos = int(row[10])
            platformitem= {'platform':newplatform}
            platformlist = []
            platformlist.append(platformitem) 
            
            if genomebuild == "37":
                temp["position_grch37"] = pos
                result = collections.find_one({'position_grch37':pos,'chromosome_grch37':chr})
            if genomebuild == "38":
                temp["position_grch38"] = pos
                result = collections.find_one({'position_grch38':pos,'chromosome_grch38':chr})
            temp['chromosome_grch37'] = chr
            temp['chromosome_grch38'] = chr
            temp['data'] = platformlist
            if(result!=None):
                collections.update_one({'_id':result["_id"]},{"$push":{"data":platformitem}})
            else:
                temp["position_grch38"] =''
                collections.insert_one(temp)
        line_count += 1
        if (line_count % 10000 == 0):
            print(line_count)
    print(f'Processed {line_count} lines.')