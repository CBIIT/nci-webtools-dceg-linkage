from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['platforms']
collections.insert_one({'platform':'Illumina Global Screening version 1', 'code':'I_GSA-v1'})
collections.insert_one({'platform':'Illumina Global Screening version 2', 'code':'I_GSA-v2'})
collections.insert_one({'platform':'Illumina Multi-Ethnic Global', 'code':'I_MEGA'})
collections.insert_one({'platform':'Affymetrix Axiom UK Biobank', 'code':'A_UKBA'})
collections.insert_one({'platform':'Affymetrix Axiom Precision Medicine Research', 'code':'A_PMRA'})
