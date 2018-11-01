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

import datetime


# Set data directories using config.yml
with open('config.yml', 'r') as f:
    config = yaml.load(f)
api_users_dir = config['data']['api_users_dir']

# email user token
def emailUser(email, token, expiration):
    print "sending message"
    packet = MIMEMultipart()
    packet['Subject'] = "API Access Token"
    packet['From'] = "LDlink" + " <do.not.reply@nih.gov>"
    packet['To'] = email

    message = 'Token: ' + token + '<br>' + 'Your token expires on: ' + expiration

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
        "CREATE TABLE api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `expiration` DATETIME);")
    con.commit()
    con.close()

# check if user email record exists
def getEmailRecord(curr, email):
    temp = (email,)
    curr.execute("SELECT * FROM api_users WHERE email=?", temp)
    return curr.fetchone()


def insertRecord(firstname, lastname, email, institution, token, registered, expiration):
    con = sqlite3.connect(api_users_dir + 'api_users.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (firstname, lastname, email, institution, token, registered, expiration)
    cur.execute(
        "INSERT INTO api_users (first_name, last_name, email, institution, token, registered, expiration) VALUES (?,?,?,?,?,?,?)", temp)
    con.commit()
    con.close()

# delete record only if api token is hit and expired
def deleteRecord(email):
    con = sqlite3.connect(api_users_dir + 'api_users.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (email,)
    cur.execute(
        "DELETE FROM api_users WHERE email=?", temp)
    con.commit()
    con.close()

# check if token is already in db
def checkUniqueToken(curr, token):
    temp = (token,)
    curr.execute("SELECT * FROM api_users WHERE token=?", temp)
    if curr.fetchone() is None:
        return False
    else:
        return True

# check if token is valid when hitting API route and not expired
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
        # return True
        present = getDatetime()
        expiration = datetime.datetime.strptime(record[6], "%Y-%m-%d %H:%M:%S")
        if (present < expiration):
            return True
        else:
            # deleteRecord(record[2])
            return False

# generate unique access token for each user
def generateToken(curr):
    token = binascii.b2a_hex(os.urandom(6))
    # if true, generate another token - make sure example token is not generated
    while(checkUniqueToken(curr, token) or token == "faketoken123"):
        token = binascii.b2a_hex(os.urandom(6))
    return token

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# get current date and time
def getExpiration(registered):
    return registered + datetime.timedelta(minutes=5)

# registers new users and emails generated token for WEB
def register_user_web(firstname, lastname, email, institution, reference):
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
            "registered": record[5],
            "expiration": record[6]
        }
        emailUser(record[2], record[4], record[6])
    else:
        # if email record does not exists in db, add to table
        token = generateToken(curr)
        registered = getDatetime()
        expiration = getExpiration(registered)
        format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
        insertRecord(firstname, lastname, email, institution, token, format_registered, format_expiration)
        out_json = {
            "message": "Thank you for registering to use the LDlink API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token,
            "registered": format_registered,
            "expiration": format_expiration
        }
        emailUser(email, token, format_expiration)

    conn.close()
    return out_json

# registers new users and emails generated token for API
def register_user_api(firstname, lastname, email, institution, token, registered, expiration):
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

    # if email record exists, do not insert to db
    if record != None:
        out_json = {
            "message": "Email already registered.",
            "firstname": record[0],
            "lastname": record[1],
            "email": record[2],
            "institution": record[3],
            "token": record[4],
            "registered": record[5],
            "expiration": record[6]
        }
    else:
        # if email record does not exists in db, add to table
        # token = generateToken(curr)
        # registered = getDatetime()
        # expiration = getExpiration(registered)
        # format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        # format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
        insertRecord(firstname, lastname, email, institution, token, registered, expiration)
        out_json = {
            "message": "Thank you for registering to use the LDlink API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token,
            "registered": registered,
            "expiration": expiration
        }

    conn.close()
    return out_json