#!/usr/bin/env python

import sqlite3
import json
import os.path
import binascii
import yaml

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from time import gmtime, strftime


# Set data directories using config.yml
with open('config.yml', 'r') as f:
    config = yaml.load(f)
api_users_dir = config['data']['api_users_dir']

# email user token
def emailUser(email, token):
    print "sending message"
    packet = MIMEMultipart()
    packet['Subject'] = "API Access Token"
    packet['From'] = "LDlink" + " <do.not.reply@nih.gov>"
    packet['To'] = email

    message = "Token: " + token

    packet.attach(MIMEText(message, 'html'))

    # print self.MAIL_HOST
    # temp use localhost, use official NIH mailfwd account in future (put in config file)
    smtp = smtplib.SMTP("localhost")
    smtp.sendmail("do.not.reply@nih.gov", email, packet.as_string())

# creates table in database if database did not exist before
def createTable(api_users_dir):
    # create database
    con = sqlite3.connect(api_users_dir + 'api_users.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME);")
    con.commit()
    con.close()

# check if user email record exists
def getEmailRecord(curr, email):
    temp = (email,)
    curr.execute("SELECT * FROM api_users WHERE email=?", temp)
    return curr.fetchone()

# check if user email record exists
def insertRecord(curr, firstname, lastname, email, institution, token, registered):
    con = sqlite3.connect(api_users_dir + 'api_users.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (firstname, lastname, email, institution, token, registered)
    cur.execute(
        "INSERT INTO api_users (first_name, last_name, email, institution, token, registered) VALUES (?,?,?,?,?,?)", temp)
    con.commit()
    con.close()
    print "record inserted."

# check if token is already in db
def checkUniqueToken(curr, token):
    temp = (token,)
    curr.execute("SELECT * FROM api_users WHERE token=?", temp)
    if curr.fetchone() is None:
        return False
    else:
        return True

# check if token is valid when hitting API route
def checkToken(token):
    con = sqlite3.connect(api_users_dir + 'api_users.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (token,)
    cur.execute("SELECT * FROM api_users WHERE token=?", temp)
    record = cur.fetchone()
    con.close()
    if record is None:
        return False
    else:
        return True

# generate unique access token for each user
def generateToken(curr):
    token = binascii.b2a_hex(os.urandom(6))
    # if true, generate another token - make sure example token is not generated
    while(checkUniqueToken(curr, token) or token == "faketoken123"):
        token = binascii.b2a_hex(os.urandom(6))
    return token

# get current date and time
def getDatetime():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())

# registers new users and emails generated token
def register_user(firstname, lastname, email, institution, reference):
    tmp_dir = "./tmp/"

    out_json = {}

    # create database and table if it does not exist already
    if not os.path.exists(api_users_dir + 'api_users.db'):
        print "api_usrs.db created."
        createTable(api_users_dir)

    # Connect to snp database
    conn = sqlite3.connect(api_users_dir + 'api_users.db')
    conn.text_factory = str
    curr = conn.cursor()

    record = getEmailRecord(curr, email)
    print record
    # if email record exists, do not insert to db
    if record != None:
        out_json = {
            "message": "Email already registered.",
            "firstname": record[0],
            "lastname": record[1],
            "email": record[2],
            "institution": record[3],
            "token": record[4],
            "registered": record[5]
        }
        emailUser(record[2], record[4])
    else:
        # if email record does not exists in db, add to table
        token = generateToken(curr)
        registered = getDatetime()
        insertRecord(curr, firstname, lastname, email, institution, token, registered)
        out_json = {
            "message": "Thank you for registering to use the LDlink API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token,
            "registered": registered
        }
        emailUser(email, token)
        
    conn.close()
    # with open(tmp_dir + 'register_' + reference + '.json', 'w') as fp:
    #     json.dump(out_json, fp)
    return out_json
