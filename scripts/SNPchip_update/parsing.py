from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['snp_col_test']
#print(db.list_collection_names())
#print(collections)
i = 0
#choose the csv file to open
with open('/users/yaox5/workspace/analysistools/rawData/GDAConfluence_20032938X375356_A1.csv') as csv_file:
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
            temp['platform'] = 'Illumina Global Diversity Array_Confluence'
            chr = row[9]
            genomebuild=row[8]
            temp['chr'] = chr
            temp['genome'] = genomebuild
            pos = row[10]
            if(collections.find_one({'pos':pos})!=None):
                item = collections.find_one_and_delete({'pos':pos})['data']
                item.append(temp)
                collections.insert_one({'pos':pos, 'data':item})
            else:
                collections.insert_one({'pos':pos, 'data':[temp]})
        line_count += 1
    print(f'Processed {line_count} lines.')