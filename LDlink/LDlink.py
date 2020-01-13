#!flask/bin/python3
import pandas as pd
import numpy as np
import sys
import getopt
import cgi
import shutil
import os
import traceback
import urllib
import collections
import argparse
import json
import time
import random
import requests
import yaml
from flask import Flask, render_template, Response, abort, request, make_response, url_for, jsonify, redirect, current_app, jsonify, url_for
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from functools import wraps
from xml.sax.saxutils import escape, unescape
from socket import gethostname
from pandas import DataFrame
from LDpair import calculate_pair
from LDpop import calculate_pop
from LDproxy import calculate_proxy
from LDtrait import calculate_trait
from LDmatrix import calculate_matrix
from LDhap import calculate_hap
from LDassoc import calculate_assoc
from SNPclip import calculate_clip
from SNPchip import calculate_chip, get_platform_request
from RegisterAPI import register_user, checkToken, checkBlocked, checkLocked, toggleLocked, logAccess, emailJustification, blockUser, unblockUser, getToken, getStats, unlockUser, unlockAllUsers, getLockedUsers, getBlockedUsers
from werkzeug.utils import secure_filename
from werkzeug.debug import DebuggedApplication

# Ensure tmp directory exists
tmp_dir = "./tmp/"
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

### Initialize Flask App ###

app = Flask(__name__, static_folder='', static_url_path='/')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024
app.config['UPLOAD_DIR'] = os.path.join(os.getcwd(), 'tmp')
app.debug = True

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

# Return error and traceback from calculations
def sendTraceback(error):
    custom = {}
    if (error is None):
        custom["error"] = "Raised when a generated error does not fall into any category."
    else:
        custom["error"] = error
    print("Unexpected error:", sys.exc_info()[0])
    traceback.print_exc()
    custom["traceback"] = traceback.format_exc()
    out_json = json.dumps(custom, sort_keys=False, indent=2)
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
    if "ldhap" in fullPath:
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
        with open('config.yml', 'r') as c:
            config = yaml.load(c)
        env = config['env']
        if env == 'local':
            url_root = 'http://localhost:5000/'
        elif env == 'prod':
            url_root = 'https://ldlink.nci.nih.gov/'
        else:
            url_root = 'https://ldlink' + env + '.nci.nih.gov/'
        require_token = bool(config['api']['require_token'])
        token_expiration = bool(config['api']['token_expiration'])
        token_expiration_days = config['api']['token_expiration_days']
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
                # Check if token is locked
                if checkLocked(token):
                    return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
        with open('config.yml', 'r') as c:
            config = yaml.load(c)
        api_superuser = config['api']['api_superuser']
        # api_access_dir = config['api']['api_access_dir']
        api_superuser_token = getToken(api_superuser)
        # Check if token argument is missing in api call
        if 'token' not in request.args:
            return sendTraceback('Admin API token missing.')
        token = request.args['token']
        # Check if token is valid
        if token != api_superuser_token or token is None:
            return sendTraceback('Invalid Admin API token.')
        return f(*args, **kwargs)
    return decorated_function

# Web route to send API token unblock request from front-end
@app.route('/LDlinkRestWeb/apiaccess/apiblocked_web', methods=['GET'])
def apiblocked_web():
    print("Execute api blocked user justification submission")
    firstname = request.args.get('firstname', False)
    lastname = request.args.get('lastname', False)
    email = request.args.get('email', False)
    institution = request.args.get('institution', False)
    registered = request.args.get('registered', False)
    blocked = request.args.get('blocked', False)
    justification = request.args.get('justification', False)
    out_json = emailJustification(firstname, lastname, email, institution, registered, blocked, justification, request.url_root)
    return sendJSON(out_json)

# Web route to register user's email for API token
@app.route('/LDlinkRestWeb/apiaccess/register_web', methods=['GET'])
def register_web():
    print("Execute api register user")
    firstname = request.args.get('firstname', False)
    lastname = request.args.get('lastname', False)
    email = request.args.get('email', False)
    institution = request.args.get('institution', False)
    reference = request.args.get('reference', False)
    out_json = register_user(firstname, lastname, email, institution, reference, request.url_root)
    out_json2 = {
        "message": out_json["message"],
        "email": out_json["email"],
        "firstname": out_json["firstname"],
        "lastname": out_json["lastname"],
        "registered": out_json["registered"],
        "blocked": out_json["blocked"],
        "institution": out_json["institution"]
    }
    return sendJSON(out_json2)

# Web route to block user's API token
@app.route('/LDlinkRestWeb/apiaccess/block_user', methods=['GET'])
@requires_admin_token
def block_user():
    print("Execute api block user")
    email = request.args.get('email', False)
    out_json = blockUser(email, request.url_root)
    return sendJSON(out_json)

# Web route to unblock user's API token
@app.route('/LDlinkRestWeb/apiaccess/unblock_user', methods=['GET'])
@requires_admin_token
def unblock_user():
    print("Execute api unblock user")
    email = request.args.get('email', False)
    out_json = unblockUser(email)
    return sendJSON(out_json)

# Web route to unlock user's API token
@app.route('/LDlinkRestWeb/apiaccess/unlock_user', methods=['GET'])
@requires_admin_token
def unlock_user():
    print("Execute api unlock user")
    email = request.args.get('email', False)
    out_json = unlockUser(email)
    return sendJSON(out_json)

# Web route to unlock all users API tokens
@app.route('/LDlinkRestWeb/apiaccess/unlock_all_users', methods=['GET'])
@requires_admin_token
def unlock_all_users():
    print("Execute api unlock all users")
    out_json = unlockAllUsers()
    return sendJSON(out_json)

# Web route to retrieve API log stats
@app.route('/LDlinkRestWeb/apiaccess/stats', methods=['GET'])
@requires_admin_token
def api_stats():
    print("Execute api stats")
    startdatetime = request.args.get('startdatetime', False)
    enddatetime = request.args.get('enddatetime', False)
    top = request.args.get('top', False)
    out_json = getStats(startdatetime, enddatetime, top)
    return sendJSON(out_json)

# Web route to retrieve all locked API users
@app.route('/LDlinkRestWeb/apiaccess/locked_users', methods=['GET'])
@requires_admin_token
def api_locked_users():
    print("Execute api locked users stats")
    out_json = getLockedUsers()
    return sendJSON(out_json)

# Web route to retrieve all blocked API users
@app.route('/LDlinkRestWeb/apiaccess/blocked_users', methods=['GET'])
@requires_admin_token
def api_blocked_users():
    print("Execute api blocked users stats")
    out_json = getBlockedUsers()
    return sendJSON(out_json)

### LDLink Helper Routes ###

# Copy output files from tools' tmp directory to apache tmp directory
@app.route('/')
def root():
    return app.send_static_file('index.html')
    # with open('config.yml', 'r') as c:
    #     config = yaml.load(c)
    # env = config['env']
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
@app.route('/ping/', strict_slashes=False)
def ping():
    print("pong")
    try:
        return "true"
    except Exception as e:
        print('------------EXCEPTION------------')
        traceback.print_exc(1)
        return str(e), 400

# Route to check file exist status 
@app.route('/status/<path:filename>', strict_slashes=False)
def status(filename):
    return jsonify(os.path.isfile(filename))

# File upload route
@app.route('/LDlinkRest/upload', methods=['POST'])
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
@app.route('/LDlinkRestWeb/ldassoc_example', methods=['GET'])
def ldassoc_example():
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    example_dir = config['data']['example_dir']
    example_filepath = example_dir + 'prostate_example.txt'
    example = {
        'filename': os.path.basename(example_filepath),
        'headers': read_csv_headers(example_filepath)
    }
    return json.dumps(example)

# Route to retrieve platform data for SNPchip
@app.route('/LDlinkRest/snpchip_platforms', methods=['GET'])
@app.route('/LDlinkRestWeb/snpchip_platforms', methods=['GET'])
def snpchip_platforms():
    print("Retrieve SNPchip Platforms")
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    return get_platform_request(web)

### LDLink Main Module Routes ###

# Web and API route for LDassoc
@app.route('/LDlinkRest/ldassoc', methods=['GET'])
@app.route('/LDlinkRestWeb/ldassoc', methods=['GET'])
def ldassoc():
    print("Execute ldassoc.")
    with open('config.yml', 'r') as c:
        config = yaml.load(c)
    example_dir = config['data']['example_dir']
    myargs = argparse.Namespace()
    myargs.window = None
    filename = secure_filename(request.args.get('filename', False))
    region = request.args.get('calculateRegion')
    pop = request.args.get('pop', False)
    print('filename: ' + filename)
    print('region: ' + region)
    print('pop: ' + pop)
    myargs.dprime = bool(request.args.get("dprime") == "True")
    myargs.chr = str(request.args.get('columns[chromosome]'))
    myargs.bp = str(request.args.get('columns[position]'))
    myargs.pval = str(request.args.get('columns[pvalue]'))
    print("dprime: " + str(myargs.dprime))
    if bool(request.args.get("useEx") == "True"):
        filename = example_dir + 'prostate_example.txt'
    else:
        filename = os.path.join(app.config['UPLOAD_DIR'], secure_filename(str(request.args.get('filename'))))
    if region == "variant":
        print("Region is variant")
        print("index: " + str(request.args.get('variant[index]')))
        print("base pair window: " + request.args.get('variant[basepair]'))
        print()
        myargs.window = int(request.args.get('variant[basepair]'))
        if request.args.get('variant[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('variant[index]')
    if region == "gene":
        print("Region is gene")
        if request.args.get('gene[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('gene[index]')
        myargs.name = request.args.get('gene[name]')
        myargs.window = int(request.args.get('gene[basepair]'))
    if region == "region":
        print("Region is region")
        if request.args.get('region[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('region[index]')
        myargs.start = str(request.args.get('region[start]'))
        myargs.end = str(request.args.get('region[end]'))
    myargs.transcript = bool(request.args.get("transcript") == "True")
    print("transcript: " + str(myargs.transcript))
    myargs.annotate = bool(request.args.get("annotate") == "True")
    print("annotate: " + str(myargs.annotate))
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print('reference: ' + reference)
        try:
            out_json = calculate_assoc(filename, region, pop, reference, web, myargs)
        except:
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        # PROGRAMMATIC ACCESS NOT AVAILABLE
    return sendJSON(out_json)

# Web and API route for LDhap
@app.route('/LDlinkRest/ldhap', methods=['GET'])
@app.route('/LDlinkRestWeb/ldhap', methods=['GET'])
@requires_token
def ldhap():
    print('Execute ldhap.')
    # print 'Request User Agent: ', request.user_agent
    # print 'Request User Agent Platform: ', request.user_agent.platform
    # print 'Request User Agent Browser: ', request.user_agent.browser

    snps = request.args.get('snps', False)
    pop = request.args.get('pop', False)
    token = request.args.get('token', False)
    print('snps: ' + snps)
    print('pop: ' + pop)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            print('request: ' + str(reference))
            snplst = tmp_dir + 'snps' + reference + '.txt'
            with open(snplst, 'w') as f:
                f.write(snps.lower())
            try:
                out_json = calculate_hap(snplst, pop, reference, web)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        print('request: ' + str(reference))
        snplst = tmp_dir + 'snps' + reference + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_hap(snplst, pop, reference, web)
            # display api out
            try: 
                # unlock token then display api output
                resultFile1 = "./tmp/snps_" + reference + ".txt"
                resultFile2 = "./tmp/haplotypes_" + reference + ".txt"
                with open(resultFile1, "r") as fp:
                    content1 = fp.read()
                with open(resultFile2, "r") as fp:
                    content2 = fp.read()
                toggleLocked(token, 0)
                return content1 + "\n" + "#####################################################################################" + "\n\n" + content2
            except:
                # unlock token then display error message
                output = json.loads(out_json)
                toggleLocked(token, 0)
                return sendTraceback(output["error"])
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return sendJSON(out_json)

# Web and API route for LDmatrix
@app.route('/LDlinkRest/ldmatrix', methods=['GET', 'POST'])
@app.route('/LDlinkRestWeb/ldmatrix', methods=['GET'])
@requires_token
def ldmatrix():
    print('Execute ldmatrix.')
    # differentiate POST or GET request
    if request.method == 'POST':
        # POST REQUEST
        data = json.loads(request.stream.read())
        if 'snps' in data:
            snps = data['snps']
        else:
            snps = False
        if "pop" in data:
            pop = data['pop']
        else:
            pop = False
        if "reference" in data:
            reference = data['reference']
        else:
            reference = False
        if "r2_d" in data:
            r2_d = data['r2_d']
        else:
            r2_d = False
    else:
        # GET REQUEST
        snps = request.args.get('snps', False)
        pop = request.args.get('pop', False)
        reference = request.args.get('reference', False)
        r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    print('snps: ' + snps)
    print('pop: ' + pop)
    print('r2_d: ' + r2_d)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            print('request: ' + str(reference))
            snplst = tmp_dir + 'snps' + str(reference) + '.txt'
            with open(snplst, 'w') as f:
                f.write(snps.lower())
            try:
                out_script, out_div = calculate_matrix(snplst, pop, reference, web, str(request.method), r2_d)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        print('request: ' + str(reference)) 
        snplst = tmp_dir + 'snps' + str(reference) + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_matrix(snplst, pop, reference, web, str(request.method), r2_d)
            # display api out
            try:
                # unlock token then display api output
                resultFile = ""
                if r2_d == "d":
                    resultFile = "./tmp/d_prime_"+reference+".txt"
                else:
                    resultFile = "./tmp/r2_"+reference+".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                return content
            except:
                # unlock token then display error message
                with open(tmp_dir + "matrix" + reference + ".json") as f:
                    json_dict = json.load(f)
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return out_script + "\n " + out_div

# Web and API route for LDpair
@app.route('/LDlinkRest/ldpair', methods=['GET'])
@app.route('/LDlinkRestWeb/ldpair', methods=['GET'])
@requires_token
def ldpair():
    print('Execute ldpair.')
    var1 = request.args.get('var1', False)
    var2 = request.args.get('var2', False)
    pop = request.args.get('pop', False)
    token = request.args.get('token', False)
    print('var1: ' + var1)
    print('var2: ' + var2)
    print('pop: ' + pop)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            print('request: ' + str(reference))
            try:
                out_json = calculate_pair(var1, var2, pop, web, reference)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pair(var1, var2, pop, web, reference)
            # display api out
            try:
                # unlock token then display api output
                with open('./tmp/LDpair_'+reference+'.txt', "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                return content
            except:
                # unlock token then display error message
                output = json.loads(out_json)
                toggleLocked(token, 0)
                return sendTraceback(output["error"])
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for LDpop
@app.route('/LDlinkRest/ldpop', methods=['GET'])
@app.route('/LDlinkRestWeb/ldpop', methods=['GET'])
@requires_token
def ldpop():
    print('Execute ldpop.')
    var1 = request.args.get('var1', False)
    var2 = request.args.get('var2', False)
    pop = request.args.get('pop', False)
    r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    print('var1: ' + var1)
    print('var2: ' + var2)
    print('pop: ' + pop)
    print('r2_d: ' + r2_d)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            print('request: ' + str(reference))
            try:
                out_json = calculate_pop(var1, var2, pop, r2_d, web, reference)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pop(var1, var2, pop, r2_d, web, reference)
            # display api out
            try:
                # unlock token then display api output
                with open('./tmp/LDpop_' + reference + '.txt', "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                return content
            except:
                # unlock token then display error message
                # output = json.loads(out_json)
                toggleLocked(token, 0)
                return sendTraceback(out_json["error"])
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for LDproxy
@app.route('/LDlinkRest/ldproxy', methods=['GET'])
@app.route('/LDlinkRestWeb/ldproxy', methods=['GET'])
@requires_token
def ldproxy():
    print('Execute ldproxy.')
    var = request.args.get('var', False)
    pop = request.args.get('pop', False)
    r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    print('var: ' + var)
    print('pop: ' + pop)
    print('r2_d: ' + r2_d)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = request.args.get('reference', False)
            print('request: ' + str(reference))
            try:
                out_script, out_div = calculate_proxy(var, pop, reference, web, r2_d)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_proxy(var, pop, reference, web, r2_d)
            # display api out
            try:
                # unlock token then display api output
                with open('./tmp/proxy' + reference + '.txt', "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                return content
            except:
                # unlock token then display error message
                with open(tmp_dir + "proxy" + reference + ".json") as f:
                    json_dict = json.load(f)
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return out_script + "\n " + out_div

# Web and API route for LDtrait
@app.route('/LDlinkRest/ldtrait', methods=['POST'])
@app.route('/LDlinkRestWeb/ldtrait', methods=['POST'])
@requires_token
def ldtrait():
    print('Execute ldtrait.')
    data = json.loads(request.stream.read())
    snps = data['snps']
    pop = data['pop']
    r2_d = data['r2_d']
    r2_d_threshold = data['r2_d_threshold']
    token = request.args.get('token', False)
    print('snps: ' + snps)
    print('pop: ' + pop)
    print('r2_d: ' + r2_d)
    print('r2_d_threshold: ' + r2_d_threshold)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(data['reference'])
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
                (query_snps, thinned_snps, details) = calculate_trait(snpfile, pop, reference, web, r2_d, float(r2_d_threshold))
                trait["query_snps"] = query_snps
                trait["thinned_snps"] = thinned_snps
                trait["details"] = details

                with open(tmp_dir + "trait" + reference + ".json") as f:
                    json_dict = json.load(f)
                if "error" in json_dict:
                    trait["error"] = json_dict["error"]
                else:
                    with open('tmp/trait_variants_annotated' + reference + '.txt', 'w') as f:
                        f.write("Query\tGWAS Trait\tRS Number\tPosition (GRCh37)\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n")
                        for snp in thinned_snps:
                            for matched_gwas in details[snp]["aaData"]:
                                f.write(snp + "\t")
                                f.write("\t".join([str(element) for i, element in enumerate(matched_gwas) if i not in {6, 11}]) + "\n")
                        if "warning" in json_dict:
                            trait["warning"] = json_dict["warning"]
                            f.write("Warning(s):\n")
                            f.write(trait["warning"])
                out_json = json.dumps(trait, sort_keys=False)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
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
            (query_snps, thinned_snps, details) = calculate_trait(snpfile, pop, reference, web, r2_d, float(r2_d_threshold))
            with open(tmp_dir + "trait" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            else:
                with open('tmp/trait_variants_annotated' + reference + '.txt', 'w') as f:
                    f.write("Query\tGWAS Trait\tRS Number\tPosition (GRCh37)\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n")
                    for snp in thinned_snps:
                        for matched_gwas in details[snp]["aaData"]:
                            f.write(snp + "\t")
                            f.write("\t".join([str(element) for i, element in enumerate(matched_gwas) if i not in {6, 11}]) + "\n")
                    if "warning" in json_dict:
                        trait["warning"] = json_dict["warning"]
                        f.write("Warning(s):\n")
                        f.write(trait["warning"])
                # display api out
                try:
                    with open('tmp/trait_variants_annotated' + reference + '.txt', 'r') as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    return content
                except:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    return sendTraceback(None)
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return current_app.response_class(out_json, mimetype='application/json')


# Web and API route for SNPchip
@app.route('/LDlinkRest/snpchip', methods=['GET', 'POST'])
@app.route('/LDlinkRestWeb/snpchip', methods=['GET', 'POST'])
@requires_token
def snpchip():
    print("Execute snpchip.")
    data = json.loads(request.stream.read())
    snps = data['snps']
    platforms = data['platforms']
    token = request.args.get('token', False)
    print('snps: ' + snps)
    print('platforms: ' + platforms)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(data['reference'])
            print('request: ' + reference)
            snplst = tmp_dir + 'snps' + reference + '.txt'
            with open(snplst, 'w') as f:
                f.write(snps.lower())
            try:
                snp_chip = calculate_chip(snplst, platforms, web, reference)
                out_json = json.dumps(snp_chip, sort_keys=True, indent=2)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        print('request: ' + reference)
        snplst = tmp_dir + 'snps' + reference + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            snp_chip = calculate_chip(snplst, platforms, web, reference)
            # display api out
            try:
                # unlock token then display api output
                resultFile = "./tmp/details"+reference+".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                return content
            except:
                # unlock token then display error message
                out_json = json.dumps(snp_chip, sort_keys=True, indent=2)
                output = json.loads(out_json)
                toggleLocked(token, 0)
                return sendTraceback(output["error"])
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for SNPclip
@app.route('/LDlinkRest/snpclip', methods=['POST'])
@app.route('/LDlinkRestWeb/snpclip', methods=['POST'])
@requires_token
def snpclip():
    print('Execute snpclip.')
    data = json.loads(request.stream.read())
    snps = data['snps']
    pop = data['pop']
    r2_threshold = data['r2_threshold']
    maf_threshold = data['maf_threshold']
    token = request.args.get('token', False)
    print('snps: ' + snps)
    print('pop: ' + pop)
    print('r2_threshold: ' + r2_threshold)
    print('maf_threshold: ' + maf_threshold)
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            reference = str(data['reference'])
            snpfile = str(tmp_dir + 'snps' + reference + '.txt')
            snplist = snps.splitlines()
            with open(snpfile, 'w') as f:
                for s in snplist:
                    s = s.lstrip()
                    if(s[:2].lower() == 'rs' or s[:3].lower() == 'chr'):
                        f.write(s.lower() + '\n')
            try:
                clip = {}
                (snps, snp_list, details) = calculate_clip(snpfile, pop, reference, web, float(r2_threshold), float(maf_threshold))
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
                with open('tmp/snp_list' + reference + '.txt', 'w') as f:
                    for rs_number in snp_list:
                        f.write(rs_number + '\n')
                with open('tmp/details' + reference + '.txt', 'w') as f:
                    f.write("RS Number\tPosition\tAlleles\tDetails\n")
                    if(type(details) is collections.OrderedDict):
                        for snp in snps:
                            f.write(snp[0] + "\t" + "\t".join(details[snp[0]]))
                            f.write("\n")
                out_json = json.dumps(clip, sort_keys=False)
            except:
                return sendTraceback(None)
        else:
            return sendJSON("This web API route does not support programmatic access. Please use the API routes specified on the API Access web page.")
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
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
            (snps, snp_list, details) = calculate_clip(snpfile, pop, reference, web, float(r2_threshold), float(maf_threshold))
            with open(tmp_dir + "clip" + reference + ".json") as f:
                json_dict = json.load(f)
            with open('tmp/details' + reference + '.txt', 'w') as f:
                f.write("RS Number\tPosition\tAlleles\tDetails\n")
                if(type(details) is collections.OrderedDict):
                    for snp in snps:
                        f.write(snp[0] + "\t" + "\t".join(details[snp[0]]))
                        f.write("\n")
            # display api out
            try:
                # unlock token then display api output
                resultFile = "./tmp/details" + reference + ".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                with open(tmp_dir + "clip" + reference + ".json") as f:
                    json_dict = json.load(f)
                    if "error" in json_dict:
                        toggleLocked(token, 0)
                        return sendTraceback(json_dict["error"])
                toggleLocked(token, 0)
                return content
            except:
                # unlock token then display error message
                toggleLocked(token, 0)
                return sendTraceback(None)
        except:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            return sendTraceback(None)
    return current_app.response_class(out_json, mimetype='application/json')

### Add Request Headers & Initialize Flags ###
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number",
                        default="9982", help="Sets the Port")
    parser.add_argument("-d", dest="debug", default="False",
                        help="Sets the Debugging Option")
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number)
    debugger = args.debug == 'True'
    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, debug=debugger, use_evalex=False)
    application = DebuggedApplication(app, True)
