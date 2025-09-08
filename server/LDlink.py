#!flask/bin/python3
import os
import traceback
import collections
import argparse
import json
import time
import random
import logging
import sys
from threading import Thread
from pathlib import Path
from functools import wraps
from socket import gethostname
from flask import Flask, request, jsonify, current_app, send_from_directory, send_file
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
from LDscore import calculate_ldscore
from LDutilites import get_config, unlock_stale_tokens
from LDcommon import genome_build_vars, connectMongoDBReadOnly
from SNPclip import calculate_clip
from SNPchip import calculate_chip, get_platform_request
from ApiAccess import (
    register_user,
    checkToken,
    checkApiServer2Auth,
    checkBlocked,
    checkLocked,
    toggleLocked,
    logAccess,
    emailJustification,
    blockUser,
    unblockUser,
    getStats,
    setUserLock,
    setUserApi2Auth,
    unlockAllUsers,
    getLockedUsers,
    getBlockedUsers,
    lookupUser,
)
import requests, glob
from ldscore.ldsc_utils import run_ldsc_command, run_herit_command, run_correlation_command
import zipfile
import shutil
from Cleanup import schedule_tmp_cleanup
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address

# retrieve config
param_list = get_config()
# Ensure tmp directory exists
tmp_dir = param_list["tmp_dir"]


Path(tmp_dir).mkdir(parents=True, exist_ok=True)

### Initialize Flask App ###
is_main = __name__ == "__main__"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 * 1024
app.config["UPLOAD_DIR"] = os.path.join(tmp_dir, "uploads")
app.debug = False

# Log settings
log_level = getattr(logging, param_list["log_level"].upper(), logging.DEBUG)
formatter = logging.Formatter("[%(name)s] [%(asctime)s] [%(levelname)s] - %(message)s", "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler(stream=sys.stderr)
handler.setLevel(log_level)
handler.setFormatter(formatter)

app.logger = logging.getLogger("ldlink")
app.logger.setLevel(log_level)
app.logger.addHandler(handler)
# Prevent propagation to root logger to avoid using root logger
app.logger.propagate = False

# Suppress third-party logs below WARNING
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)


# Flask Limiter initialization
# def get_rate_limit_key():
#     """
#     Key function for rate limiting:
#     - For API routes: use token (if present)
#     - For Web routes: use client IP address
#     """
#     token = request.args.get("token")
#     if token:
#         return f"token:{token}"
#     else:
#         # For web routes without tokens, use IP address
#         # Handle X-Forwarded-For header for load balancer scenarios
#         if request.headers.getlist("X-Forwarded-For"):
#             client_ip = request.headers.getlist("X-Forwarded-For")[0]
#         else:
#             client_ip = request.remote_addr
#         return f"ip:{client_ip}"


# Configure MongoDB storage for distributed rate limiting
# Uses existing MongoDB configuration from param_list
# def create_secure_mongodb_uri():
#     """Create MongoDB URI for rate limiting without exposing credentials in logs."""
#     from urllib.parse import quote_plus

#     mongodb_host = param_list["mongodb_host"]
#     mongodb_port = param_list["mongodb_port"]
#     mongodb_database = param_list["mongodb_database"]
#     mongodb_username = param_list["mongodb_username"]
#     mongodb_password = param_list["mongodb_password"]

#     if mongodb_username and mongodb_password:
#         encoded_username = quote_plus(mongodb_username)
#         encoded_password = quote_plus(mongodb_password)
#         return f"mongodb://{encoded_username}:{encoded_password}@{mongodb_host}:{mongodb_port}/{mongodb_database}"
#     else:
#         return f"mongodb://{mongodb_host}:{mongodb_port}/{mongodb_database}"


# try:
#     mongodb_uri = create_secure_mongodb_uri()
#     limiter = Limiter(app=app, key_func=get_rate_limit_key, storage_uri=mongodb_uri)

#     # Log connection info without credentials
#     mongodb_host = param_list["mongodb_host"]
#     mongodb_port = param_list["mongodb_port"]
#     mongodb_database = param_list["mongodb_database"]
#     app.logger.debug(f"Rate limiting configured with MongoDB: {mongodb_host}:{mongodb_port}/{mongodb_database}")

# except Exception as e:
#     error_msg = str(e)
#     if "mongodb://" in error_msg:
#         error_msg = "MongoDB connection failed"

#     app.logger.warning(f"MongoDB not available for rate limiting ({error_msg}), falling back to memory storage.")
#     limiter = Limiter(app=app, key_func=get_rate_limit_key, storage_uri="memory://")


# Return error (and traceback if specified) from calculations
def sendTraceback(error, showTraceback=False):
    custom = {}
    if error is None or len(error) == 0:
        custom["error"] = "Internal server error. Please contact LDlink admin."
    else:
        custom["error"] = error
    if showTraceback:
        traceback.print_exc()
        custom["traceback"] = traceback.format_exc()
    out_json = json.dumps(custom, sort_keys=False, indent=2)

    # Enhanced error logging with sanitization
    log_error = custom.copy()
    if "traceback" in log_error:
        log_error["traceback"] = "TRACEBACK_AVAILABLE"  # Don't log full traceback in production
    app.logger.error(f"Generated error response: {json.dumps(log_error, indent=2)}")

    return current_app.response_class(out_json, mimetype="application/json")


# Return JSON output from calculations
def sendJSON(inputString):
    out_json = json.dumps(inputString, sort_keys=False)
    return current_app.response_class(out_json, mimetype="application/json")


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
        url_root = param_list["base_url"]
        require_token = bool(param_list["require_token"])
        token_expiration = bool(param_list["token_expiration"])
        token_expiration_days = param_list["token_expiration_days"]
        if "LDlinkRestWeb" not in request.full_path:
            # Web server access does not require token
            if require_token:
                # Check if token argument is missing in api call
                if "token" not in request.args:
                    return sendTraceback(
                        "API token missing. Please register using the API Access tab: " + url_root + "?tab=apiaccess"
                    )
                token = request.args["token"]
                # Check if token is valid
                if checkToken(token, token_expiration, token_expiration_days) is False or token is None:
                    return sendTraceback(
                        "Invalid or expired API token. Please register using the API Access tab: "
                        + url_root
                        + "?tab=apiaccess"
                    )
                # Check if token is blocked
                if checkBlocked(token):
                    return sendTraceback(
                        "Your API token has been blocked. Please contact system administrator: NCILDlinkWebAdmin@mail.nih.gov"
                    )
                # Check if token is locked (exclude check on api server 2)
                if "LDlinkRest" in request.full_path:
                    if checkLocked(token):
                        return sendTraceback(
                            "Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov"
                        )
                # Check if token has been authorized to access api server 2
                # if ("LDlinkRest2" in request.full_path):
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
        # create connection to database, retrieve api_users to find the user with token
        # then check if this user has admin value as 1, if it is admin, then grand acess, if not refuse
        db = connectMongoDBReadOnly(False, True)

        users = db.api_users

        if "token" not in request.args:
            return sendTraceback("Admin API token missing.")
        token = request.args["token"]
        # Check if token is valid and based on the token to find the user, then check if the user is admin or not,
        record = users.find_one({"token": token})

        if record is None:
            return sendTraceback("Invalid admin token.")
        else:
            try:
                admin = record["admin"]
                if admin == 0:
                    return sendTraceback("Not a valid admin user.")
                elif admin == 1:
                    return f(*args, **kwargs)
                else:
                    return sendTraceback("Not a valid admin user.")
            except KeyError:
                return sendTraceback("Invalid admin token.")

    return decorated_function


# Web route to send API token unblock request from front-end
# @app.route('/LDlinkRestWeb/apiaccess/apiblocked_web', methods=['GET'])
# def apiblocked_web():
#     start_time = time.time()
#     firstname = request.args.get('firstname', False)
#     lastname = request.args.get('lastname', False)
#     email = request.args.get('email', False)
#     institution = request.args.get('institution', False)
#     registered = request.args.get('registered', False)
#     blocked = request.args.get('blocked', False)
#     justification = request.args.get('justification', False)
#     app.logger.debug('apiblocked_web params ' + json.dumps({
#         'firstname': firstname,
#         'lastname': lastname,
#         'email': email,
#         'institution': institution,
#         'registered': registered,
#         'blocked': blocked,
#         'justification': justification
#     }, indent=4, sort_keys=True))
#     url_path = request.headers.get('X-Forwarded-Host')
#     if url_path== None:
#         url_path= request.url_root
#     try:
#         out_json = emailJustification(firstname, lastname, email, institution, registered, blocked, justification, url_path)
#     except Exception as e:
#         exc_obj = e
#         app.logger.error(''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
#     end_time = time.time()
#     app.logger.info("Executed unblocked API user justification submission (%ss)" % (round(end_time - start_time, 2)))
#     return sendJSON(out_json)


# Web route to register user's email for API token
@app.route("/LDlinkRestWeb/apiaccess/register_web", methods=["GET"])
def register_web():
    start_time = time.time()
    firstname = request.args.get("firstname", False)
    lastname = request.args.get("lastname", False)
    email = request.args.get("email", False)
    institution = request.args.get("institution", False)
    reference = request.args.get("reference", False)
    url_path = request.headers.get("Referer")
    if url_path == None:
        url_path == request.url_root

    out_json = {}
    # print(request.headers)
    # will return http://nciws-d971-c.nih.gov:8090/
    # print(request.url_root)
    app.logger.debug(
        "register_web params "
        + json.dumps(
            {
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "institution": institution,
                "reference": reference,
                "URL_root": url_path,
            },
            indent=4,
            sort_keys=True,
        )
    )
    try:
        out_json = register_user(firstname, lastname, email, institution, reference, url_path)
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
        out_json = {
            "message": "Error during user registration.",
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "registered": False,
            "blocked": False,
            "institution": institution,
        }
    out_json2 = {
        "message": out_json["message"],
        "email": out_json["email"],
        "firstname": out_json["firstname"],
        "lastname": out_json["lastname"],
        "registered": out_json["registered"],
        "blocked": out_json["blocked"],
        "institution": out_json["institution"],
    }
    end_time = time.time()
    app.logger.info("Executed register API user (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json2)


# Web route to block user's API token
@app.route("/LDlinkRestWeb/apiaccess/block_user", methods=["GET"])
@requires_admin_token
def block_user():
    start_time = time.time()
    email = request.args.get("email", False)
    app.logger.debug("block_user params " + json.dumps({"email": email}, indent=4, sort_keys=True))
    url_path = request.headers.get("X-Forwarded-Host")
    if url_path == None:
        url_path = request.url_root
    try:
        out_json = blockUser(email, url_path)
        if out_json is None:
            out_json = {"message": "User email not found: " + str(email)}
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed block API user (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to unblock user's API token
@app.route("/LDlinkRestWeb/apiaccess/unblock_user", methods=["GET"])
@requires_admin_token
def unblock_user():
    start_time = time.time()
    email = request.args.get("email", False)
    app.logger.debug("unblock_user params " + json.dumps({"email": email}, indent=4, sort_keys=True))
    try:
        out_json = unblockUser(email)
        if out_json is None:
            out_json = {"message": "User email not found: " + str(email)}
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed unblock API user (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to set user's lock status
@app.route("/LDlinkRestWeb/apiaccess/set_user_lock", methods=["GET"])
@requires_admin_token
def set_user_lock():
    start_time = time.time()
    email = request.args.get("email", "Missing Argument")

    try:
        lockValue = int(request.args.get("locked", "Missing Argument"))
        app.logger.debug(
            "set_user_lock params " + json.dumps({"email": email, "lockValue": lockValue}, indent=4, sort_keys=True)
        )
        if lockValue == -1 or lockValue == 0:
            try:
                out_json = setUserLock(email, lockValue)
                if out_json is None:
                    out_json = {"message": "User email not found: " + str(email)}
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
        else:
            out_json = {"message": "Invalid lock value: " + str(lockValue)}
    except:
        out_json = {"message": "Invalid lock value"}
    end_time = time.time()
    app.logger.info("Executed set API user lock status (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to grant/revoke user's API server 2 access
@app.route("/LDlinkRestWeb/apiaccess/set_user_api2auth", methods=["GET"])
@requires_admin_token
def set_user_api2auth():
    start_time = time.time()
    email = request.args.get("email", "Missing Argument")

    try:
        authValue = int(request.args.get("authValue", "Missing Argument"))
        app.logger.debug(
            "set_user_api2auth params " + json.dumps({"email": email, "authValue": authValue}, indent=4, sort_keys=True)
        )
        if authValue == 0 or authValue == 1:
            try:
                out_json = setUserApi2Auth(email, authValue)
                if out_json is None:
                    out_json = {"message": "User email not found: " + str(email)}
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
        else:
            out_json = {"message": "Invalid auth value: " + str(authValue)}
    except:
        out_json = {"message": "Invalid auth value"}
    end_time = time.time()
    app.logger.info("Executed set API user's api server 2 access status (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to unlock all users API tokens
@app.route("/LDlinkRestWeb/apiaccess/unlock_all_users", methods=["GET"])
@requires_admin_token
def unlock_all_users():
    start_time = time.time()
    try:
        out_json = unlockAllUsers()
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed unlock all API users (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to retrieve user record
@app.route("/LDlinkRestWeb/apiaccess/lookup_user", methods=["GET"])
@requires_admin_token
def lookup_user():
    start_time = time.time()
    email = request.args.get("email", False)
    app.logger.debug("lookup_user params " + json.dumps({"email": email}, indent=4, sort_keys=True))
    try:
        out_json = lookupUser(email)
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieving API user record (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to retrieve API log stats
@app.route("/LDlinkRestWeb/apiaccess/stats", methods=["GET"])
@requires_admin_token
def api_stats():
    start_time = time.time()
    startdatetime = request.args.get("startdatetime", False)
    enddatetime = request.args.get("enddatetime", False)
    top = request.args.get("top", False)
    app.logger.debug(
        "api_stats params "
        + json.dumps({"startdatetime": startdatetime, "enddatetime": enddatetime, "top": top}, indent=4, sort_keys=True)
    )
    try:
        out_json = getStats(startdatetime, enddatetime, top)
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieve API stats (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to retrieve all locked API users
@app.route("/LDlinkRestWeb/apiaccess/locked_users", methods=["GET"])
@requires_admin_token
def api_locked_users():
    start_time = time.time()
    try:
        out_json = getLockedUsers()
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieving locked API users stats (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


# Web route to retrieve all blocked API users
@app.route("/LDlinkRestWeb/apiaccess/blocked_users", methods=["GET"])
@requires_admin_token
def api_blocked_users():
    start_time = time.time()
    try:
        out_json = getBlockedUsers()
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.info("Executed retrieving blocked API users stats (%ss)" % (round(end_time - start_time, 2)))
    return sendJSON(out_json)


### LDLink Helper Routes ###


# Copy output files from tools' tmp directory to apache tmp directory
@app.route("/")
def root():
    return app.send_static_file("index.html")
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
@app.route("/LDlinkRest/ping/", strict_slashes=False)
# @app.route('/LDlinkRest2/ping/', strict_slashes=False)
@app.route("/ping/", strict_slashes=False)
def ping():
    try:
        return "true"
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        app.logger.error("".join(traceback.format_exception(None, e, e.__traceback__)))
        return "false", 500


# Route to check file exist status
@app.route("/LDlinkRestWeb/status/<filename>", strict_slashes=False)
@app.route("/status/<filename>", strict_slashes=False)
def status(filename):
    filepath = safe_join(tmp_dir, filename)
    return jsonify(os.path.isfile(filepath))


# Route to serve temporary files
@app.route("/LDlinkRestWeb/tmp/<filename>", strict_slashes=False)
@app.route("/tmp/<filename>", strict_slashes=False)
@app.route("/LDlinkRestWeb/tmp/uploads/<filename>", strict_slashes=False)
@app.route("/tmp/uploads/<filename>", strict_slashes=False)
def send_temp_file(filename):
    if "uploads" in request.path:
        return send_from_directory(os.path.join(tmp_dir, "uploads"), filename)
    else:
        return send_from_directory(tmp_dir, filename)


@app.route("/LDlinkRestWeb/zip", methods=["POST"])
def zip_files():
    start_time = time.time()
    app.logger.info("Starting zip file creation")

    try:
        filenames = request.json.get("files", [])
        app.logger.debug(f"Creating zip with {len(filenames)} files")

        zip_filename = "files.zip"
        zip_filepath = os.path.join(tmp_dir, zip_filename)
        uploads_dir = os.path.join(tmp_dir, "uploads")
        ldscore_dir = os.path.join(param_list["data_dir"], "ldscore")

        os.makedirs(uploads_dir, exist_ok=True)

        # List of known example files
        example_files = [
            "BBJ_LDLC22.txt",
            "BBJ_HDLC22.txt",
            "22.bed",
            "22.bim",
            "22.fam",
        ]

        # For each file, ensure it exists in uploads_dir; if not, copy from ldscore_dir if it's an example file
        for filename in filenames:
            upload_path = os.path.join(uploads_dir, filename)
            if not os.path.exists(upload_path):
                if filename in example_files:
                    source_path = os.path.join(ldscore_dir, filename)
                    if os.path.exists(source_path):
                        shutil.copy(source_path, upload_path)
                        app.logger.info(f"Copied example file {source_path} to {upload_path}")
                    else:
                        app.logger.error(f"Example file {filename} not found in {ldscore_dir}")
                        return jsonify({"error": f"Example file {filename} not found in {ldscore_dir}"}), 404
                else:
                    app.logger.error(f"File {filename} not found in uploads directory and is not an example file.")
                    return (
                        jsonify(
                            {"error": f"File {filename} not found in uploads directory and is not an example file."}
                        ),
                        404,
                    )

        with zipfile.ZipFile(zip_filepath, "w") as zipf:
            for filename in filenames:
                file_path = os.path.join(uploads_dir, filename)
                zipf.write(file_path, os.path.basename(file_path))
                app.logger.debug(f"Added file to zip: {filename}")

        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"Zip file created successfully ({execution_time}s): {zip_filename}")
        return send_file(zip_filepath, as_attachment=True, download_name=zip_filename)
    except Exception as e:
        app.logger.error(f"Zip file creation failed: {str(e)}")
        app.logger.error("".join(traceback.format_exception(None, e, e.__traceback__)))
        return jsonify({"error": str(e)}), 500


# File upload route
@app.route("/LDlinkRest/upload", methods=["POST"])
# @app.route('/LDlinkRest2/upload', methods=['POST'])
@app.route("/LDlinkRestWeb/upload", methods=["POST"])
def upload():
    start_time = time.time()
    app.logger.info("Starting file upload request")

    if request.method == "POST":
        if len(request.files) == 0:
            app.logger.warning("Upload request received with no files")
            return "No file part..."

        reference = request.form.get("reference", None)
        uploaded_files = []

        for file_key in request.files:
            file = request.files[file_key]
            if file.filename == "":
                app.logger.warning("Empty filename provided in upload")
                return "No selected file"

            if file:
                filename = secure_filename(file.filename)
                app.logger.debug(f"Processing upload: {filename}")

                os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
                if reference:
                    ref_dir = os.path.join(app.config["UPLOAD_DIR"], reference)
                    os.makedirs(ref_dir, exist_ok=True)
                    file_path = os.path.join(ref_dir, filename)
                else:
                    file_path = os.path.join(app.config["UPLOAD_DIR"], filename)

                file.save(file_path)
                uploaded_files.append(filename)
                app.logger.info(f"Successfully uploaded file: {filename}")

        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"Upload completed ({execution_time}s) - {len(uploaded_files)} files saved")
        return "All files were saved"


@app.route("/LDlinkRestWeb/copy_and_download/<filename>", methods=["GET"])
def copy_and_download(filename):
    """
    Copies a file from the `data/ldscore/` directory to the `tmp/` directory
    and serves it for download.
    """
    start_time = time.time()
    app.logger.info(f"Starting file copy and download: {filename}")

    try:
        # Define source and destination paths
        source_dir = os.path.join(param_list["data_dir"], "ldscore")
        destination_dir = os.path.join(tmp_dir, "uploads")
        source_file = os.path.join(source_dir, filename)
        destination_file = os.path.join(destination_dir, filename)

        # Ensure the destination directory exists
        os.makedirs(destination_dir, exist_ok=True)

        # Copy the file to the destination directory
        shutil.copy(source_file, destination_file)
        app.logger.info(f"Successfully copied {source_file} to {destination_file}")

        # Serve the file for download
        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"File download completed ({execution_time}s): {filename}")
        return send_from_directory(destination_dir, filename, as_attachment=True)

    except FileNotFoundError:
        app.logger.error(f"File not found: {filename} in {source_dir}")
        return f"File {filename} not found in {source_dir}", 404
    except Exception as e:
        app.logger.error(f"File copy/download failed: {str(e)}")
        return f"An error occurred: {e}", 500


# Route for LDassoc example GWAS data
@app.route("/LDlinkRest/ldassoc_example", methods=["GET"])
# @app.route('/LDlinkRest2/ldassoc_example', methods=['GET'])
@app.route("/LDlinkRestWeb/ldassoc_example", methods=["GET"])
def ldassoc_example():
    genome_build = request.args.get("genome_build", "grch37")
    ldassoc_example_dir = param_list["ldassoc_example_dir"]
    data_dir = param_list["data_dir"]
    example_filepath = data_dir + ldassoc_example_dir + genome_build_vars[genome_build]["ldassoc_example_file"]
    example = {"filename": os.path.basename(example_filepath), "headers": read_csv_headers(example_filepath)}
    return json.dumps(example)


# Route for LDscore example 22
@app.route("/LDlinkRest/ldscore_example", methods=["GET"])
@app.route("/LDlinkRestWeb/ldscore_example", methods=["GET"])
def ldscore_example():
    genome_build = request.args.get("genome_build", "grch37")
    data_dir = param_list["data_dir"]
    ldscore_example_dir = data_dir + "ldscore/"
    # ldscore_example_dir = param_list['ldscore_example_dir']
    example_files = ["22.bed", "22.bim", "22.fam"]
    example_filepaths = [
        ldscore_example_dir + file for file in example_files
    ]  # + genome_build_vars[genome_build]['ldassoc_example_file']
    example = {"filenames": example_files, "filepaths": example_filepaths}
    app.logger.debug(f"LDscore example files: {example}")
    return json.dumps(example)


# Route for LDherit example
@app.route("/LDlinkRest/ldherit_example", methods=["GET"])
@app.route("/LDlinkRestWeb/ldherit_example", methods=["GET"])
def ldherit_example():
    genome_build = request.args.get("genome_build", "grch37")
    data_dir = param_list["data_dir"]
    ldscore_example_dir = data_dir + "ldscore/"
    # ldscore_example_dir = param_list['ldscore_example_dir']
    example_files = "BBJ_HDLC22.txt"
    example_filepaths = ldscore_example_dir + example_files  # + genome_build_vars[genome_build]['ldassoc_example_file']
    example = {"filenames": example_files, "filepaths": example_filepaths}
    app.logger.debug(f"LDherit example files: {example}")
    return json.dumps(example)


# Route for LDherit example
@app.route("/LDlinkRest/ldcorrelation_example", methods=["GET"])
@app.route("/LDlinkRestWeb/ldcorrelation_example", methods=["GET"])
def ldcorrelation_example():
    genome_build = request.args.get("genome_build", "grch37")
    data_dir = param_list["data_dir"]
    ldscore_example_dir = data_dir + "ldscore/"
    # ldscore_example_dir = param_list['ldscore_example_dir']
    example_files = "BBJ_HDLC22.txt"
    example_files2 = "BBJ_LDLC22.txt"
    example_filepaths = ldscore_example_dir + example_files  # + genome_build_vars[genome_build]['ldassoc_example_file']
    example = {
        "filenames": example_files,
        "filenames2": example_files2,
        "filepath": example_filepaths,
        "filepath2": ldscore_example_dir + example_files2,
    }
    app.logger.debug(f"LDcorrelation example files: {example}")
    return json.dumps(example)


# Route to retrieve LDexpress tissue info
@app.route("/LDlinkRest/ldexpress_tissues", methods=["GET"])
# @app.route('/LDlinkRest2/ldexpress_tissues', methods=['GET'])
@app.route("/LDlinkRestWeb/ldexpress_tissues", methods=["GET"])
def ldexpress_tissues():
    start_time = time.time()
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    try:
        results = get_ldexpress_tissues(web)
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.debug("Retrieved LDexpress tissues (%ss)" % (round(end_time - start_time, 2)))
    return results


# Route to retrieve platform data for SNPchip
@app.route("/LDlinkRest/snpchip_platforms", methods=["GET"])
# @app.route('/LDlinkRest2/snpchip_platforms', methods=['GET'])
@app.route("/LDlinkRestWeb/snpchip_platforms", methods=["GET"])
def snpchip_platforms():
    start_time = time.time()
    web = False
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    try:
        results = get_platform_request(web)
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.debug("Retrieved SNPchip Platforms (%ss)" % (round(end_time - start_time, 2)))
    return results


# Route to retrieve timestamp from last LDtrait data update
@app.route("/LDlinkRest/ldtrait_timestamp", methods=["GET"])
# @app.route('/LDlinkRest2/ldtrait_timestamp', methods=['GET'])
@app.route("/LDlinkRestWeb/ldtrait_timestamp", methods=["GET"])
def ldtrait_timestamp():
    start_time = time.time()
    web = False
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        web = True
    else:
        # API REQUEST
        web = False
    try:
        results = get_ldtrait_timestamp(web)
    except Exception as e:
        exc_obj = e
        app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
    end_time = time.time()
    app.logger.debug("Retrieve LDtrait Timestamp (%ss)" % (round(end_time - start_time, 2)))
    return results


### LDLink Main Module Routes ###


# Web and API route for LDassoc
@app.route("/LDlinkRest/ldassoc", methods=["GET"])
# @app.route('/LDlinkRest2/ldassoc', methods=['GET'])
@app.route("/LDlinkRestWeb/ldassoc", methods=["GET"])
def ldassoc():
    start_time = time.time()
    ldassoc_example_dir = param_list["ldassoc_example_dir"]
    data_dir = param_list["data_dir"]
    myargs = argparse.Namespace()
    myargs.window = None
    filename = secure_filename(request.args.get("filename", False))
    region = request.args.get("calculateRegion")
    pop = request.args.get("pop", False)
    genome_build = request.args.get("genome_build", "grch37")
    myargs.dprime = bool(request.args.get("dprime") == "True")
    myargs.chr = str(request.args.get("columns[chromosome]"))
    myargs.bp = str(request.args.get("columns[position]"))
    myargs.pval = str(request.args.get("columns[pvalue]"))
    if bool(request.args.get("useEx") == "True"):
        filename = data_dir + ldassoc_example_dir + genome_build_vars[genome_build]["ldassoc_example_file"]
    else:
        filename = os.path.join(app.config["UPLOAD_DIR"], secure_filename(str(request.args.get("filename"))))
    if region == "variant":
        # print("Region is variant")
        # print("index: " + str(request.args.get('variant[index]')))
        # print("base pair window: " + request.args.get('variant[basepair]'))
        # print()
        myargs.window = int(request.args.get("variant[basepair]"))
        if request.args.get("variant[index]") == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get("variant[index]")
    if region == "gene":
        # print("Region is gene")
        if request.args.get("gene[index]") == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get("gene[index]")
        myargs.name = request.args.get("gene[name]")
        myargs.window = int(request.args.get("gene[basepair]"))
    if region == "region":
        # print("Region is region")
        if request.args.get("region[index]") == "":
            myargs.origin = None
        else:
            myargs.origin = request.args.get("region[index]")
        myargs.start = str(request.args.get("region[start]"))
        myargs.end = str(request.args.get("region[end]"))
    myargs.transcript = bool(request.args.get("transcript") == "True")
    # print("transcript: " + str(myargs.transcript))
    # myargs.annotate = bool(request.args.get("annotate") == "True")
    myargs.annotate = request.args.get("annotate")
    # print("annotate: " + str(myargs.annotate))
    web = False
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        web = True
        reference = request.args.get("reference", False)
        app.logger.debug(f"LDassoc reference: {reference}")
        app.logger.debug(
            "ldassoc params "
            + json.dumps(
                {
                    "filename": filename,
                    "region": region,
                    "pop": pop,
                    "reference": reference,
                    "genome_build": genome_build,
                    "web": web,
                    "myargs": str(myargs),
                },
                indent=4,
                sort_keys=True,
            )
        )
        try:
            out_json = calculate_assoc(filename, region, pop, reference, genome_build, web, myargs)
        except Exception as e:
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        # PROGRAMMATIC ACCESS NOT AVAILABLE
    end_time = time.time()
    app.logger.info("Executed LDassoc (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return sendJSON(out_json)


# Web and API route for LDassoc
@app.route("/LDlinkRest/ldscore", methods=["GET"])
# @app.route('/LDlinkRest2/ldassoc', methods=['GET'])
@app.route("/LDlinkRestWeb/ldscore", methods=["GET"])
def ldscore():
    if "LDlinkRestWeb" in request.path:
        web = True
    else:
        web = False
    app.logger.debug(f"LDscore request with isExample: {request.args.get('isExample')}")
    start_time = time.time()

    pop = request.args.get("pop", False)
    genome_build = request.args.get("genome_build", "grch37")
    filename = request.args.get("filename", False)
    ldwindow = request.args.get("ldwindow", "1")
    windUnit = request.args.get("windUnit", "cm")
    isExample = request.args.get("isExample", False)
    reference = request.args.get("reference", False)
    app.logger.debug(
        f"LDscore params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, ldwindow: {ldwindow}, windUnit: {windUnit}, isExample: {isExample}"
    )

    fileDir = f"/data/tmp/uploads/{reference}/"
    # print(filename)
    if filename and str(isExample).lower() != "true":
        # Split by comma or semicolon (adjust as needed)
        filenames = [secure_filename(f.strip()) for f in filename.replace(";", ",").split(",")]
        for fname in filenames:
            fileroot, ext = os.path.splitext(fname)

            # Find the chromosome number in the filename
            file_parts = fname.split(".")
            file_chromo = None
            for part in file_parts:
                if part.isdigit() and 1 <= int(part) <= 22:
                    file_chromo = part
                    break

            if file_chromo:
                # Find the file in the directory
                pattern = os.path.join("/data/tmp/uploads/", f"*{file_chromo}.*")
                for file_path in glob.glob(pattern):
                    extension = file_path.split(".")[-1]
                    new_filename = f"{file_chromo}.{extension}"
                    new_file_path = os.path.join(fileDir, new_filename)
                    # Create the reference subfolder if it doesn't exist
                    reference_folder = os.path.join(fileDir, str(reference))
                    os.makedirs(reference_folder, exist_ok=True)
                    new_file_path = os.path.join(fileDir, new_filename)
                    if os.path.abspath(file_path) != os.path.abspath(new_file_path):
                        shutil.copyfile(file_path, new_file_path)
                        app.logger.info(f"Copied {file_path} to {new_file_path}")
                    else:
                        app.logger.debug(f"Skipped copying {file_path} to itself.")
                    # os.rename(file_path, new_file_path)
                    # print(f"Copied {file_path} to {new_file_path}")
    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors

        result = run_ldsc_command(pop, genome_build, filename, ldwindow, windUnit, isExample, reference)
        app.logger.debug("LDscore calculation completed, processing result")
        # print(result)
        if web:
            filtered_result = "\n".join(line for line in result.splitlines() if not line.strip().startswith("*"))
            out_json = {"result": filtered_result}
            # Write result to file for frontend to fetch, like ldpop
            if reference:
                result_filename = os.path.join(tmp_dir, f"ldscore_{reference}.txt")
                with open(result_filename, "w") as f:
                    f.write(filtered_result)
        else:
            # Pretty-print the JSON output
            summary_index = result.find("Summary of LD Scores")
            if summary_index != -1:
                filtered_result = result[summary_index:]
            else:
                filtered_result = result
            # filtered_result = filtered_result.replace("\\n", "\n")
            # out_json = {"result": filtered_result}
            # pretty_out_json = json.dumps(out_json, indent=4)
            # print(pretty_out_json)
            return filtered_result
            out_json = pretty_out_json

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDscore request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return jsonify(out_json)


@app.route("/LDlinkRest/ldscoreapi", methods=["POST"])
@requires_token
def ldscoreapi():
    required_files = ["file1", "file2", "file3"]
    fileDir = "/data/tmp/uploads"

    start_time = time.time()

    pop = request.args.get("pop", "eur")
    genome_build = request.args.get("genome_build", "grch37")
    filename = request.args.get("filename", False) + ".bim"
    ldwindow = request.args.get("ldwindow", "1")
    windUnit = request.args.get("windUnit", "cm")
    isExample = request.args.get("isExample", False)

    if filename:
        filename = secure_filename(filename)
        fileroot, ext = os.path.splitext(filename)
    # Check if all required files are present
    for file_key in required_files:
        if file_key not in request.files:
            return jsonify({"error": f"No {file_key} part"}), 400

    # Save the files
    saved_files = {}
    for file_key in required_files:
        file = request.files[file_key]
        if file.filename == "":
            return jsonify({"error": f"No selected file for {file_key}"}), 400

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(fileDir, filename)
            file.save(file_path)
            saved_files[file_key] = file_path

    if filename:
        file_parts = filename.split(".")
        file_chromo = None
        for part in file_parts:
            if part.isdigit() and 1 <= int(part) <= 22:
                file_chromo = part
                break
    app.logger.debug(f"LDscore API file chromosome: {file_chromo}")
    if file_chromo:
        # Find the file in the directory
        pattern = os.path.join(fileDir, f"{fileroot}.*")
        for file_path in glob.glob(pattern):
            extension = file_path.split(".")[-1]
            new_filename = f"{file_chromo}.{extension}"
            new_file_path = os.path.join(fileDir, new_filename)
            os.rename(file_path, new_file_path)
            app.logger.info(f"Renamed {file_path} to {new_file_path}")

    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors

        result = run_ldsc_command(pop, genome_build, filename, ldwindow, windUnit, isExample)
        app.logger.debug("LDscore API calculation completed, processing result")
        # print(result)

        # Pretty-print the JSON output
        summary_index = result.find("Summary of LD Scores")
        if summary_index != -1:
            filtered_result = result[summary_index:]
        else:
            filtered_result = result

        # Delete the uploaded files
        for file_path in saved_files.values():
            try:
                os.remove(file_path)
                app.logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                app.logger.error(f"Error deleting file {file_path}: {e}")

        return filtered_result

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDscore API request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    return jsonify(out_json)


###########
#####
###########
# Web for LDscore
@app.route("/LDlinkRest/ldherit", methods=["GET"])
@app.route("/LDlinkRestWeb/ldherit", methods=["GET"])
def ldherit():
    if "LDlinkRestWeb" in request.path:
        web = True
    else:
        web = False
    app.logger.debug(f"LDherit request with isExample: {request.args.get('isExample')}")
    start_time = time.time()

    pop = request.args.get("pop", False)
    genome_build = request.args.get("genome_build", "grch37")
    filename = request.args.get("filename", False)
    isexample = request.args.get("isExample", False)
    reference = request.args.get("reference", False)
    app.logger.debug(
        f"LDherit params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, isexample: {isexample}"
    )
    if filename:
        filename = secure_filename(filename)
        fileroot, ext = os.path.splitext(filename)

    fileDir = f"/data/tmp/uploads"
    app.logger.debug(f"LDherit processing filename: {filename}")
    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors

        result = run_herit_command(filename, pop, isexample)
        if web:
            filtered_result = "\n".join(line for line in result.splitlines() if not line.strip().startswith("*"))
            out_json = {"result": filtered_result}
            # Write result to file for frontend to fetch, like ldpop
            if reference:
                result_filename = os.path.join(tmp_dir, f"ldherit_{reference}.txt")
                with open(result_filename, "w") as f:
                    f.write(filtered_result)
        else:
            # Pretty-print the JSON output
            summary_index = result.find("Total Observed scale")
            if summary_index != -1:
                filtered_result = result[summary_index:]
            else:
                filtered_result = result
            # filtered_result = filtered_result.replace("\\n", "\n")
            # out_json = {"result": filtered_result}
            # pretty_out_json = json.dumps(out_json, indent=4)
            # print(pretty_out_json)
            return filtered_result
            out_json = pretty_out_json

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDherit request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return jsonify(out_json)


###########
#####
###########
# Web and API route for LDscore
@app.route("/LDlinkRest/ldheritapi", methods=["POST"])
@requires_token
def ldheritAPI():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    fileDir = f"/data/tmp/uploads"
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save the file to a desired location
        file.save(f"{fileDir}/{file.filename}")

    pop = request.args.get("pop", False)
    genome_build = request.args.get("genome_build", "grch37")
    filename = request.args.get("filename", False)
    isexample = request.args.get("isExample", False)

    start_time = time.time()

    app.logger.debug(
        f"LDherit API params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, isexample: {isexample}"
    )
    if filename:
        filename = secure_filename(filename)
        fileroot, ext = os.path.splitext(filename)

    app.logger.debug(f"LDherit API processing filename: {filename}")
    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors

        result = run_herit_command(filename, pop, isexample)

        # Pretty-print the JSON output
        summary_index = result.find("Total Observed scale")
        if summary_index != -1:
            filtered_result = result[summary_index:]
        else:
            filtered_result = result

        # Delete the uploaded files
        for file_path in saved_files.values():
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

        # Delete the uploaded files
        try:
            os.remove(file)
            app.logger.info(f"Deleted file: {file}")
        except Exception as e:
            app.logger.error(f"Error deleting file {file}: {e}")
        return filtered_result

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDherit API request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    return jsonify(out_json)


@app.route("/LDlinkRest/ldcorrelation", methods=["GET"])
@app.route("/LDlinkRestWeb/ldcorrelation", methods=["GET"])
def ldcorrelation():
    if "LDlinkRestWeb" in request.path:
        web = True
    else:
        web = False
    app.logger.debug(f"LDcorrelation request with isExample: {request.args.get('isExample')}")
    start_time = time.time()

    pop = request.args.get("pop", False)
    genome_build = request.args.get("genome_build", "grch37")
    filename = request.args.get("filename", False)
    filename2 = request.args.get("filename2", False)
    isexample = request.args.get("isExample", False)
    reference = request.args.get("reference", False)
    app.logger.debug(
        f"LDcorrelation params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, isexample: {isexample}"
    )
    if filename:
        filename = secure_filename(filename)
        fileroot, ext = os.path.splitext(filename)

    fileDir = f"/data/tmp/uploads"
    app.logger.debug(f"LDcorrelation processing filename: {filename}")
    try:
        # Make an API call to the ldsc39_container
        result = run_correlation_command(filename, filename2, pop, isexample)
        if web:
            filtered_result = "\n".join(line for line in result.splitlines() if not line.strip().startswith("*"))
            out_json = {"result": filtered_result}
            # Write result to file for frontend to fetch, like ldpop
            if reference:
                result_filename = os.path.join(tmp_dir, f"ldcorrelation_{reference}.txt")
                with open(result_filename, "w") as f:
                    f.write(filtered_result)
        else:
            # Pretty-print the JSON output
            summary_index = result.find("Total Observed scale")
            if summary_index != -1:
                filtered_result = result[summary_index:]
            else:
                filtered_result = result
            # filtered_result = filtered_result.replace("\\n", "\n")
            # out_json = {"result": filtered_result}
            # pretty_out_json = json.dumps(out_json, indent=4)
            # print(pretty_out_json)
            return filtered_result
            out_json = pretty_out_json

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDcorrelation request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    return jsonify(out_json)


# Web and API route for LDexpress
@app.route("/LDlinkRest/ldexpress", methods=["POST"])
# @app.route('/LDlinkRest2/ldexpress', methods=['POST'])
@app.route("/LDlinkRestWeb/ldexpress", methods=["POST"])
@requires_token
def ldexpress():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data["snps"]
    pop = data["pop"]
    tissues = data["tissues"]
    r2_d = data["r2_d"]
    r2_d_threshold = data["r2_d_threshold"]
    p_threshold = data["p_threshold"]
    window = data["window"].replace(",", "") if "window" in data else "500000"
    token = request.args.get("token", False)
    genome_build = data["genome_build"] if "genome_build" in data else "grch37"
    web = False
    reference = (
        str(data["reference"]) if "reference" in data else str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
    )
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            # reference = str(data['reference'])
            snplist = "+".join([snp.strip().lower() for snp in snps.splitlines()])
            app.logger.debug(
                "ldexpress params "
                + json.dumps(
                    {
                        "snps": snps,
                        "pop": pop,
                        "tissues": tissues,
                        "r2_d": r2_d,
                        "r2_d_threshold": r2_d_threshold,
                        "window": window,
                        "token": token,
                        "genome_build": genome_build,
                        "web": web,
                        "reference": reference,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            try:
                express = {}
                (query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings) = (
                    calculate_express(
                        snplist,
                        pop,
                        reference,
                        web,
                        tissues,
                        r2_d,
                        genome_build,
                        float(r2_d_threshold),
                        float(p_threshold),
                        int(window),
                    )
                )
                express["query_snps"] = query_snps
                express["thinned_snps"] = thinned_snps
                express["thinned_genes"] = thinned_genes
                express["thinned_tissues"] = thinned_tissues
                express["details"] = details

                if "error" in errors_warnings:
                    express["error"] = errors_warnings["error"]
                else:
                    with open(tmp_dir + "express_variants_annotated" + reference + ".txt", "w") as f:
                        f.write(
                            "Query\tRS ID\tPosition\tR2\tD'\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n"
                        )
                        # for snp in thinned_snps:
                        for matched_gwas in details["results"]["aaData"]:
                            f.write("\t".join(str(element.split("__")[0]) for element in matched_gwas) + "\n")
                        if "warning" in errors_warnings:
                            express["warning"] = errors_warnings["warning"]
                            f.write("Warning(s):\n")
                            f.write(express["warning"])
                out_json = json.dumps(express, sort_keys=False)
                with open(tmp_dir + "ldexpress" + reference + ".json", "w") as f:
                    f.write(out_json)
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        snplist = "+".join([snp.strip().lower() for snp in snps.splitlines()])
        app.logger.debug(
            "ldexpress params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "tissues": tissues,
                    "r2_d": r2_d,
                    "r2_d_threshold": r2_d_threshold,
                    "window": window,
                    "token": token,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            (query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings) = calculate_express(
                snplist,
                pop,
                reference,
                web,
                tissues,
                r2_d,
                genome_build,
                float(r2_d_threshold),
                float(p_threshold),
                int(window),
            )
            # with open(tmp_dir + "express" + reference + ".json") as f:
            #     json_dict = json.load(f)
            if "error" in errors_warnings:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(errors_warnings["error"])
            else:
                with open(tmp_dir + "express_variants_annotated" + reference + ".txt", "w") as f:
                    f.write(
                        "Query\tRS ID\tPosition\tR2\tD'\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n"
                    )
                    # for snp in thinned_snps:
                    for matched_gwas in details["results"]["aaData"]:
                        f.write("\t".join(str(element.split("__")[0]) for element in matched_gwas) + "\n")
                    if "warning" in errors_warnings:
                        # express["warning"] = errors_warnings["warning"]
                        f.write("Warning(s):\n")
                        f.write(errors_warnings["warning"])
                # display api out
                try:
                    with open(tmp_dir + "express_variants_annotated" + reference + ".txt", "r") as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDexpress (%ss)" % (round(end_time - start_time, 2)))
                    return content
                except Exception as e:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    exc_obj = e
                    app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            toggleLocked(token, 0)
            return sendTraceback(None)
        except:
            app.logger.debug("timeout except")
            toggleLocked(token, 0)
            print("timeout error")
        else:
            app.logger.debug("time out else")
            print("time out")
    end_time = time.time()
    app.logger.info("Executed LDexpress (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


    
@app.route("/LDlinkRest/ldexpressget", methods=["GET"])
@app.route("/LDlinkRestWeb/ldexpressget", methods=["GET"])
@requires_token
def ldexpressgwas():
    start_time = time.time()
       # Required parameters
    snps = request.args.get("snps", False)
    pop = request.args.get("pop", False)
    r2_d = request.args.get("r2_d", "r2" )
    r2_d_threshold = request.args.get("r2_d_threshold", 0.1)
    p_threshold = request.args.get("p_threshold", 0.1)
    token = request.args.get("token", False)
    # Optional parameters
    tissues = request.args.get("tissues", "Adipose_Subcutaneous+Adipose_Visceral_Omentum+Adrenal_Gland+Artery_Aorta+Artery_Coronary+Artery_Tibial+Bladder+Brain_Amygdala+Brain_Anterior_cingulate_cortex_BA24+Brain_Caudate_basal_ganglia+Brain_Cerebellar_Hemisphere+Brain_Cerebellum+Brain_Cortex+Brain_Frontal_Cortex_BA9+Brain_Hippocampus+Brain_Hypothalamus+Brain_Nucleus_accumbens_basal_ganglia+Brain_Putamen_basal_ganglia+Brain_Spinal_cord_cervical_c-1+Brain_Substantia_nigra+Breast_Mammary_Tissue+Cells_EBV-transformed_lymphocytes+Cells_Cultured_fibroblasts+Cervix_Ectocervix+Cervix_Endocervix+Colon_Sigmoid+Colon_Transverse+Esophagus_Gastroesophageal_Junction+Esophagus_Mucosa+Esophagus_Muscularis+Fallopian_Tube+Heart_Atrial_Appendage+Heart_Left_Ventricle+Kidney_Cortex+Kidney_Medulla+Liver+Lung+Minor_Salivary_Gland+Muscle_Skeletal+Nerve_Tibial+Ovary+Pancreas+Pituitary+Prostate+Skin_Not_Sun_Exposed_Suprapubic+Skin_Sun_Exposed_Lower_leg+Small_Intestine_Terminal_Ileum+Spleen+Stomach+Testis+Thyroid+Uterus+Vagina+Whole_Blood")
    window = request.args.get("window", "500000")
    genome_build = request.args.get("genome_build", "grch37")
    reference = request.args.get("reference", str(time.strftime("%I%M%S")) + str(random.randint(0, 10000)))
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.user_agent.browser is not None:
            web = True
            # reference = str(data['reference'])
            snplist = "+".join([snp.strip().lower() for snp in snps.splitlines()])
            try:
                express = {}
                (query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings) = (
                    calculate_express(
                        snplist,
                        pop,
                        reference,
                        web,
                        tissues,
                        r2_d,
                        genome_build,
                        float(r2_d_threshold),
                        float(p_threshold),
                        int(window),
                    )
                )
                express["query_snps"] = query_snps
                express["thinned_snps"] = thinned_snps
                express["thinned_genes"] = thinned_genes
                express["thinned_tissues"] = thinned_tissues
                express["details"] = details
                if "error" in errors_warnings:
                    express["error"] = errors_warnings["error"]
                else:
                    with open(tmp_dir + "express_variants_annotated" + reference + ".txt", "w") as f:
                        f.write(
                            "Query\tRS ID\tPosition\tR2\tD'\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n"
                        )
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
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        snplist = "+".join([snp.strip().lower() for snp in snps.splitlines()])
        app.logger.debug(
            "ldexpress params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "tissues": tissues,
                    "r2_d": r2_d,
                    "r2_d_threshold": r2_d_threshold,
                    "window": window,
                    "token": token,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            (query_snps, thinned_snps, thinned_genes, thinned_tissues, details, errors_warnings) = calculate_express(
                snplist,
                pop,
                reference,
                web,
                tissues,
                r2_d,
                genome_build,
                float(r2_d_threshold),
                float(p_threshold),
                int(window),
            )
            # with open(tmp_dir + "express" + reference + ".json") as f:
            #     json_dict = json.load(f)
            if "error" in errors_warnings:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(errors_warnings["error"])
            else:
                with open(tmp_dir + "express_variants_annotated" + reference + ".txt", "w") as f:
                    f.write(
                        "Query\tRS ID\tPosition\tR2\tD'\tGene Symbol\tGencode ID\tTissue\tNon-effect Allele Freq\tEffect Allele Freq\tEffect Size\tP-value\n"
                    )
                    # for snp in thinned_snps:
                    for matched_gwas in details["results"]["aaData"]:
                        f.write("\t".join(str(element.split("__")[0]) for element in matched_gwas) + "\n")
                    if "warning" in errors_warnings:
                        # express["warning"] = errors_warnings["warning"]
                        f.write("Warning(s):\n")
                        f.write(errors_warnings["warning"])
                # display api out
                try:
                    with open(tmp_dir + "express_variants_annotated" + reference + ".txt", "r") as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDexpress (%ss)" % (round(end_time - start_time, 2)))
                    return content
                except Exception as e:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    exc_obj = e
                    app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            toggleLocked(token, 0)
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDexpress (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


# Web and API route for LDhap
@app.route("/LDlinkRest/ldhap", methods=["GET"])
# @app.route('/LDlinkRest2/ldhap', methods=['GET'])
@app.route("/LDlinkRestWeb/ldhap", methods=["GET"])
@requires_token
def ldhap():
    start_time = time.time()
    snps = request.args.get("snps", False)
    pop = request.args.get("pop", False)
    token = request.args.get("token", False)
    genome_build = request.args.get("genome_build", "grch37")
    web = False
    reference = request.args.get("reference", str(time.strftime("%I%M%S")) + str(random.randint(0, 10000)))
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            # print('request: ' + str(reference))
            app.logger.debug(
                "LDhap params "
                + json.dumps(
                    {
                        "snps": snps,
                        "pop": pop,
                        "token": token,
                        "genome_build": genome_build,
                        "reference": reference,
                        "web": web,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            snplst = tmp_dir + "snps" + reference + ".txt"
            with open(snplst, "w") as f:
                f.write(snps.lower())
            try:
                out_json = calculate_hap(snplst, pop, reference, web, genome_build)
                with open(tmp_dir + "ldhap" + reference + ".json", "w") as f:
                    json.dump(json.loads(out_json), f)
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        app.logger.debug(
            "LDhap params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "token": token,
                    "genome_build": genome_build,
                    "reference": reference,
                    "web": web,
                },
                indent=4,
                sort_keys=True,
            )
        )
        snplst = tmp_dir + "snps" + reference + ".txt"
        with open(snplst, "w") as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_hap(snplst, pop, reference, web, genome_build)
            if "error" in json.loads(out_json):
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
                return (
                    content1
                    + "\n"
                    + "#####################################################################################"
                    + "\n\n"
                    + content2
                )
            except Exception as e:
                # unlock token then display error message
                output = json.loads(out_json)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(output["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDhap (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return sendJSON(out_json)


# Web and API route for LDmatrix
@app.route("/LDlinkRest/ldmatrix", methods=["GET", "POST"])
# @app.route('/LDlinkRest2/ldmatrix', methods=['GET', 'POST'])
@app.route("/LDlinkRestWeb/ldmatrix", methods=["GET"])
@requires_token
def ldmatrix():
    start_time = time.time()
    # differentiate POST or GET request
    if request.method == "POST":
        # POST REQUEST
        data = json.loads(request.stream.read())
        snps = data["snps"] if "snps" in data else False
        pop = data["pop"] if "pop" in data else False
        reference = data["reference"] if "reference" in data else False
        r2_d = data["r2_d"] if "r2_d" in data else False
        genome_build = data["genome_build"] if "genome_build" in data else "grch37"
        collapseTranscript = data["collapseTranscript"] if "collapseTranscript" in data else True
    else:
        # GET REQUEST
        snps = request.args.get("snps", False)
        pop = request.args.get("pop", False)
        reference = request.args.get("reference", False)
        r2_d = request.args.get("r2_d", False)
        genome_build = request.args.get("genome_build", "grch37")
        collapseTranscript = request.args.get("collapseTranscript", True)
    token = request.args.get("token", False)
    web = False
    if reference is False:
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            annotate = request.args.get("annotate", True)
            # print('request: ' + str(reference))
            app.logger.debug(
                "ldmatrix params "
                + json.dumps(
                    {
                        "snps": snps,
                        "pop": pop,
                        "r2_d": r2_d,
                        "token": token,
                        "genome_build": genome_build,
                        "collapseTranscript": collapseTranscript,
                        "web": web,
                        "reference": reference,
                        "annotate": annotate,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            snplst = tmp_dir + "snps" + str(reference) + ".txt"
            with open(snplst, "w") as f:
                f.write(snps.lower())
            try:
                out_script, out_div = calculate_matrix(
                    snplst, pop, reference, web, str(request.method), genome_build, r2_d, collapseTranscript, annotate
                )
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        app.logger.debug(
            "ldmatrix params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "r2_d": r2_d,
                    "token": token,
                    "genome_build": genome_build,
                    "collapseTranscript": collapseTranscript,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        # print('request: ' + str(reference))
        snplst = tmp_dir + "snps" + str(reference) + ".txt"
        with open(snplst, "w") as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_matrix(
                snplst, pop, reference, web, str(request.method), genome_build, r2_d, collapseTranscript
            )
            with open(tmp_dir + "matrix" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            # display api out
            try:
                # unlock token then display api output
                resultFile = ""
                if r2_d == "d":
                    resultFile = tmp_dir + "d_prime_" + reference + ".txt"
                else:
                    resultFile = tmp_dir + "r2_" + reference + ".txt"
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
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(json_dict["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDmatrix (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return out_script + "\n " + out_div


# Web and API route for LDpair
@app.route("/LDlinkRest/ldpair", methods=["GET", "POST"])
# @app.route('/LDlinkRest2/ldpair', methods=['GET', 'POST'])
@app.route("/LDlinkRestWeb/ldpair", methods=["GET"])
@requires_token
def ldpair():
    start_time = time.time()
    if request.method == "POST":
        # POST REQUEST
        try:
            data = json.loads(request.stream.read())
        except Exception as e:
            return sendTraceback("Invalid JSON input.")
        snp_pairs = data["snp_pairs"] if "snp_pairs" in data else []
        pop = data["pop"] if "pop" in data else False
        genome_build = data["genome_build"] if "genome_build" in data else "grch37"
        json_out = data["json_out"] if "json_out" in data else False
    else:
        # GET REQUEST
        var1 = request.args.get("var1", "")
        var2 = request.args.get("var2", "")
        snp_pairs = [[var1, var2]]
        pop = request.args.get("pop", False)
        genome_build = request.args.get("genome_build", "grch37")
        json_out = request.args.get("json_out", False)
    if json_out in [False, "false", "False"]:
        json_out = False
    elif json_out in [True, "true", "True"]:
        json_out = True
    else:
        json_out = False
    token = request.args.get("token", False)
    web = False
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            reference = request.args.get("reference", str(time.strftime("%I%M%S")) + str(random.randint(0, 10000)))
            app.logger.debug(
                "ldpair params "
                + json.dumps(
                    {
                        "snp_pairs": snp_pairs,
                        "pop": pop,
                        "token": token,
                        "genome_build": genome_build,
                        "web": web,
                        "reference": reference,
                        "json_out": json_out,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            # print('request: ' + str(reference))
            try:
                out_json = calculate_pair(snp_pairs, pop, web, genome_build, reference)
                with open(tmp_dir + "ldpair" + reference + ".json", "w") as f:
                    json.dump(json.loads(out_json)[0], f)
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug(
            "ldpair params "
            + json.dumps(
                {
                    "snp_pairs": snp_pairs,
                    "pop": pop,
                    "token": token,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                    "json_out": json_out,
                },
                indent=4,
                sort_keys=True,
            )
        )
        # print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pair(snp_pairs, pop, web, genome_build, reference)
            # if there is error, the out_json should be json format not as array
            if "error" in json.loads(out_json):
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
                    return current_app.response_class(out_json, mimetype="application/json")
                else:
                    # right inputs output as text
                    with open(tmp_dir + "LDpair_" + reference + ".txt", "r") as fp:
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
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(output["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDpair (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


# Web and API route for LDpop
@app.route("/LDlinkRest/ldpop", methods=["GET"])
# @app.route('/LDlinkRest2/ldpop', methods=['GET'])
@app.route("/LDlinkRestWeb/ldpop", methods=["GET"])
@requires_token
def ldpop():
    start_time = time.time()
    var1 = request.args.get("var1", False)
    var2 = request.args.get("var2", False)
    pop = request.args.get("pop", False)
    r2_d = request.args.get("r2_d", False)
    token = request.args.get("token", False)
    genome_build = request.args.get("genome_build", "grch37")
    web = False
    reference = request.args.get("reference", str(time.strftime("%I%M%S")) + str(random.randint(0, 10000)))
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            # reference = request.args.get('reference', False)
            app.logger.debug(
                "ldpop params "
                + json.dumps(
                    {
                        "var1": var1,
                        "var2": var2,
                        "pop": pop,
                        "token": token,
                        "genome_build": genome_build,
                        "web": web,
                        "reference": reference,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            # print('request: ' + str(reference))
            try:
                out_json = calculate_pop(var1, var2, pop, r2_d, web, genome_build, reference)
                with open(tmp_dir + "ldpop" + reference + ".json", "w") as f:
                    json.dump(json.loads(out_json), f)
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug(
            "ldpop params "
            + json.dumps(
                {
                    "var1": var1,
                    "var2": var2,
                    "pop": pop,
                    "token": token,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        # print('request: ' + str(reference))
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_json = calculate_pop(var1, var2, pop, r2_d, web, genome_build, reference)
            if "error" in json.loads(out_json):
                toggleLocked(token, 0)
                return sendTraceback(json.loads(out_json)["error"])
            # display api out
            try:
                # unlock token then display api output
                with open(tmp_dir + "LDpop_" + reference + ".txt", "r") as fp:
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
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(out_json["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDpop (%ss)" % (round(end_time - start_time, 2)))
    app.logger.debug(f"LDpop output: {out_json}")
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


# Web and API route for LDproxy
@app.route("/LDlinkRest/ldproxy", methods=["GET"])
# @app.route('/LDlinkRest2/ldproxy', methods=['GET'])
@app.route("/LDlinkRestWeb/ldproxy", methods=["GET"])
@requires_token
# @limiter.limit("10000 per hour")
def ldproxy():
    start_time = time.time()
    var = request.args.get("var", False)
    pop = request.args.get("pop", False)
    r2_d = request.args.get("r2_d", False)
    window = request.args.get("window", "500000").replace(",", "")
    token = request.args.get("token", False)
    genome_build = request.args.get("genome_build", "grch37")
    collapseTranscript = request.args.get("collapseTranscript", True)
    # annotateText = request.args.get('annotate', False)
    web = False
    reference = request.args.get("reference", str(time.strftime("%I%M%S")) + str(random.randint(0, 10000)))
    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            # reference = request.args.get('reference', False)
            annotate = request.args.get("annotate", False)
            # print('request: ' + str(reference))
            app.logger.debug(
                "ldproxy params "
                + json.dumps(
                    {
                        "var": var,
                        "pop": pop,
                        "r2_d": r2_d,
                        "token": token,
                        "window": window,
                        "collapseTranscript": collapseTranscript,
                        "genome_build": genome_build,
                        "web": web,
                        "reference": reference,
                        "annotate": annotate,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            try:
                out_script, out_div = calculate_proxy(
                    var, pop, reference, web, genome_build, r2_d, int(window), collapseTranscript, annotate
                )
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        # print('request: ' + str(reference))
        app.logger.debug(
            "ldproxy params "
            + json.dumps(
                {
                    "var": var,
                    "pop": pop,
                    "r2_d": r2_d,
                    "token": token,
                    "window": window,
                    "collapseTranscript": collapseTranscript,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            out_script, out_div = calculate_proxy(
                var, pop, reference, web, genome_build, r2_d, int(window), collapseTranscript
            )
            with open(tmp_dir + "proxy" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            # display api out
            try:
                # unlock token then display api output
                with open(tmp_dir + "proxy" + reference + ".txt", "r") as fp:
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
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(json_dict["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed LDproxy (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return out_script + "\n " + out_div


# Web and API route for LDtrait
@app.route("/LDlinkRest/ldtrait", methods=["POST"])
# @app.route('/LDlinkRest2/ldtrait', methods=['POST'])
@app.route("/LDlinkRestWeb/ldtrait", methods=["POST"])
@requires_token
def ldtrait():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data["snps"]
    pop = data["pop"]
    r2_d = data["r2_d"]
    r2_d_threshold = data["r2_d_threshold"]
    window = data["window"].replace(",", "") if "window" in data else "500000"
    token = request.args.get("token", False)
    genome_build = data["genome_build"] if "genome_build" in data else "grch37"
    web = False
    # Default continue behavior (proceed). Will be overridden for web requests if provided.
    ifContinue = True
    reference = (
        str(data["reference"]) if "reference" in data else str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
    )

    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            # Gracefully handle optional continue flag (older clients may omit it)
            try:
                ifContinue_raw = data.get("ifContinue", "Continue")
                # Accept boolean, string, or other truthy values; only explicit string "False" means False
                ifContinue = False if str(ifContinue_raw) == "False" else True
            except Exception:
                # Fallback to safe default (proceed) if something unexpected occurs
                ifContinue = True
            # reference = str(data['reference'])
            app.logger.debug(
                "ldtrait params "
                + json.dumps(
                    {
                        "snps": snps,
                        "pop": pop,
                        "r2_d": r2_d,
                        "r2_d_threshold": r2_d_threshold,
                        "token": token,
                        "window": window,
                        "genome_build": genome_build,
                        "web": web,
                        "reference": reference,
                        "continue": ifContinue,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            snpfile = str(tmp_dir + "snps" + reference + ".txt")
            snplist = snps.splitlines()
            with open(snpfile, "w") as f:
                for s in snplist:
                    s = s.lstrip()
                    if s[:2].lower() == "rs" or s[:3].lower() == "chr":
                        f.write(s.lower() + "\n")
            try:
                trait = {}
                # snplst, pop, request, web, r2_d, threshold
                (query_snps, thinned_snps, details) = calculate_trait(
                    snpfile, pop, reference, web, r2_d, genome_build, float(r2_d_threshold), int(window), ifContinue
                )
                trait["query_snps"] = query_snps
                trait["thinned_snps"] = thinned_snps
                trait["details"] = details

                with open(tmp_dir + "trait" + reference + ".json") as f:
                    json_dict = json.load(f)
                if "error" in json_dict:
                    trait["error"] = json_dict["error"]
                else:
                    with open(tmp_dir + "trait_variants_annotated" + reference + ".txt", "w") as f:
                        f.write(
                            "Query\tGWAS Trait\tPMID\tRS Number\tPosition ("
                            + genome_build_vars[genome_build]["title"]
                            + ")\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n"
                        )
                        for snp in thinned_snps:
                            for matched_gwas in details[snp]["aaData"]:
                                f.write(snp + "\t")
                                f.write(
                                    "\t".join(
                                        [str(element) for i, element in enumerate(matched_gwas) if i not in {7, 12}]
                                    )
                                    + "\n"
                                )
                        if "warning" in json_dict:
                            trait["warning"] = json_dict["warning"]
                            f.write("Warning(s):\n")
                            f.write(trait["warning"])
                out_json = json.dumps(trait, sort_keys=False)
                with open(tmp_dir + "ldtrait" + reference + ".json", "w") as f:
                    f.write(out_json)
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug(
            "ldtrait params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "r2_d": r2_d,
                    "r2_d_threshold": r2_d_threshold,
                    "token": token,
                    "window": window,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        snpfile = str(tmp_dir + "snps" + reference + ".txt")
        snplist = snps.splitlines()
        with open(snpfile, "w") as f:
            for s in snplist:
                s = s.lstrip()
                if s[:2].lower() == "rs" or s[:3].lower() == "chr":
                    f.write(s.lower() + "\n")
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            app.logger.debug("begin to call trait")
            try:
                (query_snps, thinned_snps, details) = calculate_trait(
                    snpfile, pop, reference, web, r2_d, genome_build, float(r2_d_threshold), int(window)
                )
            except Exception as e:
                app.logger.debug("after call trait", e)
            except:
                app.logger.debug("timeout error")

            with open(tmp_dir + "trait" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            else:
                with open(tmp_dir + "trait_variants_annotated" + reference + ".txt", "w") as f:
                    f.write(
                        "Query\tGWAS Trait\tPMID\tRS Number\tPosition ("
                        + genome_build_vars[genome_build]["title"]
                        + ")\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n"
                    )
                    for snp in thinned_snps:
                        for matched_gwas in details[snp]["aaData"]:
                            f.write(snp + "\t")
                            f.write(
                                "\t".join([str(element) for i, element in enumerate(matched_gwas) if i not in {7, 12}])
                                + "\n"
                            )
                    if "warning" in json_dict:
                        # trait["warning"] = json_dict["warning"]
                        f.write("Warning(s):\n")
                        f.write(json_dict["warning"])
                # display api out
                try:
                    with open(tmp_dir + "trait_variants_annotated" + reference + ".txt", "r") as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDtrait (%ss)" % (round(end_time - start_time, 2)))
                    return content
                except Exception as e:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    exc_obj = e
                    app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            app.logger.debug("error to call trait", e)
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
        except:
            app.logger.debug("timeout except")
            toggleLocked(token, 0)
            app.logger.error("LDtrait timeout error")
        else:
            app.logger.debug("time out else")
            app.logger.warning("LDtrait timeout occurred")
    end_time = time.time()
    app.logger.info("Executed LDtrait (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")



# Web and API route for LDtrait
@app.route("/LDlinkRest/ldtraitget", methods=["GET"])
# API route for LDtrait GWAS Catalog
@app.route("/LDlinkRestWeb/ldtraitget", methods=["GET"])
@requires_token
def ldtraitgwas():
    start_time = time.time()
    # Required parameters
    snps = request.args.get("snps", False)
    pop = request.args.get("pop", False)
    r2_d = request.args.get("r2_d", "r2" )
    r2_d_threshold = request.args.get("r2_d_threshold", 0.1)
    token = request.args.get("token", False)
    genome_build = request.args.get("genome_build", "grch37")
    # Optional parameters
    window = request.args.get("window", "500000").replace(",", "")
    reference = request.args.get("reference", str(time.strftime("%I%M%S")) + str(random.randint(0, 10000)))
   
    # Run calculate_trait in a separate thread
        # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        if request.user_agent.browser is not None:
                web = True
                snpfile = str(tmp_dir + "snps" + reference + ".txt")
                snplist = snps.splitlines()
                with open(snpfile, "w") as f:
                    for s in snplist:
                        s = s.lstrip()
                        if s[:2].lower() == "rs" or s[:3].lower() == "chr":
                            f.write(s.lower() + "\n")
                try:
                    trait = {}
                    # snplst, pop, request, web, r2_d, threshold
                    print(snpfile, pop, r2_d, r2_d_threshold, reference, genome_build, window)
                    (query_snps, thinned_snps, details) = calculate_trait(
                        snpfile, pop, reference, web, r2_d, genome_build, float(r2_d_threshold), int(window)
                    )
                    trait["query_snps"] = query_snps
                    trait["thinned_snps"] = thinned_snps
                    trait["details"] = details
                    with open(tmp_dir + "trait" + reference + ".json") as f:
                        json_dict = json.load(f)
                    if "error" in json_dict:
                        trait["error"] = json_dict["error"]
                    else:
                        with open(tmp_dir + "trait_variants_annotated" + reference + ".txt", "w") as f:
                            f.write(
                                "Query\tGWAS Trait\tPMID\tRS Number\tPosition ("
                                + genome_build_vars[genome_build]["title"]
                                + ")\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n"
                            )
                            for snp in thinned_snps:
                                for matched_gwas in details[snp]["aaData"]:
                                    f.write(snp + "\t")
                                    f.write(
                                        "\t".join(
                                            [str(element) for i, element in enumerate(matched_gwas) if i not in {7, 12}]
                                        )
                                        + "\n"
                                    )
                            if "warning" in json_dict:
                                trait["warning"] = json_dict["warning"]
                                f.write("Warning(s):\n")
                                f.write(trait["warning"])
                    out_json = json.dumps(trait, sort_keys=False)
                    schedule_tmp_cleanup(reference, app.logger)
                    return current_app.response_class(out_json, mimetype="application/json")
                except Exception as e:
                    exc_obj = e
                    app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        else:
                return sendJSON(
                    "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
                )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug(
            "ldtrait params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "r2_d": r2_d,
                    "r2_d_threshold": r2_d_threshold,
                    "token": token,
                    "window": window,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        snpfile = str(tmp_dir + "snps" + reference + ".txt")
        snplist = snps.splitlines()
        with open(snpfile, "w") as f:
            for s in snplist:
                s = s.lstrip()
                if s[:2].lower() == "rs" or s[:3].lower() == "chr":
                    f.write(s.lower() + "\n")
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            app.logger.debug("begin to call trait")
            print("####################")
            print(snpfile, pop, r2_d, r2_d_threshold, reference, genome_build, window)
            try:
                (query_snps, thinned_snps, details) = calculate_trait(
                    snpfile, pop, reference, web, r2_d, genome_build, float(r2_d_threshold), int(window)
                )
            except Exception as e:
                app.logger.debug("after call trait", e)
            except:
                app.logger.debug("timeout error")
            with open(tmp_dir + "trait" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                # display api out w/ error
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            else:
                with open(tmp_dir + "trait_variants_annotated" + reference + ".txt", "w") as f:
                    f.write(
                        "Query\tGWAS Trait\tPMID\tRS Number\tPosition ("
                        + genome_build_vars[genome_build]["title"]
                        + ")\tAlleles\tR2\tD'\tRisk Allele\tEffect Size (95% CI)\tBeta or OR\tP-value\n"
                    )
                    for snp in thinned_snps:
                        for matched_gwas in details[snp]["aaData"]:
                            f.write(snp + "\t")
                            f.write(
                                "\t".join([str(element) for i, element in enumerate(matched_gwas) if i not in {7, 12}])
                                + "\n"
                            )
                    if "warning" in json_dict:
                        # trait["warning"] = json_dict["warning"]
                        f.write("Warning(s):\n")
                        f.write(json_dict["warning"])
                # display api out
                try:
                    with open(tmp_dir + "trait_variants_annotated" + reference + ".txt", "r") as fp:
                        content = fp.read()
                    toggleLocked(token, 0)
                    end_time = time.time()
                    app.logger.info("Executed LDtrait (%ss)" % (round(end_time - start_time, 2)))
                    return content
                except Exception as e:
                    # unlock token then display error message
                    toggleLocked(token, 0)
                    exc_obj = e
                    app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                    return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            app.logger.debug("error to call trait", e)
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
        except:
            app.logger.debug("timeout except")
            toggleLocked(token, 0)
            print("timeout error")
        else:
            app.logger.debug("time out else")
            print("time out")
    end_time = time.time()
    app.logger.info("Executed LDtrait (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


# Web and API route for SNPchip
@app.route("/LDlinkRest/snpchip", methods=["POST"])
@app.route("/LDlinkRestWeb/snpchip", methods=["POST"])
@requires_token
def snpchip():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data.get("snps")
    genome_build = data.get("genome_build", "grch37")
    platforms = data.get("platforms")
    token = request.args.get("token", False)
    web = False
    reference = (
        str(data["reference"]) if "reference" in data else str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
    )

    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        web = True
        app.logger.debug(
            "snpchip params "
            + json.dumps(
                {
                    "snps": snps,
                    "token": token,
                    "platforms": platforms,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        snplst = tmp_dir + "snps" + reference + ".txt"
        with open(snplst, "w") as f:
            f.write(snps.lower())
        try:
            snp_chip = calculate_chip(snplst, platforms, web, reference, genome_build)
            out_json = json.dumps(snp_chip, sort_keys=True, indent=2)
            with open(tmp_dir + "snpchip" + reference + ".json", "w") as f:
                f.write(out_json)
        except Exception as e:
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    else:
        # API REQUEST
        web = False
        app.logger.debug(
            "snpchip params "
            + json.dumps(
                {
                    "snps": snps,
                    "token": token,
                    "platforms": platforms,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        snplst = tmp_dir + "snps" + reference + ".txt"
        with open(snplst, "w") as f:
            f.write(snps.lower())
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            snp_chip = calculate_chip(snplst, platforms, web, reference, genome_build)
            if "error" in json.loads(snp_chip) and len(json.loads(snp_chip)["error"]) > 0:
                toggleLocked(token, 0)
                return sendTraceback(json.loads(snp_chip)["error"])
            # display api out
            try:
                # unlock token then display api output
                resultFile = tmp_dir + "details" + reference + ".txt"
                with open(resultFile, "r") as fp:
                    content = fp.read()
                toggleLocked(token, 0)
                end_time = time.time()
                app.logger.info("Executed SNPchip (%ss)" % (round(end_time - start_time, 2)))
                return content
            except Exception as e:
                # unlock token then display error message
                out_json = json.dumps(snp_chip, sort_keys=True, indent=2)
                with open(tmp_dir + "snpchip" + reference + ".json", "w") as f:
                    f.write(out_json)
                output = json.loads(out_json)
                toggleLocked(token, 0)
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(output["error"])
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed SNPchip (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


# Web and API route for SNPclip
@app.route("/LDlinkRest/snpclip", methods=["POST"])
@app.route("/LDlinkRestWeb/snpclip", methods=["POST"])
@requires_token
def snpclip():
    start_time = time.time()
    data = json.loads(request.stream.read())
    snps = data["snps"]
    pop = data["pop"]
    r2_threshold = data["r2_threshold"]
    maf_threshold = data["maf_threshold"]
    token = request.args.get("token", False)
    genome_build = data["genome_build"] if "genome_build" in data else "grch37"
    web = False
    reference = (
        str(data["reference"]) if "reference" in data else str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
    )

    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            # reference = str(data['reference'])
            app.logger.debug(
                "snpclip params "
                + json.dumps(
                    {
                        "snps": snps,
                        "pop": pop,
                        "token": token,
                        "r2_threshold": r2_threshold,
                        "maf_threshold": maf_threshold,
                        "genome_build": genome_build,
                        "web": web,
                        "reference": reference,
                    },
                    indent=4,
                    sort_keys=True,
                )
            )
            snpfile = str(tmp_dir + "snps" + reference + ".txt")
            snplist = snps.splitlines()
            with open(snpfile, "w") as f:
                for s in snplist:
                    s = s.lstrip()
                    if s[:2].lower() == "rs" or s[:3].lower() == "chr":
                        f.write(s.lower() + "\n")
            try:
                clip = {}
                (snps, snp_list, details) = calculate_clip(
                    snpfile, pop, reference, web, genome_build, float(r2_threshold), float(maf_threshold)
                )
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
                with open(tmp_dir + "snp_list" + reference + ".txt", "w") as f:
                    for rs_number in snp_list:
                        f.write(rs_number + "\n")
                with open(tmp_dir + "details" + reference + ".txt", "w") as f:
                    f.write("RS Number\tPosition\tAlleles\tDetails\n")
                    if type(details) is collections.OrderedDict:
                        for snp in snps:
                            f.write(snp[0] + "\t" + "\t".join(details[snp[0]]))
                            f.write("\n")
                out_json = json.dumps(clip, sort_keys=False)
                with open(tmp_dir + "snpclip" + reference + ".json", "w") as f:
                    f.write(out_json)
            except Exception as e:
                exc_obj = e
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        else:
            return sendJSON(
                "This web API route does not support programmatic access. Please use the API routes specified on the API Access web page."
            )
    else:
        # API REQUEST
        web = False
        # reference = str(time.strftime("%I%M%S")) + str(random.randint(0, 10000))
        app.logger.debug(
            "snpclip params "
            + json.dumps(
                {
                    "snps": snps,
                    "pop": pop,
                    "token": token,
                    "r2_threshold": r2_threshold,
                    "maf_threshold": maf_threshold,
                    "genome_build": genome_build,
                    "web": web,
                    "reference": reference,
                },
                indent=4,
                sort_keys=True,
            )
        )
        snpfile = str(tmp_dir + "snps" + reference + ".txt")
        snplist = snps.splitlines()
        with open(snpfile, "w") as f:
            for s in snplist:
                s = s.lstrip()
                if s[:2].lower() == "rs" or s[:3].lower() == "chr":
                    f.write(s.lower() + "\n")
        try:
            # lock token preventing concurrent requests
            toggleLocked(token, 1)
            (snps, snp_list, details) = calculate_clip(
                snpfile, pop, reference, web, genome_build, float(r2_threshold), float(maf_threshold)
            )
            with open(tmp_dir + "clip" + reference + ".json") as f:
                json_dict = json.load(f)
            if "error" in json_dict:
                toggleLocked(token, 0)
                return sendTraceback(json_dict["error"])
            with open(tmp_dir + "details" + reference + ".txt", "w") as f:
                f.write("RS Number\tPosition\tAlleles\tDetails\n")
                if type(details) is collections.OrderedDict:
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
                app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
                return sendTraceback(None)
        except Exception as e:
            # unlock token if internal error w/ calculation
            toggleLocked(token, 0)
            exc_obj = e
            app.logger.error("".join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)))
            return sendTraceback(None)
    end_time = time.time()
    app.logger.info("Executed SNPclip (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    return current_app.response_class(out_json, mimetype="application/json")


### Add Request Headers & Initialize Flags ###
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response


def unlock_tokens_background():
    db = connectMongoDBReadOnly()
    while True:
        config = get_config()
        lock_timeout = config["token_lock_timeout"]
        try:
            unlock_stale_tokens(db, lock_timeout)
        except Exception as e:
            app.logger.error(f"Background token unlock failed: {str(e)}")
        time.sleep(lock_timeout / 2)


Thread(name="unlock_tokens_background", target=unlock_tokens_background).start()

if is_main:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number", default="9982", help="Sets the Port")
    parser.add_argument("-d", dest="debug", default="False", help="Sets the Debugging Option")
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number)
    # debugger = args.debug == 'True'
    hostname = gethostname()
    app.logger.info(f"LDlink server starting on {hostname} at port {port_num} with debug={args.debug}")
    app.run(host="0.0.0.0", port=port_num, use_evalex=False)
    # app.logger.disabled = True
    # application = DebuggedApplication(app, True)
    app.debug = False
