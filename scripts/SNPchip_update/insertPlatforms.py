
import sys
#import os
#current = os.path.dirname(os.path.realpath(__file__))
#print(current)
#parent = os.path.dirname(current)
#parent = os.path.dirname(parent)
#ldlinkpath = parent+"/LDlink"
#sys.path.append(ldlinkpath)
from pymongo import MongoClient
#from LDlink.LDcommon import connectMongoDBReadOnly
import csv
client = MongoClient()
print(client)
db = client['LDLink']
#db = connectMongoDBReadOnly(False)
collections = db['platforms']
print(db,collections)
#collections.insert_one({'platform':'Illumina Global Screening version 1', 'code':'I_GSA-v1'})
#collections.insert_one({'platform':'Illumina Global Screening version 2', 'code':'I_GSA-v2'})
#collections.insert_one({'platform':'Illumina Multi-Ethnic Global', 'code':'I_MEGA'})
#collections.insert_one({'platform':'Affymetrix Axiom UK Biobank', 'code':'A_UKBA'})
#collections.insert_one({'platform':'Affymetrix Axiom Precision Medicine Research', 'code':'A_PMRA'})
#add additional arrays for SNPchip 10/05/2022
collections.insert_one({'platform':'Illumina Global Diversity Array_Confluence', 'code':'I_GDA-C'})
collections.insert_one({'platform':'Illumina Global Screening version 3_Confluence', 'code':'I_GSA-v3C'})