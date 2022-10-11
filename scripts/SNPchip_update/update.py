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
# GDAConfluence_20032938X375356_A1 (Illumina Global Diversity Array_Confluence)
#GSAv3Confluence_20032937X371431_A2 (Illumina Global Screening version 3_Confluence)
with open('/users/yaox5/workspace/analysistools/rawData/GSAv3Confluence_20032937X371431_A2.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    count38 = 0
    count37 = 0
    found37 = 0
    found38 = 0
    newcount = 0
    updatecount = 0
    countdup = 0
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
                count37 += 1
                temp["position_grch37"] = pos
                result = collections.find_one({'position_grch37':pos,'chromosome_grch37':chr})
                if result != None:
                    found37 +=1
            if genomebuild == "38":
                count38 += 1
                temp["position_grch38"] = pos
                result = collections.find_one({'position_grch38':pos,'chromosome_grch38':chr})
                if result != None:
                    found38 +=1
            temp['chromosome_grch37'] = chr
            temp['chromosome_grch38'] = chr
            temp['data'] = platformlist
            if(result!=None):
                updatecount += 1
                if platformitem not in result["data"]:
                    #print(result)
                    collections.update_one({'_id':result["_id"]},{"$push":{"data":platformitem}})
                else:
                    countdup += 1
            else:
                temp["position_grch38"] = temp["position_grch38"] if "position_grch38" in temp else None
                if temp["position_grch37"] != None or temp["position_grch38"] != None:
                    collections.insert_one(temp)
                    newcount += 1
        line_count += 1
        if (line_count % 100000 == 0):
            print(line_count)
    print(f'GSAv3Confluence_20032937X371431_A2:Processed {line_count} lines. update:{updatecount} new:{newcount} 38:{count38} 37:{count37} found37:{found37} found38:{found38} dup:{countdup}')