#!/usr/bin/env python

import sqlite3
import json
import os.path
import binascii
import yaml


# creates table in database if database did not exist before
def createTable(api_users_dir):
    # create database
    con = sqlite3.connect(api_users_dir + 'api_users.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute("CREATE TABLE `users` (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT);")
    con.close()

# check if user email record exists
def getEmailRecord(cur, email):
    temp = (email,)
    cur.execute("SELECT * FROM users WHERE email=?", temp)
    return cur.fetchone()

# check if user email record exists
def insertRecord(cur, first_name, lastname, email, institution, token):
    temp = (first_name, lastname, email, institution, token)
    cur.execute("INSERT INTO users VALUES (?,?,?,?,?)", temp)

# check if token is already in db
def checkUniqueToken(cur, token):
    temp = (token,)
    cur.execute("SELECT * FROM users WHERE token=?", temp)
    if cur.fetchone() is None:
        return False
    else:
        return True

# generate unique access token for each user
def generateToken(cur):
    token = binascii.b2a_hex(os.urandom(6))
    while(checkUniqueToken(cur, token)):
        token = binascii.b2a_hex(os.urandom(6))
    return token

def register_user(firstname, lastname, email, institution, reference):
    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_users_dir = config['data']['api_users_dir']

    tmp_dir = "./tmp/"

    out_json = {}

    # create database and table if it does not exist already
    if not os.path.exists(api_users_dir + 'api_users.db'):
        createTable(api_users_dir)

    # Connect to snp database
    conn = sqlite3.connect(api_users_dir + 'api_users.db')
    conn.text_factory = str
    cur = conn.cursor()

    record = getEmailRecord(cur, email)
    # if email record does not exists in db, add to table
    if record is None:
        token = generateToken(cur)
        insertRecord(cur, firstname, lastname, email, institution, token)
        out_json = {
            "message": "Congratulations! You have registered to use LDlink's API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token
        }
    else:
        # if email record exists, do not insert to db
        out_json = {
            "message": "Email already registered.",
            "firstname": record[0],
            "lastname": record[1],
            "email": record[2],
            "institution": record[3],
            "token": record[4]
        }

    with open(tmp_dir + 'register_' + reference + '.json', 'w') as fp:
        json.dump(out_json, fp)

    return out_json
