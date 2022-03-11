#!/usr/bin/env python3
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
import UnlockStaleTokens
from LDcommon import connectMongoDBReadOnly,getEmail,connectMongoDBWrite

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
        print(smtp_debug)
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
    print("sending message registered")
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
    print("sending message blocked")
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
    print("sending message unblocked")
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
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    email_account = config['api']['email_account']
    api_superuser = config['api']['api_superuser']
    api_superuser_token = getToken(api_superuser)
    print("sending message justification")
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
def getEmailRecord(email, env, api_mongo_addr):
    db = connectMongoDBReadOnly()
    users = db.api_users
    emailRecord = users.find_one({"email": email})
    return emailRecord

def insertUser(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr):
    db = connectMongoDBWrite()
    user = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "institution": institution,
        "token": token,
        "registered": registered,
        "blocked": blocked,
        "locked": 0
    }
    users = db.api_users
    users.insert_one(user).inserted_id

# log token's api call to api_log table
def logAccess(token, module):
    db = connectMongoDBReadOnly()
    accessed = getDatetime()
    
    log = {
        "token": token,
        "module": module,
        "accessed": accessed
    }
    logs = db.api_log
    logs.insert_one(log).inserted_id

# sets blocked attribute of user to 1=true
def blockUser(email, url_root):
    email_account = getEmail()
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been blocked. An email has been sent to the user."
    }
    db = connectMongoDBWrite()
    users = db.api_users
    update_operation = users.find_one_and_update({"email": email}, { "$set": {"blocked": 1}})
    if update_operation is None:
        return None
    emailUserBlocked(email, email_account, url_root)
    return out_json

# sets blocked attribute of user to 0=false
def unblockUser(email):
    email_account = getEmail()
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been unblocked. An email has been sent to the user."
    }
    db = connectMongoDBWrite()
    users = db.api_users
    update_operation = users.find_one_and_update({"email": email}, { "$set": {"blocked": 0}})
    if update_operation is None:
        return None
    emailUserUnblocked(email, email_account)
    return out_json

# sets locked attribute of user to lockValue
def setUserLock(email, lockValue):
    out_json = {
        "message": "Email user (" + email + ")'s lock has been set to " + str(lockValue)
    }
    db = connectMongoDBWrite()
    users = db.api_users
    update_operation = users.find_one_and_update({"email": email}, { "$set": {"locked": int(lockValue)}})
    if update_operation is None:
        return None
    return out_json


# sets api2auth attribute of user to authValue
def setUserApi2Auth(email, authValue):
    out_json = {
        "message": "Email user (" + email + ")'s api2auth has been set to " + str(authValue)
    }
    db = connectMongoDBWrite()
    users = db.api_users
    update_operation = users.find_one_and_update({"email": email}, { "$set": {"api2auth": int(authValue)}})
    if update_operation is None:
        return None
    return out_json

# sets locked attribute of all users to 0=false
def unlockAllUsers():
    UnlockStaleTokens.main()
    
    out_json = {
        "message": "All tokens have been unlocked."
    }
    return out_json

# update record only if email's token is expired and user re-registers
def updateRecord(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr):
    db = connectMongoDBWrite()
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
    db = connectMongoDBReadOnly()
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

# check if token is authorized to access API server 2
def checkApiServer2Auth(token):
    db = connectMongoDBReadOnly()
    users = db.api_users
    record = users.find_one({"token": token})

    if record is None:
        return False
    else:
        if "api2auth" in record and record["api2auth"] == 1:
            return True
        else:
            return False

# given email, return token
def getToken(email):
    db = connectMongoDBReadOnly()
    users = db.api_users
    record = users.find_one({"email": email})
    if record is None:
        return None
    else:
        return record["token"]

# check if token is blocked (1=blocked, 0=not blocked). returns true if token is blocked
def checkBlocked(token):
    db = connectMongoDBReadOnly()
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        if int(record["blocked"]) == 1:
            return True
        else:
            return False

# check if token is locked (1=locked, 0=not locked, -1=never locked). returns true (1) if token is locked
def checkLocked(token):
    db = connectMongoDBReadOnly()
    users = db.api_users
    record = users.find_one({"token": token})

    if record is None:
        return False
    else:
        if "locked" in record:
            if record["locked"] == 0 or record["locked"] == -1:
                return False
            else:
                return True
        else:
            return False

def toggleLocked(token, lock):
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
       
    if "restrict_concurrency" in config['api']:
        restrict_concurrency = config['api']['restrict_concurrency']
    else: 
        restrict_concurrency = True
    if restrict_concurrency:
        db = connectMongoDBWrite()
        users = db.api_users
        record = users.find_one({"token": token})

        # bypass lock toggle if user has -1 locked flag set (unlimited api calls)
        if record["locked"] != -1:
            if lock == 1:
                calcStartTime = getDatetime()
                users.find_one_and_update({"token": token}, { "$set": {"locked": calcStartTime}})
            else: 
                users.find_one_and_update({"token": token}, { "$set": {"locked": lock}})

# check if email is blocked (1=blocked, 0=not blocked). returns true if email is blocked
def checkBlockedEmail(email, env, api_mongo_addr):
    db = connectMongoDBReadOnly()
    users = db.api_users
    record = users.find_one({"email": email})
    print(record)
    if record is None:
        return False
    else:
        if int(record["blocked"]) == 1:
            return True
        else:
            return False

# check if token is already in db
def checkUniqueToken(token):
    db = connectMongoDBReadOnly()
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        return True

# generate unique access token for each user
def generateToken():
    token = binascii.b2a_hex(os.urandom(6)).decode('utf-8')
    # if true, generate another token - make sure example token is not generated
    while(checkUniqueToken(token) or token == "faketoken123"):
        token = binascii.b2a_hex(os.urandom(6)).decode('utf-8')
    return token

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# get current date and time
def getExpiration(registered, token_expiration_days):
    return registered + datetime.timedelta(days=token_expiration_days)

# registers new users and emails generated token for WEB
def register_user(firstname, lastname, email, institution, reference, url_root):
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    env = config['env']
    api_mongo_addr = config['database']['api_mongo_addr']
    token_expiration = bool(config['api']['token_expiration'])
    token_expiration_days = config['api']['token_expiration_days']
    email_account = config['api']['email_account']
    out_json = {}
    # by default, users are not blocked
    blocked = 0
    record = getEmailRecord(email, env, api_mongo_addr)
    # print record
    # if email record exists, do not insert to db
    if record != None:
        if checkBlockedEmail(record["email"], env, api_mongo_addr):
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
                updateRecord(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr)
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
        insertUser(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr)
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
    db = connectMongoDBWrite()
    users = db.api_users
    log = db.api_log
    # get number of registered users in total
    numUsers = users.count_documents({})
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
                "#_api_calls": { 
                    "$sum": 1 
                } 
            } 
        }, 
        { 
            "$sort": { 
                "#_api_calls": -1 
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
    numCalls = 0
    for user in users_json_sanitized:
        numCalls += int(user['#_api_calls'])
    out_json = {
        "#_total_registered_users": numUsers,
        "#_total_api_calls": numCalls,
        "users": users_json_sanitized
    }
    return out_json

# returns stats of api users with locked tokens
def getLockedUsers():
    db = connectMongoDBReadOnly()
    users = db.api_users
    locked_users_json = users.find({"locked": {"$exists": True, "$ne": 0}},  { "firstname": 1, "lastname": 1, "email": 1, "locked": 1,  "_id": 0 })
    locked_users_json_sanitized = json.loads(json_util.dumps(locked_users_json))
    numLockedUsers = len(locked_users_json_sanitized)
    out_json = {
        "#_locked_users": numLockedUsers,
        "locked_users": locked_users_json_sanitized
    }
    return out_json

# returns stats of api users with blocked tokens
def getBlockedUsers():
    db = connectMongoDBReadOnly()
    users = db.api_users
    blocked_users_json = users.find({"blocked": {"$exists": True, "$ne": 0}},  { "firstname": 1, "lastname": 1, "email": 1, "blocked": 1,  "_id": 0 })
    blocked_users_json_sanitized = json.loads(json_util.dumps(blocked_users_json))
    numBlockedUsers = len(blocked_users_json_sanitized)
    out_json = {
        "#_blocked_users": numBlockedUsers,
        "blocked_users": blocked_users_json_sanitized
    }
    return out_json

def lookupUser(email):
    with open('config.yml', 'r') as yml_file:
        config = yaml.load(yml_file)
    env = config['env']
    api_mongo_addr = config['database']['api_mongo_addr']

    user_record = getEmailRecord(email, env, api_mongo_addr)

    if user_record != None:
        registered = user_record["registered"]
        format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        locked = user_record["locked"]

        try:
            format_locked = locked.strftime("%Y-%m-%d %H:%M:%S")
        except:
            format_locked = locked
            
        out_json = {
            "email": user_record["email"],
            "firstname": user_record["firstname"],
            "lastname": user_record["lastname"],
            "institution": user_record["institution"],
            "token": user_record["token"],
            "registered": format_registered,
            "blocked": user_record["blocked"],
            "locked": format_locked
        }
    else:
        out_json = "No record found"
    return out_json

