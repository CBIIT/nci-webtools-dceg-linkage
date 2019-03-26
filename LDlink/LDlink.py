#!flask/bin/python
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
from LDmatrix import calculate_matrix
from LDhap import calculate_hap
from LDassoc import calculate_assoc
from SNPclip import calculate_clip
from SNPchip import calculate_chip, get_platform_request
from RegisterAPI import register_user, checkToken, checkBlocked, checkLocked, toggleLocked, logAccess, emailJustification, blockUser, unblockUser, getToken, getStats, unlockUser, unlockAllUsers
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
    print "Unexpected error:", sys.exc_info()[0]
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
        require_token = bool(config['api']['require_token'])
        url_root = request.url_root
        new_url_root = url_root.replace('http://', 'https://')
        # api_access_dir = config['api']['api_access_dir']
        token_expiration = bool(config['api']['token_expiration'])
        token_expiration_days = config['api']['token_expiration_days']
        if ("LDlinkRestWeb" not in request.full_path):
            # Web server access does not require token
            if require_token:
                # Check if token argument is missing in api call
                if 'token' not in request.args:
                    return sendTraceback('API token missing. Please register using the API Access tab: ' + new_url_root + '?tab=apiaccess')
                token = request.args['token']
                # Check if token is valid
                if checkToken(token, token_expiration, token_expiration_days) is False or token is None:
                    return sendTraceback('Invalid or expired API token. Please register using the API Access tab: ' + new_url_root + '?tab=apiaccess')
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
    print "Execute api blocked user justification submission"
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
    print "Execute api register user"
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
    print "Execute api block user"
    email = request.args.get('email', False)
    out_json = blockUser(email, request.url_root)
    return sendJSON(out_json)

# Web route to unblock user's API token
@app.route('/LDlinkRestWeb/apiaccess/unblock_user', methods=['GET'])
@requires_admin_token
def unblock_user():
    print "Execute api unblock user"
    email = request.args.get('email', False)
    out_json = unblockUser(email)
    return sendJSON(out_json)

# Web route to unlock user's API token
@app.route('/LDlinkRestWeb/apiaccess/unlock_user', methods=['GET'])
@requires_admin_token
def unlock_user():
    print "Execute api unlock user"
    email = request.args.get('email', False)
    out_json = unlockUser(email)
    return sendJSON(out_json)

# Web route to unlock all users API tokens
@app.route('/LDlinkRestWeb/apiaccess/unlock_all_users', methods=['GET'])
@requires_admin_token
def unlock_all_users():
    print "Execute api unlock all users"
    out_json = unlockAllUsers()
    return sendJSON(out_json)

# Web route to retrieve API log stats
@app.route('/LDlinkRestWeb/apiaccess/stats', methods=['GET'])
@requires_admin_token
def api_stats():
    print "Execute api stats"
    startdatetime = request.args.get('startdatetime', False)
    enddatetime = request.args.get('enddatetime', False)
    top = request.args.get('top', False)
    out_json = getStats(startdatetime, enddatetime, top)
    return sendJSON(out_json)

### LDLink Helper Routes ###

# Copy output files from tools' tmp directory to apache tmp directory
@app.route('/')
def copy_output_files(reference):
    # copy_output_files
    apache_root = "/analysistools/"
    # check if URL contains the keyword sandbox
    if 'sandbox' in request.url_root:
        apache_root = "/analysistools-sandbox/"
    apache_tmp_dir = apache_root + "public_html/apps/LDlink/tmp/"
    # Ensure apache tmp directory exists
    if not os.path.exists(apache_tmp_dir):
        os.makedirs(apache_tmp_dir)
    # copy *<reference_no>.* to htodocs
    os.system("cp " + tmp_dir + "*" + reference + ".* " + apache_tmp_dir)

# Ping route for API and Web instances
@app.route('/LDlinkRest/ping/', strict_slashes=False)
@app.route('/ping/', strict_slashes=False)
def ping():
    print "pong"
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
    print "Processing upload"
    print "****** Stage 1: UPLOAD BUTTON ***** "
    print "UPLOAD_DIR = %s" % (app.config['UPLOAD_DIR'])
    for arg in request.args:
        print arg
    print "request.method = %s" % (request.method)
    if request.method == 'POST':
        # check if the post request has the file part
        print " We got a POST"
        # print dir(request.files)
        if 'ldassocFile' not in request.files:
            print('No file part')
            return 'No file part...'
        file = request.files['ldassocFile']
        # if user does not select file, browser also
        # submit a empty part without filename
        print type(file)
        if file.filename == '':
            print('No selected file')
            return 'No selected file'
        if file:
            print 'file.filename ' + file.filename
            print('file and allowed_file')
            filename = secure_filename(file.filename)
            print "About to SAVE file"
            print "filename = " + filename
            file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
            return 'File was saved'

# Route for LDassoc example GWAS data
@app.route('/LDlinkRest/ldassoc_example', methods=['GET'])
@app.route('/LDlinkRestWeb/ldassoc_example', methods=['GET'])
def ldassoc_example():
    example_filepath = '/local/content/analysistools/public_html/apps/LDlink/data/example/prostate_example.txt'
    example = {
        'filename': os.path.basename(example_filepath),
        'headers': read_csv_headers(example_filepath)
    }
    return json.dumps(example)

# Route to retrieve platform data for SNPchip
@app.route('/LDlinkRest/snpchip_platforms', methods=['GET'])
@app.route('/LDlinkRestWeb/snpchip_platforms', methods=['GET'])
def snpchip_platforms():
    print "Retrieve SNPchip Platforms"
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
    myargs = argparse.Namespace()
    myargs.window = None
    print "Execute ldassoc"
    print 'Gathering Variables from url'

    # print type(request.args)
    # for arg in request.args:
    #     print arg

    data = str(request.args)
    json_dumps = json.dumps(data)

    pop = request.args.get('pop', False)

    if request.args.get('reference', False):
        reference = request.args.get('reference', False)
    else:
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`

    filename = secure_filename(request.args.get('filename', False))
    matrixVariable = request.args.get('matrixVariable')
    region = request.args.get('calculateRegion')

    myargs.dprime = bool(request.args.get("dprime") == "True")
    print "dprime: " + str(myargs.dprime)

    # Column settings
    myargs.chr = str(request.args.get('columns[chromosome]'))
    myargs.bp = str(request.args.get('columns[position]'))
    myargs.pval = str(request.args.get('columns[pvalue]'))

    # print "myargs:"
    # print type(myargs.chr)
    # regionValues = json.loads(request.args.get('region'))
    # variantValues = json.loads(request.args.get('variant'))
    # columns = json.loads(request.args.get('columns'))

    if bool(request.args.get("useEx") == "True"):
        filename = '/local/content/analysistools/public_html/apps/LDlink/data/example/prostate_example.txt'
    else:
        filename = os.path.join(app.config['UPLOAD_DIR'], secure_filename(
            str(request.args.get('filename'))))

    print 'filename: ' + filename
    print 'region: ' + region
    print 'pop: ' + pop
    print 'reference: ' + reference
    print 'region: ' + region

    if region == "variant":
        print "Region is variant"
        print "index: " + str(request.args.get('variant[index]'))
        print "base pair window: " + request.args.get('variant[basepair]')
        print
        myargs.window = int(request.args.get('variant[basepair]'))

        if request.args.get('variant[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('variant[index]')

    if region == "gene":
        print "Region is gene"
        if request.args.get('gene[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('gene[index]')

        myargs.name = request.args.get('gene[name]')
        myargs.window = int(request.args.get('gene[basepair]'))

    if region == "region":
        print "Region is region"
        if request.args.get('region[index]') == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get('region[index]')

        myargs.start = str(request.args.get('region[start]'))
        myargs.end = str(request.args.get('region[end]'))

    myargs.transcript = bool(request.args.get("transcript") == "True")
    print "transcript: " + str(myargs.transcript)

    myargs.annotate = bool(request.args.get("annotate") == "True")
    print "annotate: " + str(myargs.annotate)

    try:
        # pass flag to LDassoc to allow svg generation only for web instance
        web = False
        if 'LDlinkRestWeb' in request.path:
            web = True
        else:
            web = False
        out_json = calculate_assoc(
            filename, region, pop, reference, web, myargs)
    except:
        return sendTraceback(None)

    # copy_output_files(reference)
    # print "out_json:"
    # print out_json

    return sendJSON(out_json)

# Web and API route for LDhap
@app.route('/LDlinkRest/ldhap', methods=['GET'])
@app.route('/LDlinkRestWeb/ldhap', methods=['GET'])
@requires_token
def ldhap():
    print 'Execute ldhap.'
    snps = request.args.get('snps', False)
    pop = request.args.get('pop', False)
    token = request.args.get('token', False)
    print 'snps: ' + snps
    print 'pop: ' + pop
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print 'request: ' + str(reference)
        snplst = tmp_dir + 'snps' + reference + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            out_json = calculate_hap(snplst, pop, reference, web)
        except:
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        print 'request: ' + str(reference)
        snplst = tmp_dir + 'snps' + reference + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_hap(snplst, pop, reference, web)
            # retrieve error message from json returned from calculation
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
    print 'Execute ldmatrix.'
    if request.method == 'POST':
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
        snps = request.args.get('snps', False)
        pop = request.args.get('pop', False)
        reference = request.args.get('reference', False)
        r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    print 'snps: ' + snps
    print 'pop: ' + pop
    print 'r2_d: ' + r2_d
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print 'request: ' + str(reference)
        snplst = tmp_dir + 'snps' + str(reference) + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            out_script, out_div = calculate_matrix(snplst, pop, reference, web, r2_d)
        except:
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        print 'request: ' + str(reference)            
        snplst = tmp_dir + 'snps' + str(reference) + '.txt'
        with open(snplst, 'w') as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_matrix(snplst, pop, reference, web, r2_d)
            # retrieve error message from json returned from calculation
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
    print 'Execute ldpair.'
    var1 = request.args.get('var1', False)
    var2 = request.args.get('var2', False)
    pop = request.args.get('pop', False)
    token = request.args.get('token', False)
    print 'var1: ' + var1
    print 'var2: ' + var2
    print 'pop: ' + pop
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print 'request: ' + str(reference)
        try:
            out_json = calculate_pair(var1, var2, pop, web, reference)
        except:
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        print 'request: ' + str(reference)
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pair(var1, var2, pop, web, reference)
            # retrieve error message from json returned from calculation
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
    print 'Execute ldpop.'
    var1 = request.args.get('var1', False)
    var2 = request.args.get('var2', False)
    pop = request.args.get('pop', False)
    r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    print 'var1: ' + var1
    print 'var2: ' + var2
    print 'pop: ' + pop
    print 'r2_d: ' + r2_d
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print 'request: ' + str(reference)
        try:
            out_json = calculate_pop(var1, var2, pop, r2_d, web, reference)
        except:
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        print 'request: ' + str(reference)
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pop(var1, var2, pop, r2_d, web, reference)
            # retrieve error message from json returned from calculation
            try:
                # unlock token then display api output
                toggleLocked(token, 0)
                return sendJSON(out_json)
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

# Web and API route for LDproxy
@app.route('/LDlinkRest/ldproxy', methods=['GET'])
@app.route('/LDlinkRestWeb/ldproxy', methods=['GET'])
@requires_token
def ldproxy():
    print 'Execute ldproxy.'
    var = request.args.get('var', False)
    pop = request.args.get('pop', False)
    r2_d = request.args.get('r2_d', False)
    token = request.args.get('token', False)
    print 'var: ' + var
    print 'pop: ' + pop
    print 'r2_d: ' + r2_d
    web = False
    # differentiate web or api request
    if 'LDlinkRestWeb' in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get('reference', False)
        print 'request: ' + str(reference)
        try:
            out_script, out_div = calculate_proxy(var, pop, reference, web, r2_d)
        except:
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        print 'request: ' + str(reference)
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_proxy(var, pop, reference, web, r2_d)
            # retrieve error message from json returned from calculation
            try:
                # unlock token then display api output
                with open('./tmp/proxy'+reference+'.txt', "r") as fp:
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

# Web and API route for SNPchip
@app.route('/LDlinkRest/snpchip', methods=['GET', 'POST'])
@app.route('/LDlinkRestWeb/snpchip', methods=['GET', 'POST'])
@requires_token
def snpchip():
    web = False
    if 'LDlinkRestWeb' in request.path:
        web = True
    else:
        web = False
    # Command line example
    isProgrammatic = False
    print "Execute snpchip"

    data = json.loads(request.stream.read())
    snps = data['snps']
    platforms = data['platforms']

    # check if call is from API or Web instance by seeing if reference number has already been generated or not
    # if accessed by web instance, generate reference number via javascript after hit calculate button
    if 'reference' in data.keys():
        reference = str(data['reference'])
    else:
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        isProgrammatic = True

    #snps = request.args.get('snps', False)
    #platforms = request.args.get('platforms', False)
    #reference = request.args.get('reference', False)
    print 'snps: ' + snps
    print 'platforms: ' + platforms
    print 'request: ' + reference

    snplst = tmp_dir + 'snps' + reference + '.txt'
    print 'snplst: ' + snplst

    f = open(snplst, 'w')
    f.write(snps.lower())
    f.close()

    try:
        snp_chip = calculate_chip(snplst, platforms, web, reference)
    except:
        return sendTraceback(None)

    chip = {}
    chip["snp_chip"] = snp_chip
    # copy_output_files(reference)
    out_json = json.dumps(snp_chip, sort_keys=True, indent=2)

    if isProgrammatic:
        resultFile = "./tmp/details"+reference+".txt"

        fp = open(resultFile, "r")
        content = fp.read()
        fp.close()

        return content

    return current_app.response_class(out_json, mimetype='application/json')

# Web and API route for SNPclip
@app.route('/LDlinkRest/snpclip', methods=['POST'])
@app.route('/LDlinkRestWeb/snpclip', methods=['POST'])
@requires_token
def snpclip():
    web = False
    if 'LDlinkRestWeb' in request.path:
        web = True
    else:
        web = False
    isProgrammatic = False
    # Command line example
    # [ncianalysis@nciws-d275-v LDlinkc]$ python ./SNPclip.py LDlink-rs-numbers.txt YRI 333
    mimetype = 'application/json'
    data = json.loads(request.stream.read())
    print 'Execute snpclip'
    snps = data['snps']
    pop = data['pop']
    r2_threshold = data['r2_threshold']
    maf_threshold = data['maf_threshold']

    # check if call is from API or Web instance by seeing if reference number has already been generated or not
    # if accessed by web instance, generate reference number via javascript after hit calculate button
    if 'reference' in data.keys():
        reference = str(data['reference'])
    else:
        reference = str(time.strftime("%I%M%S")) + `random.randint(0, 10000)`
        isProgrammatic = True

    snpfile = str(tmp_dir + 'snps' + reference + '.txt')
    snplist = snps.splitlines()

    f = open(snpfile, 'w')
    for s in snplist:
        s = s.lstrip()
        if(s[:2].lower() == 'rs' or s[:3].lower() == 'chr'):
            f.write(s.lower() + '\n')

    f.close()

    clip = {}

    try:
        (snps, snp_list, details) = calculate_clip(snpfile, pop, reference, web, float(r2_threshold), float(maf_threshold))
    except:
        return sendTraceback(None)

    clip["snp_list"] = snp_list
    clip["details"] = details
    clip["snps"] = snps
    clip["filtered"] = collections.OrderedDict()

    # Print output
    with open(tmp_dir + "clip" + reference + ".json") as f:
        json_dict = json.load(f)

    try:
        json_dict["error"]
    except KeyError:
        # print ""
        print "LD Thinned SNP list (" + pop + "):"
        for snp in snp_list:
            print snp

        print "The snps.."
        for snp in snps:
            print snp

        print ""
        print "RS Number\tPosition\tAlleles\tDetails"
        for snp in snps:
            print snp[0] + "\t" + "\t".join(details[snp[0]])
            clip["filtered"][snp[0]] = details[snp[0]]

        try:
            json_dict["warning"]

        except KeyError:
            print ""
        else:
            print ""
            print "WARNING: " + json_dict["warning"] + "!"
            print ""
            clip["warning"] = json_dict["warning"]

    else:
        print ""
        print json_dict["error"]
        print ""
        clip["error"] = json_dict["error"]

    # SNP List file
    f = open('tmp/snp_list' + reference + '.txt', 'w')
    for rs_number in snp_list:
        f.write(rs_number + '\n')

    f.close()

    f = open('tmp/details' + reference + '.txt', 'w')
    f.write("RS Number\tPosition\tAlleles\tDetails\n")
    if(type(details) is collections.OrderedDict):
        for snp in snps:
            f.write(snp[0] + "\t" + "\t".join(details[snp[0]]))
            f.write("\n")

    f.close()
    # copy_output_files(reference)
    out_json = json.dumps(clip, sort_keys=False)
    try:
        if isProgrammatic:
            resultFile = "./tmp/details"+reference+".txt"

            fp = open(resultFile, "r")
            content = fp.read()
            fp.close()

            with open(tmp_dir + "clip" + reference + ".json") as f:
                json_dict = json.load(f)
                if "error" in json_dict:
                    return sendTraceback(json_dict["error"])

            return content
    except:
        return sendTraceback(None)

    return current_app.response_class(out_json, mimetype=mimetype)

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
