from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['platforms']
collections.insert_one({'platform':'Illumina Global Screening Array version 1', 'code':'I_GSA-v1'})
collections.insert_one({'platform':'Illumina Global Screening Array version 2', 'code':'I_GSA-v2'})
collections.insert_one({'platform':'Illumina Multi-Ethnic Global Array', 'code':'I_MEGA'})
collections.insert_one({'platform':'Affymetrix Axiom UK Biobank Array', 'code':'A_UKBA'})
collections.insert_one({'platform':'Affymetrix Axiom Precision Medicine Research Array', 'code':'A_PMRA'})
