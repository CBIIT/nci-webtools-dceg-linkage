from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['snp_col']
#print(db.list_collection_names())
#print(collections)
i = 0
with open('Axiom_PMRA.na35.annot.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if(line_count < 20):
            print('################ROW NUMBER ', line_count, '#####################')
            print(row)
        if(line_count >= 20 and len(row) > 5):
            temp = {}
            temp['platform'] = 'Affymetrix Axiom Precision Medicine Research Array'
            temp['chr'] = row[4]
            pos = row[5]
            if(collections.find_one({'pos':pos})!=None):
                item = collections.find_one_and_delete({'pos':pos})['data']
                item.append(temp)
                collections.insert_one({'pos':pos, 'data':item})
            else:
                collections.insert_one({'pos':pos, 'data':[temp]})
        line_count += 1
    print(f'Processed {line_count} lines.')
