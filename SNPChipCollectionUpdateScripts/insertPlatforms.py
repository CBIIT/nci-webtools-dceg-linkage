from pymongo import MongoClient
import csv
client = MongoClient()
print(client)
db = client['LDLink']
collections = db['platforms']
collections.insert_one({'platform':'Illumina Global Screening Array version 1', 'code':'C1'})
collections.insert_one({'platform':'Illumina Global Screening Array version 2', 'code':'A1'})
collections.insert_one({'platform':'Illumina Multi-Ethnic Global Array', 'code':'D1'})
collections.insert_one({'platform':'Affymetrix Axiom UK Biobank Array', 'code':'UKB_WCSG'})
collections.insert_one({'platform':'Affymetrix Axiom Precision Medicine Research Array', 'code':'PMRA'})
