#!flask/bin/python3
import os
import traceback
import collections
import argparse
import json
import time
import random
from threading import Thread
from pathlib import Path
from functools import wraps
from socket import gethostname
from flask import Flask, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from LDpair import calculate_pair
from LDpop import calculate_pop
from LDproxy import calculate_proxy
from LDtrait import calculate_trait, get_ldtrait_timestamp
from LDexpress import calculate_express, get_ldexpress_tissues
from LDmatrix import calculate_matrix
from LDhap import calculate_hap
from LDassoc import calculate_assoc
from LDutilites import get_config, unlock_stale_tokens
from LDcommon import genome_build_vars,connectMongoDBReadOnly
from SNPclip import calculate_clip
from SNPchip import calculate_chip, get_platform_request
from ApiAccess import register_user, checkToken, checkApiServer2Auth, checkBlocked, checkLocked, toggleLocked, logAccess, emailJustification, blockUser, unblockUser, getStats, setUserLock, setUserApi2Auth, unlockAllUsers, getLockedUsers, getBlockedUsers, lookupUser

# retrieve config
param_list = get_config()
# Ensure tmp directory exists
tmp_dir = param_list['tmp_dir']
log_level = param_list['log_level']

Path(tmp_dir).mkdir(parents=True, exist_ok=True) 

### Initialize Flask App ###

is_main = __name__ == '__main__'
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024
app.config['UPLOAD_DIR'] = os.path.join(os.getcwd(), 'tmp')
app.debug = False
app.logger.setLevel(log_level)

# Flask Limiter initialization
# def get_token():
#     return request.args.get('token')
# # limit requests with token on API calls only
# limiter = Limiter(
#     app,
#     key_func=get_token
# )
# limiter = Limiter(
#     app,
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"]
# )
# Example Flask Limiter decorator: @limiter.limit("1 per second")

### Helper functions ###

# Return error (and traceback if specified) from calculations
def sendTraceback(error, showTraceback=False):
    custom = {}
    if (error is None or len(error) == 0):
        custom["error"] = "Internal server error. Please contact LDlink admin."
    else:
        custom["error"] = error
    if showTraceback:
        traceback.print_exc()
        custom["traceback"] = traceback.format_exc()
    out_json = json.dumps(custom, sort_keys=False, indent=2)
    app.logger.info('Generated error message ' + json.dumps(custom, indent=4, sort_keys=True))
    return current_app.response_class(out_json, mimetype='application/json')

# Return JSON output from calculations
def sendJSON(inputString):
    out_json = json.dumps(inputString, sort_keys=False)
    return current_app.response_class(out_json, mimetype='application/json')

# Read headers from uploaded data files for LDassoc
def read_csv_headers(example_filepath):
    final_headers = []
    with open(example_filepath) as fp:
        headers = fp.readline().strip().split()
    for heads in headers:
        if len(heads) > 0:
            final_headers.append(heads)
    return final_headers

### API Tokenization ###

# Get module name from request path for API logs collection in MongoDB 
def getModule(fullPath):
    if "ldexpress" in fullPath:
        return "LDexpress"
    elif "ldhap" in fullPath:
        return "LDhap"
    elif "ldmatrix" in fullPath:
        return "LDmatrix"
    elif "ldpair" in fullPath:
        return "LDpair"
    elif "ldpop" in fullPath:
        return "LDpop"
    elif "ldproxy" in fullPath:
        return "LDproxy"
    elif "ldtrait" in fullPath:
        return "LDtrait"
    elif "snpchip" in fullPath:
        return "SNPchip"
    elif "snpclip" in fullPath:
        return "SNPclip"
    else:
        return "NA"

# Flask decorator
# Requires API route to include valid token in argument or will throw error
def requires_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Set data directories using config.yml
        url_root = param_list['base_url']
        require_token = bool(param_list['require_token'])
        token_expiration = bool(param_list['token_expiration'])
        token_expiration_days = param_list['token_expiration_days']
        if ("LDlinkRestWeb" not in request.full_path):
            # Web server access does not require token
            if require_token:
                # Check if token argument is missing in api call
                if 'token' not in request.args:
                    return sendTraceback('API token missing. Please register using the API Access tab: ' + url_root + '?tab=apiaccess')
                token = request.args['token']
                # Check if token is valid
                if checkToken(token, token_expiration, token_expiration_days) is False or token is None:
                    return sendTraceback('Invalid or expired API token. Please register using the API Access tab: ' + url_root + '?tab=apiaccess')
                # Check if token is blocked
                if checkBlocked(token):
                    return sendTraceback("Your API token has been blocked. Please contact system administrator: NCILDlinkWebAdmin@mail.nih.gov")
                # Check if token is locked (exclude check on api server 2)
                if ("LDlinkRest" in request.full_path):
                    if checkLocked(token):
                        return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
                # Check if token has been authorized to access api server 2
                #if ("LDlinkRest2" in request.full_path):
                #    if not checkApiServer2Auth(token):
                #        return sendTraceback("Your token is not authorized to access this API endpoint. Please contact system administrator: NCILDlinkWebAdmin@mail.nih.gov")
                module = getModule(request.full_path)
                logAccess(token, module)
                return f(*args, **kwargs)
            token = "NA"
            module = getModule(request.full_path)
            logAccess(token, module)
            return f(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

# Flask decorator
# Requires API route to include valid token in argument or will throw error
def requires_admin_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #create connection to database, retrieve api_users to find the user with token
        #then check if this user has admin value as 1, if it is admin, then grand acess, if not refuse
        db = connectMongoDBReadOnly(False,True)

        users = db.api_users
           
        if 'token' not in request.args:
            return sendTraceback('Admin API token missing.')
        token = request.args['token']
        # Check if token is valid and based on the token to find the user, then check if the user is admin or not, 
        record = users.find_one({"token": token})
        
        if record is None:
            return sendTraceback('Invalid admin token.')
        else:
            try:
                admin = record["admin"]
                if admin == 0:
                    return sendTraceback('Not a valid admin user.')
                elif admin == 1:
                    return f(*args, **kwargs)
                else:
                    return sendTraceback('Not a valid admin user.')
            except KeyError:
                return sendTraceback('Invalid admin token.')
    return decorated_function

# Web route to send API token unblock request from front-end
@app.route('/LDlinkRestWeb/apiaccess/apiblocked_web', methods=['GET'])
def apiblocked_web():
    start_time = time.time()
    firstname = request.args.get('firstname', False)
    lastname = request.args.get('lastname', False)
    email = request.args.get('email', False)
    institution = request.args.get('institution', False)
    registered = request.args.get('registered', False)
    blocked = request.args.get('blocked', False)
    justification = request.args.get('justification', False) 
    app.logger.debug('apiblocked_web params ' + json.dumps({
        'firstname': firstname,
        'lastname': lastname,
        'email': email,
        'institution': institution,
        'registered': registered,
        'blocked': blocked,
        'justification': justification
    }, indent=4, sort_keys=True))
    url_path = request.headers.get('X-Forwarded-Host')
    if url_path== None:
        url_path= request.url_root
    try:
        out_json = emailJustification(firstname, lastname, email, institution, registered, blocked, justification, url_path)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed unblocked API user justification submission (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to register user's email for API token
@app.route('/LDlinkRestWeb/apiaccess/register_web', methods=['GET'])
def register_web():
    start_time = time.time()
    firstname = request.args.get('firstname', False)
    lastname = request.args.get('lastname', False)
    email = request.args.get('email', False)
    institution = request.args.get('institution', False)
    reference = request.args.get('reference', False)
    url_path = request.headers.get('Referer')
    if url_path == None:
        url_path == request.url_root

    #print(request.headers)
    #will return http://nciws-d971-c.nci.nih.gov:8090/
    #print(request.url_root) 
    app.logger.debug('register_web params ' + json.dumps({
        'firstname': firstname,
        'lastname': lastname,
        'email': email,
        'institution': institution,
        'reference': reference,
        'URL_root':url_path
    }, indent=4, sort_keys=True))
    try:
        out_json = register_user(firstname, lastname, email, institution, reference, url_path)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    out_json2 = {
        "message": out_json["message"],
        "email": out_json["email"],
        "firstname": out_json["firstname"],
        "lastname": out_json["lastname"],
        "registered": out_json["registered"],
        "blocked": out_json["blocked"],
        "institution": out_json["institution"]
    }
    end_time = time.time()
    app.logger.info("Executed register API user (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json2)

# Web route to block user's API token
@app.route('/LDlinkRestWeb/apiaccess/block_user', methods=['GET'])
@requires_admin_token
def block_user():
    start_time = time.time()
    email = request.args.get('email', False)
    app.logger.debug('block_user params ' + json.dumps({
        'email': email
    }, indent=4, sort_keys=True))
    url_path = request.headers.get('X-Forwarded-Host')
    if url_path== None:
        url_path= request.url_root
    try:
        out_json = blockUser(email, url_path)
        if out_json is None:
            out_json =  {
                "message": "User email not found: " + str(email)
            }  
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed block API user (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to unblock user's API token
@app.route('/LDlinkRestWeb/apiaccess/unblock_user', methods=['GET'])
@requires_admin_token
def unblock_user():
    start_time = time.time()
    email = request.args.get('email', False)
    app.logger.debug('unblock_user params ' + json.dumps({
        'email': email
    }, indent=4, sort_keys=True))
    try:
        out_json = unblockUser(email)
        if out_json is None:
            out_json =  {
                "message": "User email not found: " + str(email)
            }  
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed unblock API user (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to set user's lock status
@app.route('/LDlinkRestWeb/apiaccess/set_user_lock', methods=['GET'])
@requires_admin_token
def set_user_lock():
    start_time = time.time()
    email = request.args.get('email', "Missing Argument")

    try:
        lockValue = int(request.args.get('locked', "Missing Argument"))
        app.logger.debug('set_user_lock params ' + json.dumps({
            'email': email,
            'lockValue': lockValue
        }, indent=4, sort_keys=True))
        if lockValue == -1 or lockValue == 0:
            try:
                out_json = setUserLock(email, lockValue)
                if out_json is None:
                    out_json =  {
                        "message": "User email not found: " + str(email)
                    }   
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
        else:
            out_json =  {
                "message": "Invalid lock value: " + str(lockValue)
            }
    except:
        out_json =  {
            "message": "Invalid lock value"
        }
    end_time = time.time()
    app.logger.info("Executed set API user lock status (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to grant/revoke user's API server 2 access
@app.route('/LDlinkRestWeb/apiaccess/set_user_api2auth', methods=['GET'])
@requires_admin_token
def set_user_api2auth():
    start_time = time.time()
    email = request.args.get('email', "Missing Argument")

    try:
        authValue = int(request.args.get('authValue', "Missing Argument"))
        app.logger.debug('set_user_api2auth params ' + json.dumps({
            'email': email,
            'authValue': authValue
        }, indent=4, sort_keys=True))
        if authValue == 0 or authValue == 1:
            try:
                out_json = setUserApi2Auth(email, authValue)
                if out_json is None:
                    out_json =  {
                        "message": "User email not found: " + str(email)
                    }   
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
        else:
            out_json =  {
                "message": "Invalid auth value: " + str(authValue)
            }
    except:
        out_json =  {
            "message": "Invalid auth value"
        }
    end_time = time.time()
    app.logger.info("Executed set API user's api server 2 access status (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to unlock all users API tokens
@app.route('/LDlinkRestWeb/apiaccess/unlock_all_users', methods=['GET'])
@requires_admin_token
def unlock_all_users():
    start_time = time.time()
    try:
        out_json = unlockAllUsers()
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed unlock all API users (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to retrieve user record 
@app.route('/LDlinkRestWeb/apiaccess/lookup_user', methods=['GET'])
@requires_admin_token
def lookup_user():
    start_time = time.time()
    email = request.args.get('email', False)
    app.logger.debug('lookup_user params ' + json.dumps({
        'email': email
    }, indent=4, sort_keys=True))
    try:
        out_json = lookupUser(email)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieving API user record (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to retrieve API log stats
@app.route('/LDlinkRestWeb/apiaccess/stats', methods=['GET'])
@requires_admin_token
def api_stats():
    start_time = time.time()
    startdatetime = request.args.get('startdatetime', False)
    enddatetime = request.args.get('enddatetime', False)
    top = request.args.get('top', False)
    app.logger.debug('api_stats params ' + json.dumps({
        'startdatetime': startdatetime,
        'enddatetime': enddatetime,
        'top': top
    }, indent=4, sort_keys=True))
    try:
        out_json = getStats(startdatetime, enddatetime, top)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieve API stats (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to retrieve all locked API users
@app.route('/LDlinkRestWeb/apiaccess/locked_users', methods=['GET'])
@requires_admin_token
def api_locked_users():
    start_time = time.time()
    try:
        out_json = getLockedUsers()
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieving locked API users stats (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web route to retrieve all blocked API users
@app.route('/LDlinkRestWeb/apiaccess/blocked_users', methods=['GET'])
@requires_admin_token
def api_blocked_users():
    start_time = time.time()
    try:
        out_json = getBlockedUsers()
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieving blocked API users stats (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

### LDLink Helper Routes ###

# Copy output files from tools' tmp directory to apache tmp directory
@app.route('/')
def root():
    return app.send_static_file('index.html')
    # with open('config.yml', 'r') as yml_file:
    #     config = yaml.load(yml_file)
    # env = config['env']
    # connect_external = config['database']['connect_external']
    # if env == "local":
        # return app.send_static_file('index.html')
    # else:
    #     # def copy_output_files(reference):
    #     # copy_output_files
    #     apache_root = "/analysistools/"
    #     # check if URL contains the keyword sandbox
    #     if 'sandbox' in request.url_root:
    #         apache_root = "/analysistools-sandbox/"
    #     apache_tmp_dir = apache_root + "public_html/apps/LDlink/tmp/"
    #     # Ensure apache tmp directory exists
    #     if not os.path.exists(apache_tmp_dir):
    #         os.makedirs(apache_tmp_dir)
    #     # copy *<reference_no>.* to htodocs
    #     os.system("cp " + tmp_dir + "*" + reference + ".* " + apache_tmp_dir)

# Ping route for API and Web instances
@app.route('/LDlinkRest/ping/', strict_slashes=False)
#@app.route('/LDlinkRest2/ping/', strict_slashes=False)
@app.route('/ping/', strict_slashes=False)
def ping():
    print("pong")
    try:
        return "true"
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))

# Route to check file exist status 
@app.route('/LDlinkRestWeb/status/<filename>', strict_slashes=False)
@app.route('/status/<filename>', strict_slashes=False)
def status(filename):
    filepath = safe_join(tmp_dir, filename)
    return jsonify(os.path.isfile(filepath))


# Route to serve temporary files
@app.route('/LDlinkRestWeb/tmp/<filename>', strict_slashes=False)
@app.route('/tmp/<filename>', strict_slashes=False)
def send_temp_file(filename):
    return send_from_directory(tmp_dir, filename)

# File upload route
@app.route('/LDlinkRest/upload', methods=['POST'])
#@app.route('/LDlinkRest2/upload', methods=['POST'])
@app.route('/LDlinkRestWeb/upload', methods=['POST'])
def upload():
    print("Processing upload")
    print("****** Stage 1: UPLOAD BUTTON ***** ")
    print("UPLOAD_DIR = %s" % (app.config['UPLOAD_DIR']))
    for arg in request.args:
        print(arg)
    print("request.method = %s" % (request.method))
    if request.method == 'POST':
        # check if the post request has the file part
        print(" We got a POST")
        # print dir(request.files)
        if 'ldassocFile' not in request.files:
            print('No file part')
            return 'No file part...'
        file = request.files['ldassocFile']
        # if user does not select file, browser also
        # submit a empty part without filename
        print(type(file))
        if file.filename == '':
            print('No selected file')
            return 'No selected file'
        if file:
            print('file.filename ' + file.filename)
            print('file and allowed_file')
            filename = secure_filename(file.filename)
            print("About to SAVE file")
            print("filename = " + filename)
            file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
            return 'File was saved'

# Route for LDassoc example GWAS data
@app.route('/LDlinkRest/ldassoc_example', methods=['GET'])
#@app.route('/LDlinkRest2/ldassoc_example', methods=['GET'])
@app.route('/LDlinkRestWeb/ldassoc_example', methods=['GET'])
def ldassoc_example():
    genome_build = request.args.get('genome_build', 'grch37')
    ldassoc_example_dir = param_list['ldassoc_example_dir']
    data_dir = param_list['data_dir']
    example_filepath = data_dir + ldassoc_example_dir + genome_build_vars[genome_build]['ldassoc_example_file']
    example = {
        'filename': os.path.basename(example_filepath),
        'headers': read_csv_headers(example_filepath)
    }
    return json.dumps(example)

# Route to retrieve LDexpress tissue info
@app.route('/LDlinkRest/ldexpress_tissues', methods=['GET'])
#@app.route('/LDlinkRest2/ldexpress_tissues', methods=['GET'])
@app.route('/LDlinkRestWeb/ldexpress_tissues', methods=['GET'])
def ldexpress_tissues():
    start_time = time.time()
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    try:
        results = get_ldexpress_tissues(web)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.debug("Retrieved LDexpress tissues (%ss)" % (round(end_time - start_time, 2)))
    return results

# Route to retrieve platform data for SNPchip
@app.route('/LDlinkRest/snpchip_platforms', methods=['GET'])
#@app.route('/LDlinkRest2/snpchip_platforms', methods=['GET'])
@app.route('/LDlinkRestWeb/snpchip_platforms', methods=['GET'])
def snpchip_platforms():
    start_time = time.time()
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    try:
        results = get_platform_request(web)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.debug("Retrieved SNPchip Platforms (%ss)" % (round(end_time - start_time, 2)))
    return results

# Route to retrieve timestamp from last LDtrait data update
@app.route('/LDlinkRest/ldtrait_timestamp', methods=['GET'])
#@app.route('/LDlinkRest2/ldtrait_timestamp', methods=['GET'])
@app.route('/LDlinkRestWeb/ldtrait_timestamp', methods=['GET'])
def ldtrait_timestamp():
    start_time = time.time()
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    try:
        results = get_ldtrait_timestamp(web)
    except Exception as e:
        exc_obj = e
        app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.debug("Retrieve LDtrait Timestamp (%ss)" % (round(end_time - start_time, 2)))
    return results

### LDLink Main Module Routes ###

# Web and API route for LDassoc
@app.route('/LDlinkRest/ldassoc', methods=['GET'])
#@app.route('/LDlinkRest2/ldassoc', methods=['GET'])
@app.route('/LDlinkRestWeb/ldassoc', methods=['GET'])
def ldassoc():
    start_time = time.time()
    ldassoc_example_dir = param_list['ldassoc_example_dir']
    data_dir = param_list['data_dir']
    myargs = argparse.Namespace()
    myargs.window = None
    filename = secure_filename(request.args.get('filename', False))
    region = request.args.get('calculateRegion')
    pop = request.args.get('pop', False)
    genome_build = request.args.get('genome_build', 'grch37')
    myargs.dprime = bool(request.args.get("dprime") == "True")
    myargs.chr = str(request.args.get('columns[chromosome]'))
    myargs.bp = str(request.args.get('columns[position]'))
    myargs.pval = str(request.args.get('columns[pvalue]'))
    if bool(request.args.get("useEx") == "True"):
        filename = data_dir + ldassoc_example_dir + genome_build_vars[genome_build]['ldassoc_example_file']
    else:
        filename = os.path.join(app.config['UPLOAD_DIR'], secure_filename(str(request.args.get('filename'))))
    if region == "variant":
        # print("Region is variant")
        # print("index: " + str(request.args.get('variant[index]')))
        # print("base pair window: " + request.args.get('variant[basepair]'))
        # print()
        myargs.window = int(request.args.get('variant[basepair]'))
        if request.args.get('variant[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('variant[index]')
    if region == "gene":
        # print("Region is gene")
        if request.args.get('gene[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('gene[index]')
        myargs.name = request.args.get('gene[name]')
        myargs.window = int(request.args.get('gene[basepair]'))
    if region == "region":
        # print("Region is region")
        if request.args.get('region[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('region[index]')
        myargs.start = str(request.args.get('region[start]'))
        myargs.end = str(request.args.get('region[end]'))
    myargs.transcript = bool(request.args.get("transcript") == "True")
    # print("transcript: " + str(myargs.transcript))
    #myargs.annotate = bool(request.args.get("annotate") == "True")
    myargs.annotate = request.args.get("annotate")
    #print("annotate: " + str(myargs.annotate))
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print('reference: ' + reference)
        app.logger.debug('ldassoc params ' + json.dumps({
            'filename': filename,
            'region': region,
            'pop': pop,
            'reference': reference,
            'genome_build': genome_build,
            'web': web,
            'myargs': str(myargs)
        }, indent=4, sort_keys=True))
        try:
            out_json = calculate_assoc(filename, region, pop, reference, genome_build, web, myargs)
        except Exception as e:
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        # PROGRAMMATIC ACCESS NOT AVAILABLE
    end_time = time.time()
    app.logger.info("Executed LDassoc (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web and API route for LDexpress
@app.route('/LDlinkRest/ldexpress', methods=['POST'])
#@app.route('/LDlinkRest2/ldexpress', methods=['POST'])
@app.route('/LDlinkRestWeb/ldexpress', methods=['POST'])
@requires_token
def ldexpress():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data['snps']
    pop = data['pop']
    tissues = data['tissues']
    r2_d = data['r2_d']
    r2_d_threshold = data['r2_d_threshold']
    p_threshold = data['p_threshold']
    window = data['window'].replace(',', '') if 'window' in data else '500000'
    token = request.args.get('token', False)
    genome_build = data['genome_build'] if 'genome_build' in data else 'grch37'
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(data['reference'])
            snplist = "+".join([snp.strip().lower() for snp in snps.splitlines()])
            app.logger.debug('ldexpress params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'tissues': tissues,
                'r2_d': r2_d,
                'r2_d_threshold': r2_d_threshold,
                'window': window,
                'token': token,
                'genome_build': genome_build,
                'web': web,
                'reference': reference
            }, indent=4, sort_keys=True))
            try:
                express = {}
                (query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings) = calculate_express(snplist, pop, reference, web, tissues, r2_d, genome_build, float(r2_d_threshold), float(p_threshold), int(window))
                express["query_snps"] = query_snps
                express["thinned_snps"] = thinned_snps
                express["thinned_genes"] = thinned_genes
                express["thinned_tissues"] = thinned_tissues
                express["details"] = details

                if "error" in errors_warnings:
                    express["error"] = errors_warnings["error"]
                else:
                    with open(tmp_dir + 'express_variants_annotated' + reference + '.txt', 'w') as f:
                        f.write("Query\tRS ID\tPosition\tR2\tD'\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n")
                        # for snp in thinned_snps:
                        for matched_gwas in details["results"]["aaData"]:
                            f.write("\t".join(str(element.split("__")[0]) for element in matched_gwas) + "\n")
                        if "warning" in errors_warnings:
                            express["warning"] = errors_warnings["warning"]
                            f.write("Warning(s):\n")
                            f.write(express["warning"])
                out_json = json.dumps(express, sort_keys=False)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        snplist = "+".join([snp.strip().lower() for snp in snps.splitlines()])
        app.logger.debug('ldexpress params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'tissues': tissues,
                'r2_d': r2_d,
                'r2_d_threshold': r2_d_threshold,
                'window': window,
                'token': token,
                'genome_build': genome_build,
                'web': web,
                'reference': reference
            }, indent=4, sort_keys=True))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            (query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings) = calculate_express(snplist, pop, reference, web, tissues, r2_d, genome_build, float(r2_d_threshold), float(p_threshold), int(window))
            # with open(tmp_dir + "express" + reference + ".json") as f:
            #     json_dict = json.load(f)
            if "error" in errors_warnings:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(errors_warnings["error"])
            else:
                with open(tmp_dir + 'express_variants_annotated' + reference + '.txt', 'w') as f:
                    f.write("Query\tRS ID\tPosition\tR2\tD'\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n")
                    # for snp in thinned_snps:
                    for matched_gwas in details["results"]["aaData"]:
                        f.write("\t".join(str(element.split("__")[0]) for element in matched_gwas) + "\n")
                    if "warning" in errors_warnings:
                        # express["warning"] = errors_warnings["warning"]
                        f.write("Warning(s):\n")
                        f.write(errors_warnings["warning"])
                # display api out
                try:
                    with open(tmp_dir + 'express_variants_annotated' + reference + '.txt', 'r') as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDexpress (%ss)" % (round(end_time - start_time, 2)))
                    return content
                except Exception as e:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    exc_obj = e
                    app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            toggleLocked(token, 0)
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDexpress (%ss)" % (round(end_time - start_time, 2)))
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for LDhap
@app.route('/LDlinkRest/ldhap', methods=['GET'])
#@app.route('/LDlinkRest2/ldhap', methods=['GET'])
@app.route('/LDlinkRestWeb/ldhap', methods=['GET'])
@requires_token
def ldhap():
    start_time = time.time()
    snps = request.args.get('snps', False)
    pop = request.args.get('pop', False)
    token = request.args.get('token', False)
    genome_build = request.args.get('genome_build', 'grch37')
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            # print('request: ' + str(reference))
            app.logger.debug('LDhap params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'token': token,
                'genome_build': genome_build,
                'reference': reference,
                'web': web
            }, indent=4, sort_keys=True))
            snplst = tmp_dir + 'snps' + reference + '.txt'
            with open(snplst, 'w') as f:
                f.write(snps.lower())
            try:
                out_json = calculate_hap(snplst, pop, reference, web, genome_build)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug('LDhap params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'token': token,
                'genome_build': genome_build,
                'reference': reference,
                'web': web
        }, indent=4, sort_keys=True))
        snplst = tmp_dir + 'snps' + reference + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_hap(snplst, pop, reference, web, genome_build)
            if 'error' in json.loads(out_json):
                toggleLocked(token, 0)
                return sendTraceback(json.loads(out_json)["error"])
            # display api out
            try: 
                # unlock token then display api output
                resultFile1 = tmp_dir + "snps_" + reference + ".txt"
                resultFile2 = tmp_dir + "haplotypes_" + reference + ".txt"
                with open(resultFile1, "r") as fp:
                    content1 = fp.read()
                with open(resultFile2, "r") as fp:
                    content2 = fp.read()
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed LDhap (%ss)" % (round(end_time - start_time, 2)))
                return content1 + "\n" + "#####################################################################################" + "\n\n" + content2
            except Exception as e:
                # unlock token then display error message
                output = json.loads(out_json)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(output["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDhap (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)

# Web and API route for LDmatrix
@app.route('/LDlinkRest/ldmatrix', methods=['GET', 'POST'])
#@app.route('/LDlinkRest2/ldmatrix', methods=['GET', 'POST'])
@app.route('/LDlinkRestWeb/ldmatrix', methods=['GET'])
@requires_token
def ldmatrix():
    start_time = time.time()
    # differentiate POST or GET request
    if request.method == 'POST':
        # POST REQUEST
        data = json.loads(request.stream.read())
        snps = data['snps'] if 'snps' in data else False
        pop = data['pop'] if 'pop' in data else False
        reference = data['reference'] if 'reference' in data else False
        r2_d = data['r2_d'] if 'r2_d' in data else False
        genome_build = data['genome_build'] if 'genome_build' in data else 'grch37'
        collapseTranscript = data['collapseTranscript'] if 'collapseTranscript' in data else True
    else:
        # GET REQUEST
        snps = request.args.get('snps', False)
        pop = request.args.get('pop', False)
        reference = request.args.get('reference', False)
        r2_d = request.args.get('r2_d', False)
        genome_build = request.args.get('genome_build', 'grch37')
        collapseTranscript = request.args.get('collapseTranscript', True)
    token = request.args.get('token', False)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            annotate = request.args.get('annotate',True)
            # print('request: ' + str(reference))
            app.logger.debug('ldmatrix params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'r2_d': r2_d,
                'token': token,
                'genome_build': genome_build,
                'collapseTranscript': collapseTranscript,
                'web': web,
                'reference': reference,
                'annotate' : annotate
            }, indent=4, sort_keys=True))
            snplst = tmp_dir + 'snps' + str(reference) + '.txt'
            with open(snplst, 'w') as f:
                f.write(snps.lower())
            try:
                out_script, out_div = calculate_matrix(snplst, pop, reference, web, str(request.method), genome_build, r2_d, collapseTranscript,annotate)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug('ldmatrix params ' + json.dumps({
            'snps': snps,
            'pop': pop,
            'r2_d': r2_d,
            'token': token,
            'genome_build': genome_build,
            'collapseTranscript': collapseTranscript,
            'web': web,
            'reference': reference
        }, indent=4, sort_keys=True))
        # print('request: ' + str(reference)) 
        snplst = tmp_dir + 'snps' + str(reference) + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_matrix(snplst, pop, reference, web, str(request.method), genome_build, r2_d, collapseTranscript)
            with open(tmp_dir + "matrix" + reference + ".json") as f:
                json_dict = json.load(f)
            if 'error' in json_dict:
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            # display api out
            try:
                # unlock token then display api output
                resultFile = ""
                if r2_d == "d":
                    resultFile = tmp_dir + "d_prime_"+reference+".txt"
                else:
                    resultFile = tmp_dir + "r2_"+reference+".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed LDmatrix (%ss)" % (round(end_time - start_time, 2)))
                return content
            except Exception as e:
                # unlock token then display error message
                with open(tmp_dir + "matrix" + reference + ".json") as f:
                    json_dict = json.load(f)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(json_dict["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDmatrix (%ss)" % (round(end_time - start_time, 2)))
    return out_script + "\n " + out_div

# Web and API route for LDpair
@app.route('/LDlinkRest/ldpair', methods=['GET', 'POST'])
#@app.route('/LDlinkRest2/ldpair', methods=['GET', 'POST'])
@app.route('/LDlinkRestWeb/ldpair', methods=['GET'])
@requires_token
def ldpair():
    start_time = time.time()
    if request.method == 'POST':
        # POST REQUEST
        try:
            data = json.loads(request.stream.read())
        except Exception as e:
            return sendTraceback("Invalid JSON input.")
        snp_pairs = data['snp_pairs'] if 'snp_pairs' in data else []
        pop = data['pop'] if 'pop' in data else False
        genome_build = data['genome_build'] if 'genome_build' in data else 'grch37'
        json_out = data['json_out'] if 'json_out' in data else False
    else:
        # GET REQUEST
        var1 = request.args.get('var1', "")
        var2 = request.args.get('var2', "")
        snp_pairs = [[var1, var2]]
        pop = request.args.get('pop', False)
        genome_build = request.args.get('genome_build', 'grch37')
        json_out = request.args.get('json_out', False)
    if json_out in [False, "false", "False"]:
        json_out = False
    elif json_out in [True, "true", "True"]:
        json_out = True
    else:
        json_out = False
    token = request.args.get('token', False)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
            app.logger.debug('ldpair params ' + json.dumps({
                'snp_pairs': snp_pairs,
                'pop': pop,
                'token': token,
                'genome_build': genome_build,
                'web': web,
                'reference': reference,
                'json_out': json_out
            }, indent=4, sort_keys=True))
            # print('request: ' + str(reference))
            try:
                out_json = calculate_pair(snp_pairs, pop, web, genome_build, reference)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug('ldpair params ' + json.dumps({
            'snp_pairs': snp_pairs,
            'pop': pop,
            'token': token,
            'genome_build': genome_build,
            'web': web,
            'reference': reference,
            'json_out': json_out
        }, indent=4, sort_keys=True))
        # print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pair(snp_pairs, pop, web, genome_build, reference)
            #if there is error, the out_json should be json format not as array
            if 'error' in json.loads(out_json):
                toggleLocked(token, 0)
                return sendTraceback(json.loads(out_json)["error"])
            # display api out
            try:
                # unlock token then display api output
                # if user set json=true, output format is json
                if json_out or len(json.loads(out_json)) > 1:
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDpair (%ss)" % (round(end_time - start_time, 2)))
                    return current_app.response_class(out_json, mimetype='application/json')
                else:
                    #right inputs output as text
                    with open(tmp_dir + 'LDpair_' + reference + '.txt', "r") as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDpair (%ss)" % (round(end_time - start_time, 2)))
                    return content
            except Exception as e:
                # unlock token then display error message
                output = json.loads(out_json)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(output["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDpair (%ss)" % (round(end_time - start_time, 2)))
 
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for LDpop
@app.route('/LDlinkRest/ldpop', methods=['GET'])
#@app.route('/LDlinkRest2/ldpop', methods=['GET'])
@app.route('/LDlinkRestWeb/ldpop', methods=['GET'])
@requires_token
def ldpop():
    start_time = time.time()
    var1 = request.args.get('var1', False)
    var2 = request.args.get('var2', False)
    pop = request.args.get('pop', False)
    r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    genome_build = request.args.get('genome_build', 'grch37')
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            app.logger.debug('ldpop params ' + json.dumps({
                'var1': var1,
                'var2': var2,
                'pop': pop,
                'token': token,
                'genome_build': genome_build,
                'web': web,
                'reference': reference
            }, indent=4, sort_keys=True))
            # print('request: ' + str(reference))
            try:
                out_json = calculate_pop(var1, var2, pop, r2_d, web, genome_build, reference)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug('ldpop params ' + json.dumps({
            'var1': var1,
            'var2': var2,
            'pop': pop,
            'token': token,
            'genome_build': genome_build,
            'web': web,
            'reference': reference
        }, indent=4, sort_keys=True))
        # print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pop(var1, var2, pop, r2_d, web, genome_build, reference)
            if 'error' in json.loads(out_json):
                toggleLocked(token, 0)
                return sendTraceback(json.loads(out_json)["error"])
            # display api out
            try:
                # unlock token then display api output
                with open(tmp_dir + 'LDpop_' + reference + '.txt', "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed LDpop (%ss)" % (round(end_time - start_time, 2)))
                return content
            except Exception as e:
                # unlock token then display error message
                # output = json.loads(out_json)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(out_json["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDpop (%ss)" % (round(end_time - start_time, 2)))
    print("ERRR",out_json)
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for LDproxy
@app.route('/LDlinkRest/ldproxy', methods=['GET'])
#@app.route('/LDlinkRest2/ldproxy', methods=['GET'])
@app.route('/LDlinkRestWeb/ldproxy', methods=['GET'])
@requires_token
def ldproxy():
    start_time = time.time()
    var = request.args.get('var', False)
    pop = request.args.get('pop', False)
    r2_d = request.args.get('r2_d', False)
    window = request.args.get('window', '500000').replace(',', '')
    token = request.args.get('token', False)
    genome_build = request.args.get('genome_build', 'grch37')
    collapseTranscript = request.args.get('collapseTranscript', True)
    #annotateText = request.args.get('annotate', False)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            annotate = request.args.get('annotate', False)
            # print('request: ' + str(reference))
            app.logger.debug('ldproxy params ' + json.dumps({
                'var': var,
                'pop': pop,
                'r2_d': r2_d,
                'token': token,
                'window': window,
                'collapseTranscript': collapseTranscript,
                'genome_build': genome_build,
                'web': web,
                'reference': reference,
                'annotate': annotate
            }, indent=4, sort_keys=True))
            try:
                out_script, out_div = calculate_proxy(var, pop, reference, web, genome_build, r2_d, int(window), collapseTranscript,annotate)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        # print('request: ' + str(reference))
        app.logger.debug('ldproxy params ' + json.dumps({
            'var': var,
            'pop': pop,
            'r2_d': r2_d,
            'token': token,
            'window': window,
            'collapseTranscript': collapseTranscript,
            'genome_build': genome_build,
            'web': web,
            'reference': reference
        }, indent=4, sort_keys=True))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_proxy(var, pop, reference, web, genome_build, r2_d, int(window), collapseTranscript)
            with open(tmp_dir + "proxy" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            # display api out
            try:
                # unlock token then display api output
                with open(tmp_dir + 'proxy' + reference + '.txt', "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed LDproxy (%ss)" % (round(end_time - start_time, 2)))
                return content
            except Exception as e:
                # unlock token then display error message
                with open(tmp_dir + "proxy" + reference + ".json") as f:
                    json_dict = json.load(f)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(json_dict["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDproxy (%ss)" % (round(end_time - start_time, 2)))
    return out_script + "\n " + out_div

# Web and API route for LDtrait
@app.route('/LDlinkRest/ldtrait', methods=['POST'])
#@app.route('/LDlinkRest2/ldtrait', methods=['POST'])
@app.route('/LDlinkRestWeb/ldtrait', methods=['POST'])
@requires_token
def ldtrait():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data['snps']
    pop = data['pop']
    r2_d = data['r2_d']
    r2_d_threshold = data['r2_d_threshold']
    window = data['window'].replace(',', '') if 'window' in data else '500000'
    token = request.args.get('token', False)
    genome_build = data['genome_build'] if 'genome_build' in data else 'grch37'
    web = False
   
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            if data['ifContinue']:
                ifContinue = data['ifContinue'] 
                ifContinue = bool(ifContinue!="False")
            reference = str(data['reference'])
            app.logger.debug('ldtrait params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'r2_d': r2_d,
                'r2_d_threshold': r2_d_threshold,
                'token': token,
                'window': window,
                'genome_build': genome_build,
                'web': web,
                'reference': reference,
                'continue':ifContinue
            }, indent=4, sort_keys=True))
            snpfile = str(tmp_dir + 'snps' + reference + '.txt')
            snplist = snps.splitlines()
            with open(snpfile, 'w') as f:
                for s in snplist:
                    s = s.lstrip()
                    if(s[:2].lower() == 'rs' or s[:3].lower() == 'chr'):
                        f.write(s.lower() + '\n')
            try:
                trait = {}
                # snplst, pop, request, web, r2_d, threshold
                (query_snps, thinned_snps, details) = calculate_trait(snpfile, pop, reference, web, r2_d, genome_build, float(r2_d_threshold), int(window),ifContinue)
                trait["query_snps"] = query_snps
                trait["thinned_snps"] = thinned_snps
                trait["details"] = details

                with open(tmp_dir + "trait" + reference + ".json") as f:
                    json_dict = json.load(f)
                if "error" in json_dict:
                    trait["error"] = json_dict["error"]
                else:
                    with open(tmp_dir + 'trait_variants_annotated' + reference + '.txt', 'w') as f:
                        f.write("Query\tGWAS Trait\tRS Number\tPosition (" + genome_build_vars[genome_build]['title'] + ")\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n")
                        for snp in thinned_snps:
                            for matched_gwas in details[snp]["aaData"]:
                                f.write(snp + "\t")
                                f.write("\t".join([str(element) for i, element in enumerate(matched_gwas) if i not in {6, 11}]) + "\n")
                        if "warning" in json_dict:
                            trait["warning"] = json_dict["warning"]
                            f.write("Warning(s):\n")
                            f.write(trait["warning"])
                out_json = json.dumps(trait, sort_keys=False)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug('ldtrait params ' + json.dumps({
            'snps': snps,
            'pop': pop,
            'r2_d': r2_d,
            'r2_d_threshold': r2_d_threshold,
            'token': token,
            'window': window,
            'genome_build': genome_build,
            'web': web,
            'reference': reference
        }, indent=4, sort_keys=True))
        snpfile = str(tmp_dir + 'snps' + reference + '.txt')
        snplist = snps.splitlines()
        with open(snpfile, 'w') as f:
            for s in snplist:
                s = s.lstrip()
                if(s[:2].lower() == 'rs' or s[:3].lower() == 'chr'):
                    f.write(s.lower() + '\n')
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            app.logger.debug('begin to call trait')
            try:
                (query_snps, thinned_snps, details) = calculate_trait(snpfile, pop, reference, web, r2_d, genome_build, float(r2_d_threshold), int(window))
            except Exception as e:
                app.logger.debug('after call trait',e)
            except :
                app.logger.debug('timeout error')

            with open(tmp_dir + "trait" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            else:
                with open(tmp_dir + 'trait_variants_annotated' + reference + '.txt', 'w') as f:
                    f.write("Query\tGWAS Trait\tRS Number\tPosition (" + genome_build_vars[genome_build]['title'] + ")\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n")
                    for snp in thinned_snps:
                        for matched_gwas in details[snp]["aaData"]:
                            f.write(snp + "\t")
                            f.write("\t".join([str(element) for i, element in enumerate(matched_gwas) if i not in {6, 11}]) + "\n")
                    if "warning" in json_dict:
                        # trait["warning"] = json_dict["warning"]
                        f.write("Warning(s):\n")
                        f.write(json_dict["warning"])
                # display api out
                try:
                    with open(tmp_dir + 'trait_variants_annotated' + reference + '.txt', 'r') as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDtrait (%ss)" % (round(end_time - start_time, 2)))
                    return content
                except Exception as e:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    exc_obj = e
                    app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            app.logger.debug('error to call trait',e)
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
        except:
            app.logger.debug('timeout except')
            toggleLocked(token, 0)
            print("timeout error")
        else:
            app.logger.debug('time out else')
            print("time out")
    end_time = time.time()
    app.logger.info("Executed LDtrait (%ss)" % (round(end_time - start_time, 2)))
    return current_app.response_class(out_json, mimetype='application/json')


# Web and API route for SNPchip
@app.route('/LDlinkRest/snpchip', methods=['GET', 'POST'])
#@app.route('/LDlinkRest2/snpchip', methods=['GET', 'POST'])
@app.route('/LDlinkRestWeb/snpchip', methods=['GET', 'POST'])
@requires_token
def snpchip():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data['snps']
    genome_build = data['genome_build'] if 'genome_build' in data else 'grch37'
    platforms = data['platforms']
    token = request.args.get('token', False)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(data['reference'])
            app.logger.debug('snpchip params ' + json.dumps({
                'snps': snps,
                'token': token,
                'platforms': platforms,
                'genome_build': genome_build,
                'web': web,
                'reference': reference
            }, indent=4, sort_keys=True))
            snplst = tmp_dir + 'snps' + reference + '.txt'
            with open(snplst, 'w') as f:
                f.write(snps.lower())
            try:
                snp_chip = calculate_chip(snplst, platforms, web, reference, genome_build)
                out_json = json.dumps(snp_chip, sort_keys=True, indent=2)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        # print('request: ' + reference)
        app.logger.debug('snpchip params ' + json.dumps({
            'snps': snps,
            'token': token,
            'platforms': platforms,
            'genome_build': genome_build,
            'web': web,
            'reference': reference
        }, indent=4, sort_keys=True))
        snplst = tmp_dir + 'snps' + reference + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            snp_chip = calculate_chip(snplst, platforms, web, reference, genome_build)
            if 'error' in json.loads(snp_chip) and len(json.loads(snp_chip)["error"]) > 0:
                toggleLocked(token, 0)
                return sendTraceback(json.loads(snp_chip)["error"])
            # display api out
            try:
                # unlock token then display api output
                resultFile = tmp_dir + "details"+reference+".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed SNPchip (%ss)" % (round(end_time - start_time, 2)))
                return content
            except Exception as e:
                # unlock token then display error message
                out_json = json.dumps(snp_chip, sort_keys=True, indent=2)
                output = json.loads(out_json)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(output["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed SNPchip (%ss)" % (round(end_time - start_time, 2)))
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for SNPclip
@app.route('/LDlinkRest/snpclip', methods=['POST'])
#@app.route('/LDlinkRest2/snpclip', methods=['POST'])
@app.route('/LDlinkRestWeb/snpclip', methods=['POST'])
@requires_token
def snpclip():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data['snps']
    pop = data['pop']
    r2_threshold = data['r2_threshold']
    maf_threshold = data['maf_threshold']
    token = request.args.get('token', False)
    genome_build = data['genome_build'] if 'genome_build' in data else 'grch37'
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(data['reference'])
            app.logger.debug('snpclip params ' + json.dumps({
                'snps': snps,
                'pop': pop,
                'token': token,
                'r2_threshold': r2_threshold,
                'maf_threshold': maf_threshold,
                'genome_build': genome_build,
                'web': web,
                'reference': reference
            }, indent=4, sort_keys=True))
            snpfile = str(tmp_dir + 'snps' + reference + '.txt')
            snplist = snps.splitlines()
            with open(snpfile, 'w') as f:
                for s in snplist:
                    s = s.lstrip()
                    if(s[:2].lower() == 'rs' or s[:3].lower() == 'chr'):
                        f.write(s.lower() + '\n')
            try:
                clip = {}
                (snps, snp_list, details) = calculate_clip(snpfile, pop, reference, web, genome_build, float(r2_threshold), float(maf_threshold))
                clip["snp_list"] = snp_list
                clip["details"] = details
                clip["snps"] = snps
                clip["filtered"] = collections.OrderedDict()
                with open(tmp_dir + "clip" + reference + ".json") as f:
                    json_dict = json.load(f)
                if "error" in json_dict:
                    clip["error"] = json_dict["error"]
                else:
                    for snp in snps:
                        clip["filtered"][snp[0]] = details[snp[0]]
                    if "warning" in json_dict:
                        clip["warning"] = json_dict["warning"]
                with open(tmp_dir + 'snp_list' + reference + '.txt', 'w') as f:
                    for rs_number in snp_list:
                        f.write(rs_number + '\n')
                with open(tmp_dir + 'details' + reference + '.txt', 'w') as f:
                    f.write("RS Number\tPosition\tAlleles\tDetails\n")
                    if(type(details) is collections.OrderedDict):
                        for snp in snps:
                            f.write(snp[0] + "\t" + "\t".join(details[snp[0]]))
                            f.write("\n")
                out_json = json.dumps(clip, sort_keys=False)
            except Exception as e:
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug('snpclip params ' + json.dumps({
            'snps': snps,
            'pop': pop,
            'token': token,
            'r2_threshold': r2_threshold,
            'maf_threshold': maf_threshold,
            'genome_build': genome_build,
            'web': web,
            'reference': reference
        }, indent=4, sort_keys=True))
        snpfile = str(tmp_dir + 'snps' + reference + '.txt')
        snplist = snps.splitlines()
        with open(snpfile, 'w') as f:
            for s in snplist:
                s = s.lstrip()
                if(s[:2].lower() == 'rs' or s[:3].lower() == 'chr'):
                    f.write(s.lower() + '\n')
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            (snps, snp_list, details) = calculate_clip(snpfile, pop, reference, web, genome_build, float(r2_threshold), float(maf_threshold))
            with open(tmp_dir + "clip" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            with open(tmp_dir + 'details' + reference + '.txt', 'w') as f:
                f.write("RS Number\tPosition\tAlleles\tDetails\n")
                if(type(details) is collections.OrderedDict):
                    for snp in snps:
                        f.write(snp[0] + "\t" + "\t".join(details[snp[0]]))
                        f.write("\n")
            # display api out
            try:
                # unlock token then display api output
                resultFile = tmp_dir + "details" + reference + ".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                with open(tmp_dir + "clip" + reference + ".json") as f:
                    json_dict = json.load(f)
                    if "error" in json_dict:
                        toggleLocked(token, 0)
                        return sendTraceback(json_dict["error"])
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed SNPclip (%ss)" % (round(end_time - start_time, 2)))
                return content
            except Exception as e:
                # unlock token then display error message
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed SNPclip (%ss)" % (round(end_time - start_time, 2)))
    return current_app.response_class(out_json, mimetype='application/json')

### Add Request Headers & Initialize Flags ###
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

def unlock_tokens_background():
    db = connectMongoDBReadOnly()
    while True:
        config = get_config()
        lock_timeout =  config['token_lock_timeout']
        try:
            unlock_stale_tokens(db, lock_timeout)
        except Exception as e:
            print(e)
        time.sleep(lock_timeout / 2)

Thread(name='unlock_tokens_background', target=unlock_tokens_background).start()

if is_main:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number",
                        default="9982", help="Sets the Port")
    parser.add_argument("-d", dest="debug", default="False",
                        help="Sets the Debugging Option")
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number)
    # debugger = args.debug == 'True'
    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, use_evalex=False)
    # app.logger.disabled = True
    # application = DebuggedApplication(app, True)
    app.debug = False