#!/usr/bin/env python3
import os
import sqlite3
import pymongo

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def regulomeToMongo(conn):
   
    myclient = pymongo.MongoClient('localhost', 27017)
    mydb = myclient['sqliteData']
    chrCollection = mydb["regulome"]
    chrJSON = []

    cur = conn.cursor()

    tableNames = ["chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8",
                  "chr9", "chr10", "chr11", "chr12", "chr13", "chr14", "chr15", "chr16",
                  "chr17", "chr18", "chr19", "chr20", "chr21", "chr22", "chrX", "chrY"]

    for tableName in tableNames:
        cur.execute("SELECT * FROM " + tableName)
        rows = cur.fetchall()

        print("processing "  + tableName)

        for row in rows:
            chrRecord = { 
                "chromosome": tableName,
                "position": row[0], 
                "score": row[1]
            }
            chrJSON.append(chrRecord)
            
    print("inserting many... regulome record count: " + str(len(chrJSON)))
     
    chrCollection.insert_many(chrJSON)
    resp = chrCollection.create_index(
        [
            ("chromosome", 1),
            ("position", 1)
        ])    
    print(mydb.regulome.count())

    return

def geneNamesToMongo(conn):
   
    myclient = pymongo.MongoClient('localhost', 27017)
    mydb = myclient['sqliteData']
    geneCollection = mydb["genes"]
    geneJSON = []

    cur = conn.cursor()

    cur.execute("SELECT * FROM genes")
    rows = cur.fetchall()

    print("processing genes table")

    for row in rows:
        geneRecord = { 
            "name": row[0],
            "chromosome": row[1],
            "begin": row[2], 
            "end": row[3]
        }
        geneJSON.append(geneRecord)
            
    print("inserting many... gene record count: " + str(len(geneJSON)))
     
    geneCollection.insert_many(geneJSON)   
    print(mydb.genes.count())

    return    

      

def main():
    regulomeDatabase = os.path.expanduser("~/Documents/GithubProjects/nci-webtools-dceg-linkage/data/sqlite/regulomedb/regulomedb.db")
    geneNamesDatabase = os.path.expanduser("~/Documents/GithubProjects/nci-webtools-dceg-linkage/data/sqlite/refGene/gene_names_coords.db")

    # create regulome sqlite database connection
    conn = create_connection(regulomeDatabase)
    with conn:
        regulomeToMongo(conn)

    # create geneNames sqlite database connection
    conn = create_connection(geneNamesDatabase)
    with conn:
        geneNamesToMongo(conn)


if __name__ == '__main__':
    main()