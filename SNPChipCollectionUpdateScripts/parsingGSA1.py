from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['snp_col']
#print(db.list_collection_names())
#print(collections)
i = 0
with open('GSA-24v1-0_C1.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if(line_count < 8):
            print('################ROW NUMBER ', line_count, '#####################')
            print(row)
        if(line_count >= 8 and len(row) > 10):
            temp = {}
            temp['platform'] = 'Illumina Global Screening Array version 1'
            temp['chr'] = row[9]
            pos = row[10]

            if(collections.find_one({'pos':pos})!=None):
                item = collections.find_one_and_delete({'pos':pos})['data']
                item.append(temp)
                collections.insert_one({'pos':pos, 'data':item})
            else:
                collections.insert_one({'pos':pos, 'data':[temp]})
        line_count += 1
    print(f'Processed {line_count} lines.')
