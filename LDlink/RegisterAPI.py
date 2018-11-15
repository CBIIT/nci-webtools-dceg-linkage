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

# blocked users attribute: 0=false, 1=true

# email user token
def emailUser(email, token, expiration, firstname, token_expiration, email_account):
    print "sending message"
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token"
    # packet['From'] = "LDlink" + " <do.not.reply@nih.gov>"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    message = ''
    if token_expiration:
        message = 'Dear ' + firstname + ', ' + '<br><br>' + 'Thank you for registering to use the LDlink API! <br><br>' + 'Your token is: ' + token + '<br>' + 'Your token expires on: ' + expiration + '<br><br>' + 'Please include this token as part of the submitted argument in your LDlink API requests. Examples of how to use a LDlink token are described in the <a href="https://ldlink.nci.nih.gov/?tab=apiaccess"><u>API Access</u></a> tab. Please do not share this token with other users as misuse of this token will result in potential blocking or termination of API use. <br><br>Thanks again for your interest in LDlink,<br><br>' + 'LDlink Web Admin'
    else:
        message = 'Dear ' + firstname + ', ' + '<br><br>' + 'Thank you for registering to use the LDlink API! <br><br>' + 'Your token is: ' + token + '<br><br>' + 'Please include this token as part of the submitted argument in your LDlink API requests. Examples of how to use a LDlink token are described in the <a href="https://ldlink.nci.nih.gov/?tab=apiaccess"><u>API Access</u></a> tab. Please do not share this token with other users as misuse of this token will result in potential blocking or termination of API use. <br><br>Thanks again for your interest in LDlink,<br><br>' + 'LDlink Web Admin'

    packet.attach(MIMEText(message, 'html'))

    # print self.MAIL_HOST
    # temp use localhost, use official NIH mailfwd account in future (put in config file)
    smtp = smtplib.SMTP(email_account)
    # smtp.sendmail("do.not.reply@nih.gov", email, packet.as_string())
    smtp.sendmail("NCILDlinkWebAdmin@mail.nih.gov", email, packet.as_string())

def emailJustification(firstname, lastname, email, institution, token, registered, blocked, justification):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    admin_token = config['api']['admin_token']
    email_account = config['api']['email_account']
    admin_email_list = config['api']['admin_email_list']
    print "sending message justification"
    bool_blocked = ""
    if blocked == "1":
        bool_blocked = "True"
    else:
        bool_blocked = "False"
    emailList = admin_email_list.split(', ') # change to NCILDlinkWebAdmin email or a list of emails later
    packet = MIMEMultipart()
    packet['Subject'] = "[Unblock Request] LDLink API Access User"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = ", ".join(emailList)
    message = "First name: " + str(firstname)
    message += "<br>Last name: " + str(lastname)
    message += "<br><br>Email: " + str(email)
    message += "<br><br>Token: " + str(token)
    message += "<br>Registered: " + str(registered)
    message += "<br>Blocked: " + str(bool_blocked)
    message += "<br><br>Justification: " + str(justification)
    message += '<br><br><u><a href="https://ldlink-dev.nci.nih.gov/LDlinkRestWeb/apiaccess/unblock_user?email=' + email + '&token=' + admin_token + '">Click here to unblock user.</a></u>'
    packet.attach(MIMEText(message, 'html'))
    smtp = smtplib.SMTP(email_account)
    smtp.sendmail("NCILDlinkWebAdmin@mail.nih.gov", emailList, packet.as_string())
    out_json = {
        "email": email,
        "justification": justification
    }
    return out_json

# creates table in database if database did not exist before
def createTables(api_access_dir):
    # create database
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `blocked` INTEGER);")
    cur.execute(
        "CREATE TABLE api_log (`token` TEXT, `module` TEXT, `accessed` DATETIME);")
    con.commit()
    con.close()

# check if user email record exists
def getEmailRecord(curr, email):
    temp = (email,)
    curr.execute("SELECT * FROM api_users WHERE email=?", temp)
    return curr.fetchone()

def insertRecord(firstname, lastname, email, institution, token, registered, blocked, api_access_dir):
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `blocked` INTEGER);")
    con.commit()
    temp = (firstname, lastname, email, institution, token, registered, blocked)
    cur.execute(
        "INSERT INTO api_users (first_name, last_name, email, institution, token, registered, blocked) VALUES (?,?,?,?,?,?,?)", temp)
    con.commit()
    con.close()

# log token's api call to api_log table
def logAccess(token, module):
    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_access_dir = config['api']['api_access_dir']
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS api_log (`token` TEXT, `module` TEXT, `accessed` DATETIME);")
    con.commit()
    access_date = getDatetime().strftime("%Y-%m-%d %H:%M:%S")
    temp = (token, module, access_date)
    cur.execute(
        "INSERT INTO api_log (token, module, accessed) VALUES (?,?,?)", temp)
    con.commit()
    con.close()

# sets blocked attribute of user to 1=true
def blockUser(email):
    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_access_dir = config['api']['api_access_dir']
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (email,)
    cur.execute(
        "UPDATE api_users SET blocked=1 WHERE email=?", temp)
    con.commit()
    con.close()
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been blocked."
    }
    return out_json

# sets blocked attribute of user to 0=false
def unblockUser(email):
    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_access_dir = config['api']['api_access_dir']
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (email,)
    cur.execute(
        "UPDATE api_users SET blocked=0 WHERE email=?", temp)
    con.commit()
    con.close()
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been unblocked."
    }
    return out_json

# update record only if email's token is expired and user re-registers
def updateRecord(firstname, lastname, email, institution, token, registered, blocked, api_access_dir):
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    temp = (firstname, lastname, institution, token, registered, blocked, email)
    cur.execute(
        "UPDATE api_users SET first_name=?, last_name=?, institution=?, token=?, registered=?, blocked=? WHERE email=?", temp)
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
def checkToken(token, api_access_dir, token_expiration, token_expiration_days):
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `blocked` INTEGER);")
    con.commit()
    temp = (token,)
    cur.execute("SELECT * FROM api_users WHERE token=?", temp)
    record = cur.fetchone()
    con.close()
    if record is None:
        return False
    else:
        # return True
        present = getDatetime()
        registered = datetime.datetime.strptime(record[5], "%Y-%m-%d %H:%M:%S")
        expiration = getExpiration(registered, token_expiration_days)
        if ((present < expiration) or not token_expiration):
            return True
        else:
            return False

# check if token is blocked (1=blocked, 0=not blocked). returns true if token is blocked
def checkBlocked(token, api_access_dir):
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `blocked` INTEGER);")
    con.commit()
    temp = (token,)
    cur.execute("SELECT * FROM api_users WHERE token=?", temp)
    record = cur.fetchone()
    con.close()
    if record is None:
        return False
    else:
        if int(record[6]) == 1:
            return True
        else:
            return False

# check if email is blocked (1=blocked, 0=not blocked). returns true if email is blocked
def checkBlockedEmail(email, api_access_dir):
    con = sqlite3.connect(api_access_dir + 'api_access.db')
    con.text_factory = str
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `blocked` INTEGER);")
    con.commit()
    temp = (email,)
    cur.execute("SELECT * FROM api_users WHERE email=?", temp)
    record = cur.fetchone()
    con.close()
    if record is None:
        return False
    else:
        if int(record[6]) == 1:
            return True
        else:
            return False

# generate unique access token for each user
def generateToken(curr):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    admin_token = bool(config['api']['admin_token'])
    token = binascii.b2a_hex(os.urandom(6))
    # if true, generate another token - make sure example token is not generated
    while(checkUniqueToken(curr, token) or token == "faketoken123" or token == admin_token):
        token = binascii.b2a_hex(os.urandom(6))
    return token

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# get current date and time
def getExpiration(registered, token_expiration_days):
    return registered + datetime.timedelta(days=token_expiration_days)

# registers new users and emails generated token for WEB
def register_user_web(firstname, lastname, email, institution, reference):
    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_access_dir = config['api']['api_access_dir']
    token_expiration = bool(config['api']['token_expiration'])
    token_expiration_days = config['api']['token_expiration_days']
    email_account = config['api']['email_account']

    out_json = {}

    # create database and table if it does not exist already
    if not os.path.exists(api_access_dir + 'api_access.db'):
        print "api_usrs.db created."
        createTables(api_access_dir)

    # by default, users are not blocked
    blocked = 0

    # Connect to snp database
    conn = sqlite3.connect(api_access_dir + 'api_access.db')
    conn.text_factory = str
    curr = conn.cursor()

    record = getEmailRecord(curr, email)
    print record
    # if email record exists, do not insert to db
    if record != None:
        if checkBlockedEmail(record[2], api_access_dir):
            out_json = {
                "message": "Your API token has been blocked.",
                "firstname": record[0],
                "lastname": record[1],
                "email": record[2],
                "institution": record[3],
                "token": record[4],
                "registered": record[5],
                "blocked": record[6]
            }
        else:
            present = getDatetime()
            registered = datetime.datetime.strptime(record[5], "%Y-%m-%d %H:%M:%S")
            expiration = getExpiration(registered, token_expiration_days)
            format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
            if ((present < expiration) or not token_expiration):
                out_json = {
                    "message": "Email already registered.",
                    "firstname": record[0],
                    "lastname": record[1],
                    "email": record[2],
                    "institution": record[3],
                    "token": record[4],
                    "registered": record[5],
                    "blocked": record[6]
                }
                emailUser(record[2], record[4], format_expiration, record[0], token_expiration, email_account)
            else:
                token = generateToken(curr)
                registered = getDatetime()
                expiration = getExpiration(registered, token_expiration_days)
                format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
                format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
                updateRecord(firstname, lastname, email, institution, token, format_registered, blocked, api_access_dir)
                out_json = {
                    "message": "Thank you for registering to use the LDlink API.",
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": email,
                    "institution": institution,
                    "token": token,
                    "registered": format_registered,
                    "blocked": blocked
                }
                emailUser(email, token, format_expiration, firstname, token_expiration, email_account)
    else:
        # if email record does not exists in db, add to table
        token = generateToken(curr)
        registered = getDatetime()
        expiration = getExpiration(registered, token_expiration_days)
        format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
        insertRecord(firstname, lastname, email, institution, token, format_registered, blocked, api_access_dir)
        out_json = {
            "message": "Thank you for registering to use the LDlink API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token,
            "registered": format_registered,
            "blocked": blocked
        }
        emailUser(email, token, format_expiration, firstname, token_expiration, email_account)

    conn.close()
    return out_json

# registers new users and emails generated token for API
def register_user_api(firstname, lastname, email, institution, token, registered, blocked):
    # Set data directories using config.yml
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_access_dir = config['api']['api_access_dir']

    out_json = {}

    # create database and table if it does not exist already
    if not os.path.exists(api_access_dir + 'api_access.db'):
        print "api_usrs.db created."
        createTables(api_access_dir)

    # by default, users are not blocked
    blocked = 0

    # Connect to snp database
    conn = sqlite3.connect(api_access_dir + 'api_access.db')
    conn.text_factory = str
    curr = conn.cursor()

    record = getEmailRecord(curr, email)

    # if email record exists, do not insert to db
    if record != None:
        # if email record in api database does not have new token, update it
        if (record[2] == email and record[4] != token):
            updateRecord(firstname, lastname, email, institution, token, registered, blocked, api_access_dir)
            out_json = {
                "message": "Thank you for registering to use the LDlink API.",
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "institution": institution,
                "token": token,
                "registered": registered,
                "blocked": blocked
            }
        else:
            out_json = {
                "message": "Email already registered.",
                "firstname": record[0],
                "lastname": record[1],
                "email": record[2],
                "institution": record[3],
                "token": record[4],
                "registered": record[5],
                "blocked": record[6]
            }
    else:
        # if email record does not exists in db, add to table
        insertRecord(firstname, lastname, email, institution, token, registered, blocked, api_access_dir)
        out_json = {
            "message": "Thank you for registering to use the LDlink API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token,
            "registered": registered,
            "blocked": blocked
        }

    conn.close()
    return out_json