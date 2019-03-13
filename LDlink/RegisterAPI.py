#!/usr/bin/env python
import json
import os.path
import binascii
import yaml
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import json_util, ObjectId
contents = open("SNP_Query_loginInfo.ini").read().split('\n')
# username = contents[0].split('=')[1]
username = 'ncianalysis_api'
password = contents[1].split('=')[1]
port = int(contents[2].split('=')[1])

# blocked users attribute: 0=false, 1=true

# connect to email account
def smtp_connect(email_account):
    smtp = smtplib.SMTP(email_account)
    smtp.set_debuglevel(1)
    return smtp

# send email
def smtp_send(smtp, email_account, email, packet):
    # retries twice upon failure (often connection timeout)
    try:
        smtp_debug = smtp.sendmail("NCILDlinkWebAdmin@mail.nih.gov", email, packet.as_string())
        print smtp_debug
        smtp.quit()
    except Exception:
        smtp.quit()
        smtp = smtp_connect(email_account)
        try:
            smtp_send(smtp, email_account, email, packet)
        except Exception:
            smtp.quit()
            smtp = smtp_connect(email_account)
            smtp_send(smtp, email_account, email, packet)

# email user token
def emailUser(email, token, expiration, firstname, token_expiration, email_account, url_root):
    print "sending message registered"
    new_url_root = url_root.replace('http://', 'https://')
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    message = ''
    if token_expiration:
        message = 'Dear ' + firstname + ', ' + '<br><br>' + 'Thank you for registering to use the LDlink API! <br><br>' + 'Your token is: ' + token + '<br>' + 'Your token expires on: ' + expiration + '<br><br>' + 'Please include this token as part of the submitted argument in your LDlink API requests. Examples of how to use a LDlink token are described in the <a href="'+ new_url_root + '?tab=apiaccess"><u>API Access</u></a> tab. Please do not share this token with other users as misuse of this token will result in potential blocking or termination of API use. <br><br>Thanks again for your interest in LDlink,<br><br>' + 'LDlink Web Admin'
    else:
        message = 'Dear ' + firstname + ', ' + '<br><br>' + 'Thank you for registering to use the LDlink API! <br><br>' + 'Your token is: ' + token + '<br><br>' + 'Please include this token as part of the submitted argument in your LDlink API requests. Examples of how to use a LDlink token are described in the <a href="' + new_url_root + '?tab=apiaccess"><u>API Access</u></a> tab. Please do not share this token with other users as misuse of this token will result in potential blocking or termination of API use. <br><br>Thanks again for your interest in LDlink,<br><br>' + 'LDlink Web Admin'
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, email, packet)

# email user when their token is blocked
def emailUserBlocked(email, email_account, url_root):
    print "sending message blocked"
    new_url_root = url_root.replace('http://', 'https://')
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token Blocked"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    message = "Dear " + str(email) + ", " + "<br><br>"
    message += "Your LDlink API access token has been blocked.<br><br>"
    message += "To unblock, resubmit a request in LDlink's <a href=\"" + new_url_root + "?tab=apiaccess\"><u>API Access</u></a> tab with the same email address.<br><br>"
    message += "Please contact the LDlink Web Admin (NCILDlinkWebAdmin@mail.nih.gov) for any questions or concerns.<br><br>"
    message += "LDlink Web Admin"
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, email, packet)

# email user when their token is unblocked
def emailUserUnblocked(email, email_account):
    print "sending message unblocked"
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token Unblocked"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    
    message = "Dear " + str(email) + ", " + "<br><br>"
    message += "Your LDlink API access token has been unblocked.<br><br>"
    message += "Please contact the LDlink Web Admin (NCILDlinkWebAdmin@mail.nih.gov) for any questions or concerns.<br><br>"
    message += "LDlink Web Admin"
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, email, packet)

# email unblock request to list of web admins
def emailJustification(firstname, lastname, email, institution, registered, blocked, justification, url_root):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    email_account = config['api']['email_account']
    api_superuser = config['api']['api_superuser']
    api_superuser_token = getToken(api_superuser)
    print "sending message justification"
    new_url_root = url_root.replace('http://', 'https://')
    bool_blocked = ""
    if blocked == "1":
        bool_blocked = "True"
    else:
        bool_blocked = "False"
    # emailList = approval_email_list.split(', ') # change to NCILDlinkWebAdmin email or a list of emails later
    packet = MIMEMultipart()
    packet['Subject'] = "[Unblock Request] LDLink API Access User"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    # packet['To'] = ", ".join(emailList)
    packet['To'] = api_superuser
    message = "The following user has submitted an unblock request:"
    message += "<br><br>First name: " + str(firstname)
    message += "<br>Last name: " + str(lastname)
    message += "<br>Email: " + str(email)
    message += "<br>Registered: " + str(registered)
    message += "<br>Blocked: " + str(bool_blocked)
    message += "<br><br>Justification: " + str(justification)
    message += "<br><br>Please review user details and justification. To unblock the user, click the link below."
    message += '<br><br><u><a href="' + new_url_root + 'LDlinkRestWeb/apiaccess/unblock_user?email=' + email + '&token=' + api_superuser_token + '">Click here to unblock user.</a></u>'
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, api_superuser, packet)
    out_json = {
        "email": email,
        "justification": justification
    }
    return out_json

# check if user email record exists
def getEmailRecord(email):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    emailRecord = users.find_one({"email": email})
    return emailRecord

def insertUser(firstname, lastname, email, institution, token, registered, blocked):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    user = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "institution": institution,
        "token": token,
        "registered": registered,
        "blocked": blocked
    }
    users = db.api_users
    users.insert_one(user).inserted_id

# log token's api call to api_log table
def logAccess(token, module):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    api_mongo_addr = config['api']['api_mongo_addr']
    accessed = getDatetime()
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    log = {
        "token": token,
        "module": module,
        "accessed": accessed
    }
    logs = db.api_log
    logs.insert_one(log).inserted_id

# sets blocked attribute of user to 1=true
def blockUser(email, url_root):
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    email_account = config['api']['email_account']
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been blocked. An email has been sent to the user."
    }
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    users.find_one_and_update({"email": email}, { "$set": {"blocked": 1}})
    emailUserBlocked(email, email_account, url_root)
    return out_json

# sets blocked attribute of user to 0=false
def unblockUser(email):
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    email_account = config['api']['email_account']
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been unblocked. An email has been sent to the user."
    }
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    users.find_one_and_update({"email": email}, { "$set": {"blocked": 0}})
    emailUserUnblocked(email, email_account)
    return out_json

# update record only if email's token is expired and user re-registers
def updateRecord(firstname, lastname, email, institution, token, registered, blocked):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    user = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "institution": institution,
        "token": token,
        "registered": registered,
        "blocked": blocked
    }
    users = db.api_users
    users.find_one_and_update({"email": email}, { "$set": user})

# check if token is valid when hitting API route and not expired
def checkToken(token, token_expiration, token_expiration_days):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    api_mongo_addr = config['api']['api_mongo_addr']
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        # return True
        present = getDatetime()
        # registered = datetime.datetime.strptime(record["registered"], "%Y-%m-%d %H:%M:%S")
        registered = record["registered"]
        expiration = getExpiration(registered, token_expiration_days)
        if ((present < expiration) or not token_expiration):
            return True
        else:
            return False

# given email, return token
def getToken(email):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    record = users.find_one({"email": email})
    if record is None:
        return None
    else:
        return record["token"]

# check if token is blocked (1=blocked, 0=not blocked). returns true if token is blocked
def checkBlocked(token):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    api_mongo_addr = config['api']['api_mongo_addr']
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        if int(record["blocked"]) == 1:
            return True
        else:
            return False

# check if token is locked (1=locked, 0=not locked). returns true (1) if token is locked
def checkLocked(token):
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    api_mongo_addr = config['api']['api_mongo_addr']
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        if "locked" in record:
            if int(record["locked"]) == 1:
                return True
            else:
                return False
        else:
            return False
    # db.api_users.update({token: "f655a4bf0a71"}, {$set:{locked: 1}})

def toggleLocked(token, lock):
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    api_mongo_addr = config['api']['api_mongo_addr']
    client = MongoClient('mongodb://'+username+':'+password+'@'+api_mongo_addr+'/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    users.find_one_and_update({"token": token}, { "$set": {"locked": lock}})

# check if email is blocked (1=blocked, 0=not blocked). returns true if email is blocked
def checkBlockedEmail(email):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    record = users.find_one({"email": email})
    if record is None:
        return False
    else:
        if int(record["blocked"]) == 1:
            return True
        else:
            return False

# check if token is already in db
def checkUniqueToken(token):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        return True

# generate unique access token for each user
def generateToken():
    token = binascii.b2a_hex(os.urandom(6))
    # if true, generate another token - make sure example token is not generated
    while(checkUniqueToken(token) or token == "faketoken123"):
        token = binascii.b2a_hex(os.urandom(6))
    return token

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# get current date and time
def getExpiration(registered, token_expiration_days):
    return registered + datetime.timedelta(days=token_expiration_days)

# registers new users and emails generated token for WEB
def register_user(firstname, lastname, email, institution, reference, url_root):
    with open('config.yml', 'r') as f:
        config = yaml.load(f)
    token_expiration = bool(config['api']['token_expiration'])
    token_expiration_days = config['api']['token_expiration_days']
    email_account = config['api']['email_account']
    out_json = {}
    # by default, users are not blocked
    blocked = 0
    record = getEmailRecord(email)
    # print record
    # if email record exists, do not insert to db
    if record != None:
        if checkBlockedEmail(record["email"]):
            registered = record["registered"]
            format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
            out_json = {
                "message": "Your email is associated with a blocked API token.",
                "firstname": record["firstname"],
                "lastname": record["lastname"],
                "email": record["email"],
                "institution": record["institution"],
                "token": record["token"],
                "registered": format_registered,
                "blocked": record["blocked"]
            }
        else:
            present = getDatetime()
            # registered = datetime.datetime.strptime(record["registered"], "%Y-%m-%d %H:%M:%S")
            registered = record["registered"]
            expiration = getExpiration(registered, token_expiration_days)
            format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
            format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
            if ((present < expiration) or not token_expiration):
                out_json = {
                    "message": "Email already registered.",
                    "firstname": record["firstname"],
                    "lastname": record["lastname"],
                    "email": record["email"],
                    "institution": record["institution"],
                    "token": record["token"],
                    "registered": format_registered,
                    "blocked": record["blocked"]
                }
                emailUser(record["email"], record["token"], format_expiration, record["firstname"], token_expiration, email_account, url_root)
            else:
                token = generateToken()
                registered = getDatetime()
                expiration = getExpiration(registered, token_expiration_days)
                format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
                format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
                updateRecord(firstname, lastname, email, institution, token, registered, blocked)
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
                emailUser(email, token, format_expiration, firstname, token_expiration, email_account, url_root)
    else:
        # if email record does not exists in db, add to table
        token = generateToken()
        registered = getDatetime()
        expiration = getExpiration(registered, token_expiration_days)
        format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
        insertUser(firstname, lastname, email, institution, token, registered, blocked)
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
        emailUser(email, token, format_expiration, firstname, token_expiration, email_account, url_root)
    return out_json

# returns stats of total number of calls per registered api users with optional arguments
# optional arguments: startdatetime of api calls, enddatetime of api calls, top # users with most calls
def getStats(startdatetime, enddatetime, top):
    client = MongoClient('mongodb://'+username+':'+password+'@localhost/LDLink', port)
    db = client["LDLink"]
    users = db.api_users
    log = db.api_log
    # get number of registered users in total
    numUsers = users.count()
    # join api_log and api_users by foreign key to retrieve user info per api_log record
    pipeline = [
        { 
            "$lookup" : { 
                "from" : "api_users", 
                "localField" : "token", 
                "foreignField" : "token", 
                "as" : "user_info" 
            } 
        }, 
        {   
            '$unwind' : "$user_info" 
        },
        {   
            "$project" : {
                "accessed" : 1,
                "module" : 1,
                "userinfo" : {
                    "email" : "$user_info.email",
                    "firstname" : "$user_info.firstname",
                    "lastname" : "$user_info.lastname"
                }
            } 
        },
        { 
            "$group": { 
                "_id": "$userinfo", 
                "#_total_api_calls": { 
                    "$sum": 1 
                } 
            } 
        }, 
        { 
            "$sort": { 
                "#_total_api_calls": -1 
            } 
        }
    ]
    # handle if top parameter is indicated or not
    if top is not False:
        pipeline.append({ "$limit": int(top) })
    # handle startdatetime and enddatetime parameters
    if ((startdatetime is not False) or (enddatetime is not False)):
        rangeQuery = {}
        if ((startdatetime is not False) and (enddatetime is False)):
            fromdatetime = startdatetime.split("-")
            if (len(fromdatetime) == 6): 
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), int(fromdatetime[5]), 0)
            elif (len(fromdatetime) == 3):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), 0, 0, 0, 0)
            elif (len(fromdatetime) == 5):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), 0, 0)
            else:
                return { "message": "Invalid input parameters."}
            rangeQuery = { "$match": { "accessed": { "$gte": from_datetime } } }
        if ((enddatetime is not False) and (startdatetime is False)):
            todatetime = enddatetime.split("-")
            if (len(fromdatetime) == 6): 
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), int(todatetime[5]), 0)
            elif (len(fromdatetime) == 3):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), 23, 59, 59, 0)
            elif (len(fromdatetime) == 5):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), 59, 0)
            else:
                return { "message": "Invalid input parameters."}
            rangeQuery = { "$match": { "accessed": { "$lt": to_datetime } } }
        if ((startdatetime is not False) and (enddatetime is not False)):
            fromdatetime = startdatetime.split("-")
            if (len(fromdatetime) == 6): 
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), int(fromdatetime[5]), 0)
            elif (len(fromdatetime) == 3):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), 0, 0, 0, 0)
            elif (len(fromdatetime) == 5):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), 0, 0)
            else:
                return { "message": "Invalid input parameters."}
            todatetime = enddatetime.split("-")
            if (len(todatetime) == 6): 
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), int(todatetime[5]), 0)
            elif (len(todatetime) == 3):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), 23, 59, 59, 0)
            elif (len(todatetime) == 5):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), 59, 0)
            else:
                return { "message": "Invalid input parameters."}
            rangeQuery = { "$match": { "accessed": { "$gte": from_datetime, "$lt": to_datetime } } }
        pipeline.insert(3, rangeQuery)
    users_json = log.aggregate(pipeline)
    # santize string to be returned as proper json
    users_json_sanitized = json.loads(json_util.dumps(users_json))
    out_json = {
        "#_registered_users": numUsers,
        "users": users_json_sanitized
    }
    return out_json