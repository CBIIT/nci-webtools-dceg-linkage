#!flask/bin/python3
import os
import re
import traceback
import collections
import argparse
import json
import time
import uuid
import hmac
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
    getTokenRuntimeLast24Hours,
    checkApiServer2Auth,
    checkBlocked,
    checkLocked,
    toggleLocked,
    logAccess,
    emailJustification,
    blockToken,
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
from ldscore.ldsc_utils import run_ldsc_command, run_herit_command, run_correlation_command, validBfile
from sumstats_normalizer import normalize_sumstats_for_ldsc
from ldscore_compatibility import validate_bfile_compatibility, validate_sumstats_preanalysis, write_compatibility_metadata
import zipfile
import shutil
from Cleanup import schedule_tmp_cleanup, schedule_tmp_cleanup_ldscore


WEB_COMPUTE_ENDPOINTS = {
    "ldassoc",
    "ldexpress",
    "ldexpressget",
    "ldhap",
    "ldmatrix",
    "ldpair",
    "ldpop",
    "ldproxy",
    "ldscore",
    "ldherit",
    "ldcorrelation",
    "ldtrait",
    "ldtraitget",
    "snpchip",
    "snpclip"
}

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


def _is_ldlinkrestweb_compute_request(path):
    web_prefix = "/LDlinkRestWeb/"
    if not path.startswith(web_prefix):
        return False

    endpoint = path[len(web_prefix) :].split("/", 1)[0]
    return endpoint in WEB_COMPUTE_ENDPOINTS


@app.before_request
def internal_auth_guard():
    if request.method == "OPTIONS":
        return None

    if not _is_ldlinkrestweb_compute_request(request.path):
        return None

    expected_internal_token = os.environ.get("LDLINK_INTERNAL_AUTH_TOKEN", "").strip()
    provided_internal_token = request.headers.get("X-Internal-Auth", "").strip()
    request_source = request.remote_addr or "unknown"

    if not expected_internal_token:
        app.logger.error(
            f"Internal auth token is not configured; blocking LDlinkRestWeb compute request for {request.path} from {request_source}."
        )
        response = sendJSON({"error": "Internal auth is not configured for LDlinkRestWeb compute routes."})
        response.status_code = 500
        return response

    if not provided_internal_token:
        app.logger.warning(
            f"Missing X-Internal-Auth on LDlinkRestWeb compute request for {request.path} from {request_source}."
        )
        response = sendJSON({"error": "Forbidden: internal authentication header is required."})
        response.status_code = 403
        return response

    if not hmac.compare_digest(provided_internal_token, expected_internal_token):
        app.logger.warning(
            f"Invalid X-Internal-Auth on LDlinkRestWeb compute request for {request.path} from {request_source}."
        )
        response = sendJSON({"error": "Forbidden: internal authentication header is invalid."})
        response.status_code = 403
        return response

    return None


SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9_.:+,= -]{1,512}$")
SAFE_FREE_TEXT_RE = re.compile(r"^[^\x00\r\n]{1,512}$")
SAFE_LIST_RE = re.compile(r"^[A-Za-z0-9_.:+,= -]{1,4096}$")
SAFE_EMAIL_RE = re.compile(r"^[^@\s]{1,128}@[^@\s]{1,128}\.[^@\s]{2,64}$")
SAFE_SNP_RE = re.compile(r"^[A-Za-z0-9_:.+\-\s\r\n,;|]{1,200000}$")
SAFE_SNP_PAIR_RE = re.compile(r"^[A-Za-z0-9_:.+\-\s]{1,128}$")
POP_RE = re.compile(r"^[A-Za-z0-9_+,-]{1,512}$")
LDSC_POP_RE = re.compile(r"^[A-Za-z0-9_+-]{1,64}$")

ANCESTRAL_POP_ENDPOINTS = {
    "ldassoc",
    "ldexpress",
    "ldexpressgwas",
    "ldhap",
    "ldmatrix",
    "ldpair",
    "ldpop",
    "ldproxy",
    "ldtrait",
    "ldtraitgwas",
    "snpclip",
}

LDSC_POP_ENDPOINTS = {
    "ldscore",
    "ldscoreapi",
    "ldherit",
    "ldheritAPI",
    "ldcorrelation",
}

GENOME_BUILD_ENDPOINTS = ANCESTRAL_POP_ENDPOINTS | LDSC_POP_ENDPOINTS | {
    "ldassoc_example",
    "ldscore_example",
    "ldherit_example",
    "ldcorrelation_example",
    "snpchip",
}

R2_D_ENDPOINTS = {
    "ldexpress",
    "ldexpressgwas",
    "ldmatrix",
    "ldpop",
    "ldproxy",
    "ldtrait",
    "ldtraitgwas",
}

WINDOW_ENDPOINTS = {
    "ldexpress",
    "ldexpressgwas",
    "ldproxy",
    "ldtrait",
    "ldtraitgwas",
}

PROBABILITY_ENDPOINT_FIELDS = {
    "ldexpress": {"r2_d_threshold", "p_threshold"},
    "ldexpressgwas": {"r2_d_threshold", "p_threshold"},
    "ldtrait": {"r2_d_threshold"},
    "ldtraitgwas": {"r2_d_threshold"},
    "snpclip": {"r2_threshold", "maf_threshold"},
}

BOOLEAN_ENDPOINT_FIELDS = {
    "ldassoc": {"dprime", "useEx", "transcript"},
    "ldscore": {"isExample"},
    "ldscoreapi": {"isExample"},
    "ldherit": {"isExample"},
    "ldheritAPI": {"isExample"},
    "ldcorrelation": {"isExample"},
    "ldmatrix": {"collapseTranscript"},
    "ldpair": {"json_out"},
}

JSON_SNP_ENDPOINTS = {"ldexpress", "ldmatrix", "ldtrait", "snpchip", "snpclip"}
QUERY_SNP_ENDPOINTS = {"ldhap", "ldmatrix", "ldtraitgwas", "ldexpressgwas"}


def generate_reference():
    return str(uuid.uuid4())


QUERY_REFERENCE_ENDPOINTS = {
    "ldassoc",
    "ldscore",
    "ldherit",
    "ldheritAPI",
    "ldcorrelation",
    "ldproxy",
    "ldmatrix",
    "ldpair",
    "ldpop",
    "ldhap",
    "ldexpressgwas",
    "ldtraitgwas",
    "validate_sumstats",
    "validate_bfile",
}

JSON_REFERENCE_ENDPOINTS = {
    "ldexpress",
    "ldmatrix",
    "ldtrait",
    "snpchip",
    "snpclip",
    "zip_files",
}


def _validation_response(message, status_code=400):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def _validation_error(parameter, reason):
    marker = request.headers.get("X-QA-Marker", "")
    marker_log = f", marker={marker}" if marker else ""
    app.logger.warning(
        f"Rejected structural input: method={request.method}, path={request.path}, endpoint={request.endpoint}, parameter={parameter}, reason={reason}{marker_log}"
    )
    return _validation_response(f"Invalid {parameter} parameter.")


def _is_missing_optional(value):
    return value is None


def _normalize_optional_string(value):
    if _is_missing_optional(value):
        return None
    normalized_value = str(value).strip()
    if not normalized_value:
        return None
    return normalized_value


def _validate_regex_value(parameter, value, pattern, reason):
    normalized_value = _normalize_optional_string(value)
    if normalized_value is None:
        return None
    if not normalized_value or not pattern.fullmatch(normalized_value):
        return _validation_error(parameter, reason)
    return None


def _is_valid_uuid_reference(value):
    normalized_value = str(value).strip()
    try:
        parsed_uuid = uuid.UUID(normalized_value)
    except (TypeError, ValueError, AttributeError):
        return False
    return parsed_uuid.version == 4 and str(parsed_uuid) == normalized_value.lower()


def _validate_reference_value(parameter, value):
    if _is_missing_optional(value):
        return None

    normalized_value = str(value).strip()
    if not normalized_value:
        return _validation_error(parameter, "empty reference")
    if not _is_valid_uuid_reference(normalized_value):
        return _validation_error(parameter, "reference must be a canonical UUIDv4 string")
    return None


def _validate_genome_build_value(value):
    normalized_value = _normalize_optional_string(value)
    if normalized_value is None:
        return None
    if normalized_value not in genome_build_vars["vars"]:
        return _validation_error("genome_build", "unsupported genome build")
    return None


def _validate_choice_value(parameter, value, allowed_values):
    normalized_value = _normalize_optional_string(value)
    if normalized_value is None:
        return None
    if normalized_value not in allowed_values:
        return _validation_error(parameter, "value is not in allowlist")
    return None


def _validate_boolean_value(parameter, value):
    if _is_missing_optional(value):
        return None
    if isinstance(value, bool):
        return None
    normalized_value = str(value).strip().lower()
    if normalized_value not in {"true", "false", "1", "0"}:
        return _validation_error(parameter, "value must be boolean")
    return None


def _validate_number_value(parameter, value, minimum=None, maximum=None, integer=False):
    normalized_value = _normalize_optional_string(value)
    if normalized_value is None:
        return None
    normalized_value = normalized_value.replace(",", "")
    if not normalized_value:
        return _validation_error(parameter, "empty numeric value")
    try:
        parsed_value = int(normalized_value) if integer else float(normalized_value)
    except ValueError:
        return _validation_error(parameter, "value must be numeric")
    if minimum is not None and parsed_value < minimum:
        return _validation_error(parameter, "value is below minimum")
    if maximum is not None and parsed_value > maximum:
        return _validation_error(parameter, "value exceeds maximum")
    return None


def _validate_snps_value(value):
    if _is_missing_optional(value):
        return None
    if not isinstance(value, str):
        return _validation_error("snps", "value must be text")
    if "\x00" in value:
        return _validation_error("snps", "value contains null byte")
    if not value.strip():
        return _validation_error("snps", "empty SNP list")
    if not SAFE_SNP_RE.fullmatch(value):
        return _validation_error("snps", "SNP list contains unsupported characters")
    return None


def _validate_snp_pairs_value(value):
    if _is_missing_optional(value):
        return None
    if not isinstance(value, list):
        return _validation_error("snp_pairs", "value must be an array")
    for pair in value:
        if not isinstance(pair, list) or len(pair) != 2:
            return _validation_error("snp_pairs", "each pair must contain two variants")
        for variant in pair:
            if not isinstance(variant, str) or not SAFE_SNP_PAIR_RE.fullmatch(variant.strip()):
                return _validation_error("snp_pairs", "variant contains unsupported characters")
    return None


def _validate_text_field(parameter, value, pattern=SAFE_TEXT_RE):
    return _validate_regex_value(parameter, value, pattern, "value contains unsupported characters")


def _validate_free_text_field(parameter, value):
    return _validate_regex_value(parameter, value, SAFE_FREE_TEXT_RE, "value contains unsupported characters")


def _request_value(data, parameter):
    if request.method == "POST" and data is not None and parameter in data:
        return data.get(parameter)
    return request.args.get(parameter, None)


def _validate_common_parameters(endpoint):
    data = None
    if request.method == "POST" and request.mimetype == "application/json":
        try:
            data = _get_request_json_body()
        except ValueError:
            return _validation_response("Invalid JSON input.")

    if endpoint in GENOME_BUILD_ENDPOINTS:
        response = _validate_genome_build_value(_request_value(data, "genome_build"))
        if response:
            return response

    if endpoint in ANCESTRAL_POP_ENDPOINTS:
        response = _validate_regex_value("pop", _request_value(data, "pop"), POP_RE, "population contains unsupported characters")
        if response:
            return response

    if endpoint in LDSC_POP_ENDPOINTS:
        response = _validate_regex_value("pop", _request_value(data, "pop"), LDSC_POP_RE, "LDSC population contains unsupported characters")
        if response:
            return response

    if endpoint in R2_D_ENDPOINTS:
        response = _validate_choice_value("r2_d", _request_value(data, "r2_d"), {"r2", "d"})
        if response:
            return response

    if endpoint in WINDOW_ENDPOINTS:
        response = _validate_number_value("window", _request_value(data, "window"), minimum=0, maximum=1000000, integer=True)
        if response:
            return response

    for field in PROBABILITY_ENDPOINT_FIELDS.get(endpoint, set()):
        response = _validate_number_value(field, _request_value(data, field), minimum=0, maximum=1)
        if response:
            return response

    for field in BOOLEAN_ENDPOINT_FIELDS.get(endpoint, set()):
        response = _validate_boolean_value(field, _request_value(data, field))
        if response:
            return response

    if endpoint in JSON_SNP_ENDPOINTS:
        response = _validate_snps_value(_request_value(data, "snps"))
        if response:
            return response

    if endpoint in QUERY_SNP_ENDPOINTS:
        response = _validate_snps_value(request.args.get("snps", None))
        if response:
            return response

    if endpoint == "ldpair" and request.method == "POST":
        response = _validate_snp_pairs_value(_request_value(data, "snp_pairs"))
        if response:
            return response

    if endpoint in {"ldpair", "ldpop"} and request.method == "GET":
        for field in ("var1", "var2"):
            response = _validate_text_field(field, request.args.get(field, None), SAFE_SNP_PAIR_RE)
            if response:
                return response

    if endpoint == "ldproxy":
        response = _validate_text_field("var", request.args.get("var", None), SAFE_SNP_PAIR_RE)
        if response:
            return response

    if endpoint == "ldassoc":
        response = _validate_choice_value("calculateRegion", request.args.get("calculateRegion", None), {"variant", "gene", "region"})
        if response:
            return response
        for field in ("variant[basepair]", "gene[basepair]"):
            response = _validate_number_value(field, request.args.get(field, None), minimum=0, maximum=3000000, integer=True)
            if response:
                return response
        for field in ("variant[index]", "gene[index]", "gene[name]", "region[index]", "columns[chromosome]", "columns[position]", "columns[pvalue]"):
            response = _validate_text_field(field, request.args.get(field, None))
            if response:
                return response
        for field in ("region[start]", "region[end]"):
            response = _validate_text_field(field, request.args.get(field, None), SAFE_SNP_PAIR_RE)
            if response:
                return response

    if endpoint in {"ldscore", "ldscoreapi"}:
        response = _validate_number_value("ldwindow", request.args.get("ldwindow", None), minimum=0)
        if response:
            return response
        response = _validate_choice_value("windUnit", request.args.get("windUnit", None), {"cm", "cM", "kb"})
        if response:
            return response

    if endpoint in {"ldherit", "ldheritAPI", "ldcorrelation"}:
        response = _validate_choice_value("scale", request.args.get("scale", None), {"observed", "liability"})
        if response:
            return response

    if endpoint == "ldexpress" or endpoint == "ldexpressgwas":
        response = _validate_regex_value("tissues", _request_value(data, "tissues"), SAFE_LIST_RE, "tissues contains unsupported characters")
        if response:
            return response

    if endpoint == "snpchip":
        response = _validate_regex_value("platforms", _request_value(data, "platforms"), SAFE_LIST_RE, "platforms contains unsupported characters")
        if response:
            return response

    if endpoint == "ldtrait":
        response = _validate_choice_value("ifContinue", _request_value(data, "ifContinue"), {"Continue", "False", "true", "false", "True"})
        if response:
            return response

    for field in ("firstname", "lastname", "institution"):
        response = _validate_free_text_field(field, request.args.get(field, None))
        if response:
            return response

    for field in ("startdatetime", "enddatetime"):
        response = _validate_text_field(field, request.args.get(field, None))
        if response:
            return response

    for field in ("top", "authValue"):
        response = _validate_number_value(field, request.args.get(field, None), minimum=0, integer=True)
        if response:
            return response

    response = _validate_choice_value("locked", request.args.get("locked", None), {"-1", "0"})
    if response:
        return response

    response = _validate_regex_value("email", request.args.get("email", None), SAFE_EMAIL_RE, "email format is invalid")
    if response:
        return response

    return None


def _validate_filename_value(parameter, value, strict=True):
    if _is_missing_optional(value):
        return None

    filename = str(value).strip()
    if not filename:
        return _validation_error(parameter, "empty filename")
    if len(filename) > 255:
        return _validation_error(parameter, "filename exceeds maximum length")
    if "\x00" in filename or "/" in filename or "\\" in filename or ".." in filename:
        return _validation_error(parameter, "filename contains path traversal characters")

    sanitized_filename = secure_filename(filename)
    if not sanitized_filename:
        return _validation_error(parameter, "filename cannot be normalized")
    if strict and sanitized_filename != filename:
        return _validation_error(parameter, "filename changes during normalization")
    return None


def _validate_filename_list_value(parameter, value):
    if _is_missing_optional(value):
        return None

    filenames = [filename.strip() for filename in str(value).replace(";", ",").split(",")]
    if not filenames or any(not filename for filename in filenames):
        return _validation_error(parameter, "empty filename in list")
    for filename in filenames:
        response = _validate_filename_value(parameter, filename, strict=False)
        if response:
            return response
    return None


def _get_request_json_body():
    raw_body = request.get_data(cache=True)
    if not raw_body:
        return {}
    try:
        data = json.loads(raw_body)
    except (TypeError, ValueError):
        raise ValueError("Invalid JSON input.")
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON input.")
    return data


def _validate_json_reference(endpoint):
    if endpoint not in JSON_REFERENCE_ENDPOINTS:
        return None
    try:
        data = _get_request_json_body()
    except ValueError:
        return _validation_response("Invalid JSON input.")
    return _validate_reference_value("reference", data.get("reference"))


def _validate_zip_files():
    if request.endpoint != "zip_files":
        return None
    try:
        data = _get_request_json_body()
    except ValueError:
        return _validation_response("Invalid JSON input.")
    filenames = data.get("files", [])
    if not isinstance(filenames, list):
        return _validation_error("files", "files must be an array")
    for filename in filenames:
        response = _validate_filename_value("files[]", filename, strict=True)
        if response:
            return response
    return None


@app.before_request
def structural_input_guard():
    endpoint = request.endpoint
    if request.method == "OPTIONS" or endpoint is None:
        return None

    response = _validate_common_parameters(endpoint)
    if response:
        return response

    if endpoint in QUERY_REFERENCE_ENDPOINTS:
        response = _validate_reference_value("reference", request.args.get("reference", None))
        if response:
            return response

    if endpoint == "ldassoc":
        response = _validate_filename_value("filename", request.args.get("filename", None), strict=False)
        if response:
            return response

    if endpoint in {"ldscore", "ldscoreapi", "ldherit", "ldheritAPI", "ldcorrelation", "validate_sumstats", "validate_bfile"}:
        response = _validate_filename_list_value("filename", request.args.get("filename", None))
        if response:
            return response

    if endpoint == "ldcorrelation":
        response = _validate_filename_value("filename2", request.args.get("filename2", None), strict=False)
        if response:
            return response

    if endpoint == "upload":
        response = _validate_reference_value("reference", request.form.get("reference", None))
        if response:
            return response
        for uploaded_file in request.files.values():
            response = _validate_filename_value("filename", uploaded_file.filename, strict=False)
            if response:
                return response

    if endpoint in {"ldscoreapi", "ldheritAPI"}:
        for uploaded_file in request.files.values():
            response = _validate_filename_value("filename", uploaded_file.filename, strict=False)
            if response:
                return response

    if endpoint == "copy_and_download":
        response = _validate_filename_value("filename", (request.view_args or {}).get("filename"), strict=True)
        if response:
            return response

    if endpoint == "send_temp_file":
        response = _validate_filename_value("filename", (request.view_args or {}).get("filename"), strict=True)
        if response:
            return response

    if endpoint == "send_temp_file_reference":
        view_args = request.view_args or {}
        response = _validate_reference_value("reference", view_args.get("reference"))
        if response:
            return response
        response = _validate_filename_value("filename", view_args.get("filename"), strict=True)
        if response:
            return response

    if endpoint == "status":
        response = _validate_filename_value("filename", (request.view_args or {}).get("filename"), strict=True)
        if response:
            return response

    response = _validate_json_reference(endpoint)
    if response:
        return response

    response = _validate_zip_files()
    if response:
        return response

    return None


def _parse_probability_value(raw_value, field_name):
    try:
        parsed_value = float(str(raw_value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}: value must be a number between 0 and 1 (exclusive).")

    if not 0 < parsed_value < 1:
        raise ValueError(f"Invalid {field_name}: value must be between 0 and 1 (exclusive).")

    return format(parsed_value, ".15g")


def _parse_probability_pair(raw_value, field_name):
    parts = [part.strip() for part in str(raw_value).split(",")]
    if len(parts) != 2 or any(part == "" for part in parts):
        raise ValueError(
            f"Invalid {field_name}: for liability scale in LDcorrelation, provide two comma-separated values between 0 and 1."
        )

    normalized_parts = []
    for index, value in enumerate(parts):
        normalized_parts.append(_parse_probability_value(value, f"{field_name}[{index + 1}]"))
    return ",".join(normalized_parts)


def _validate_ldsc_scale_params(scale, samp_prev, pop_prev, require_pair=False):
    normalized_scale = str(scale or "observed").strip().lower()
    if normalized_scale not in {"observed", "liability"}:
        raise ValueError("Invalid scale: allowed values are 'observed' or 'liability'.")

    if normalized_scale != "liability":
        return normalized_scale, "", ""

    normalized_samp_prev = str(samp_prev).strip()
    normalized_pop_prev = str(pop_prev).strip()
    if not normalized_samp_prev or not normalized_pop_prev:
        if require_pair:
            raise ValueError(
                "When scale=liability for LDcorrelation, both samp_prev and pop_prev are required as two comma-separated values between 0 and 1."
            )
        raise ValueError(
            "When scale=liability for LDherit, both samp_prev and pop_prev are required as values between 0 and 1."
        )

    if require_pair:
        normalized_samp_prev = _parse_probability_pair(normalized_samp_prev, "samp_prev")
        normalized_pop_prev = _parse_probability_pair(normalized_pop_prev, "pop_prev")
    else:
        normalized_samp_prev = _parse_probability_value(normalized_samp_prev, "samp_prev")
        normalized_pop_prev = _parse_probability_value(normalized_pop_prev, "pop_prev")

    return normalized_scale, normalized_samp_prev, normalized_pop_prev


LDSCORE_EXAMPLE_DIR = "/data/ldscore"


def _resolve_ldscore_example_path(file_name):
    normalized_name = secure_filename(str(file_name or "").strip())
    if not normalized_name:
        raise ValueError("Invalid example filename.")

    source_path = safe_join(LDSCORE_EXAMPLE_DIR, normalized_name)
    if source_path is None:
        raise ValueError("Invalid example filename.")

    real_source_path = os.path.realpath(source_path)
    real_example_dir = os.path.realpath(LDSCORE_EXAMPLE_DIR)
    if os.path.commonpath([real_example_dir, real_source_path]) != real_example_dir:
        raise ValueError("Invalid example filename.")

    if not os.path.isfile(real_source_path):
        raise FileNotFoundError(f"Example file '{normalized_name}' was not found.")

    return normalized_name, real_source_path


def _resolve_upload_dir(reference, create_dir=False):
    normalized_reference = str(reference or "").strip()
    if not normalized_reference or not _is_valid_uuid_reference(normalized_reference):
        raise ValueError("Missing or invalid reference parameter.")

    upload_root = os.path.realpath(app.config["UPLOAD_DIR"])
    resolved_dir = safe_join(upload_root, normalized_reference)
    if resolved_dir is None:
        raise ValueError("Invalid reference parameter.")

    resolved_dir = os.path.realpath(resolved_dir)
    if os.path.commonpath([upload_root, resolved_dir]) != upload_root:
        raise ValueError("Invalid reference parameter.")

    if create_dir:
        os.makedirs(resolved_dir, exist_ok=True)

    return normalized_reference, resolved_dir


def _resolve_upload_file_path(filename, reference=None, create_dir=False):
    normalized_filename = secure_filename(str(filename or "").strip())
    if not normalized_filename:
        raise ValueError("Invalid filename parameter.")

    upload_root = os.path.realpath(app.config["UPLOAD_DIR"])
    if reference:
        _, resolved_dir = _resolve_upload_dir(reference, create_dir=create_dir)
    else:
        resolved_dir = upload_root
        if create_dir:
            os.makedirs(resolved_dir, exist_ok=True)

    resolved_file_path = safe_join(resolved_dir, normalized_filename)
    if resolved_file_path is None:
        raise ValueError("Invalid filename parameter.")

    resolved_file_path = os.path.realpath(resolved_file_path)
    if os.path.commonpath([upload_root, resolved_file_path]) != upload_root:
        raise ValueError("Invalid filename parameter.")

    return normalized_filename, resolved_file_path, resolved_dir


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
    elif "ldscore" in fullPath:
        return "LDscore"
    elif "ldherit" in fullPath:
        return "LDherit"
    elif "ldcorrelation" in fullPath:
        return "LDcorrelation"
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
                is_blocked, blocked_reason = checkBlocked(token)
                if is_blocked:
                    if blocked_reason == "runtime_limit":
                        return sendTraceback(
                            f"Your API token has been temporarily blocked because runtime usage exceeded the 24-hour limit. "
                            f"The following request was NOT submitted: {request.full_path}. "
                            f"This request and all remaining requests in your queue must be resubmitted after the {param_list['runtime_block_cooldown_minutes']}-minute cooldown period. "
                            f"Your token will be automatically unblocked after {param_list['runtime_block_cooldown_minutes']} minutes. "
                            f"If you believe this is an error, contact: NCILDlinkWebAdmin@mail.nih.gov"
                        )
                    return sendTraceback(
                        "Your API token has been blocked. Please contact system administrator: NCILDlinkWebAdmin@mail.nih.gov"
                    )
                # Check if user has API server 2 authorization (concurrent + no runtime limit)
                user_api2auth = checkApiServer2Auth(token)
                # Check if token is locked (exclude check on api server 2)
                if "LDlinkRest" in request.full_path and not user_api2auth:
                    if checkLocked(token):
                        return sendTraceback(
                            "Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov"
                        )
                if not param_list.get("disable_control", False) and not user_api2auth:
                    total_runtime_ms_24h = getTokenRuntimeLast24Hours(token)
                    request.environ["token_runtime_ms_24h"] = total_runtime_ms_24h
                    runtime_limit_ms_24h = param_list["runtime_limit_ms_24h"]
                    #app.logger.info(
                    #    "Runtime budget check: total_runtime_ms_24h=%d limit_ms_24h=%d comparison_result=%s",
                    #    total_runtime_ms_24h,
                    #    runtime_limit_ms_24h,
                    #    "OVER_LIMIT" if total_runtime_ms_24h > runtime_limit_ms_24h else "UNDER_LIMIT",
                    # )

                    if total_runtime_ms_24h > runtime_limit_ms_24h:
                        app.logger.warning(
                            "BLOCKING TOKEN: total_runtime_ms_24h=%d exceeded limit=%d module=%s",
                            total_runtime_ms_24h,
                            runtime_limit_ms_24h,
                            getModule(request.full_path),
                        )
                        blockToken(token, url_root)
                        return sendTraceback(
                            f"Your API token has been temporarily blocked because runtime usage exceeded the 24-hour limit. "
                            f"The following request was NOT submitted: {request.full_path}. "
                            f"This request and all remaining requests in your queue must be resubmitted after the {param_list['runtime_block_cooldown_minutes']}-minute cooldown period. "
                            f"Your token will be automatically unblocked after {param_list['runtime_block_cooldown_minutes']} minutes. "
                            f"If you believe this is an error, contact: NCILDlinkWebAdmin@mail.nih.gov"
                        )
                # Check if token has been authorized to access api server 2
                # if ("LDlinkRest2" in request.full_path):
                #    if not checkApiServer2Auth(token):
                #        return sendTraceback("Your token is not authorized to access this API endpoint. Please contact system administrator: NCILDlinkWebAdmin@mail.nih.gov")
                module = getModule(request.full_path)
                if not param_list.get("disable_control", False) and not user_api2auth:
                    app.logger.info(
                        "Token runtime 24h check for %s: %.2f minutes",
                        module,
                        total_runtime_ms_24h / 60000.0,
                    )
                request_started_at = time.time()
                skip_runtime = param_list.get("disable_control", False) or user_api2auth
                try:
                    return f(*args, **kwargs)
                finally:
                    duration_ms = round((time.time() - request_started_at) * 1000)
                    try:
                        logAccess(token, module, duration_ms, skip_runtime_cache=skip_runtime)
                    except Exception:
                        app.logger.exception("Failed to log API access")
            else:
                token = "NA"
                module = getModule(request.full_path)
                request_started_at = time.time()
                try:
                    return f(*args, **kwargs)
                finally:
                    duration_ms = round((time.time() - request_started_at) * 1000)
                    try:
                        logAccess(token, module, duration_ms)
                    except Exception:
                        app.logger.exception("Failed to log API access")
        else:
            token = "NA"
            module = getModule(request.full_path)
            request_started_at = time.time()
            try:
                return f(*args, **kwargs)
            finally:
                duration_ms = round((time.time() - request_started_at) * 1000)
                try:
                    logAccess(token, module, duration_ms)
                except Exception:
                    app.logger.exception("Failed to log API access")
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


@app.route("/LDlinkRestWeb/tmp/uploads/<reference>/<filename>", strict_slashes=False)
@app.route("/tmp/uploads/<reference>/<filename>", strict_slashes=False)
def send_temp_file_reference(reference, filename):
    return send_from_directory(os.path.join(tmp_dir, "uploads", reference), filename)


@app.route("/LDlinkRestWeb/zip", methods=["POST"])
def zip_files():
    start_time = time.time()
    app.logger.info("Starting zip file creation")

    try:
        data = _get_request_json_body()
        filenames = data.get("files", [])
        reference = data.get("reference", None)
        app.logger.debug(f"Creating zip with {len(filenames)} files, reference: {reference}")

        zip_filename = "files.zip"
        ldscore_dir = os.path.join(param_list["data_dir"], "ldscore")

        # If reference is provided, use reference subfolder for both input files and zip
        if reference:
            reference, uploads_dir = _resolve_upload_dir(reference, create_dir=True)
            zip_filepath = safe_join(uploads_dir, zip_filename)
        else:
            uploads_dir = os.path.join(tmp_dir, "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            zip_filepath = os.path.join(tmp_dir, zip_filename)

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
            safe_filename, upload_path, _ = _resolve_upload_file_path(filename, reference)
            if not os.path.exists(upload_path):
                if safe_filename in example_files:
                    source_path = os.path.join(ldscore_dir, safe_filename)
                    if os.path.exists(source_path):
                        # shutil.copy(source_path, upload_path)
                        app.logger.info(f"Copied example file {source_path} to {upload_path}")
                    else:
                        app.logger.error(f"Example file {safe_filename} not found in {ldscore_dir}")
                        return jsonify({"error": f"Example file {safe_filename} not found in {ldscore_dir}"}), 404
                else:
                    app.logger.error(f"File {safe_filename} not found in uploads directory and is not an example file.")
                    return (
                        jsonify(
                            {"error": f"File {safe_filename} not found in uploads directory and is not an example file."}
                        ),
                        404,
                    )

        with zipfile.ZipFile(zip_filepath, "w") as zipf:
            for filename in filenames:
                safe_filename, file_path, _ = _resolve_upload_file_path(filename, reference)
                zipf.write(file_path, os.path.basename(file_path))
                app.logger.debug(f"Added file to zip: {safe_filename}")

        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"Zip file created successfully ({execution_time}s): {zip_filename} in {uploads_dir}")
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
        upload_metadata = {
            "analysis_type": request.form.get("analysis_type", ""),
            "analysis_run_id": request.form.get("analysis_run_id", reference or ""),
            "session_id": request.form.get("session_id", reference or ""),
            "project_id": request.form.get("project_id", ""),
            "user_id": request.form.get("user_id", ""),
            "summary_stats_format": request.form.get("summary_stats_format", ""),
            "trait": request.form.get("trait", ""),
        }
        uploaded_files = []
        renamed_notifications = []
        app.logger.debug(f"Upload reference: {reference}")
        for file_key in request.files:
            file = request.files[file_key]
            if file.filename == "":
                app.logger.warning("Empty filename provided in upload")
                return jsonify({"message": "No selected file"}), 400
    
            if file:
                original_filename = file.filename
                filename = secure_filename(original_filename)
                # If secure_filename changed the name, record a notification for the user
                if filename != original_filename:
                    renamed_notifications.append({"original": original_filename, "sanitized": filename})

                app.logger.debug(f"Processing upload: {filename}")

                if reference:
                    _, file_path, _ = _resolve_upload_file_path(filename, reference, create_dir=True)
                else:
                    _, file_path, _ = _resolve_upload_file_path(filename, create_dir=True)

                file.save(file_path)
                uploaded_files.append(filename)
                app.logger.info(f"Successfully uploaded file: {filename}")

        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"Upload completed ({execution_time}s) - {len(uploaded_files)} files saved")

        if reference:
            schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])

        metadata = {key: value for key, value in upload_metadata.items() if value}
        if metadata:
            if reference:
                try:
                    _, uploads_dir = _resolve_upload_dir(reference, create_dir=True)
                    metadata_path = safe_join(uploads_dir, "upload_metadata.json")
                    metadata_record = {
                        "reference": reference,
                        "uploaded_files": uploaded_files,
                        "metadata": metadata,
                    }
                    with open(metadata_path, "w") as metadata_file:
                        json.dump(metadata_record, metadata_file, sort_keys=True, indent=2)
                except (OSError, ValueError) as metadata_error:
                    app.logger.error(f"Failed to write upload metadata for reference {reference}: {metadata_error}")
                    return jsonify({"message": "Files were uploaded, but metadata could not be saved."}), 500

            response = {
                "message": "All files were saved",
                "uploaded_files": uploaded_files,
                "metadata": metadata,
                "reference": reference,
            }
            if renamed_notifications:
                response["renamed"] = renamed_notifications
            return jsonify(response)

        # Return JSON with uploaded filenames and any sanitization notes
        # Only include the `renamed` field when there were actual sanitizations.
        if renamed_notifications:
            response = {
                "message": "All files were saved",
                "uploaded_files": uploaded_files,
                "renamed": renamed_notifications,
            }
            return jsonify(response)
        else:
            # Preserve previous simple-text behavior when nothing was renamed
            return "All files were saved"


@app.route("/LDlinkRestWeb/validate_sumstats", methods=["GET"])
def validate_sumstats():
    """
    Validates a sumstats file for heritability/correlation analysis.
    Expects 'filename' and 'reference' as query parameters.
    Returns JSON with normalized filename and validation details.
    """
    start_time = time.time()
    app.logger.info("Starting sumstats validation request")
    
    filename = request.args.get("filename", None)
    reference = request.args.get("reference", None)
    selected_format = request.args.get("summary_stats_format", None)
    trait = request.args.get("trait", "")
    
    if not filename:
        app.logger.warning("Validation request missing filename")
        return jsonify({"fileValid": {"valid": False, "errors": ["Missing filename parameter"], "warnings": []}})
    
    try:
        filename, file_path, upload_dir = _resolve_upload_file_path(filename, reference)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid sumstats validation input: {validation_error}")
        return jsonify({"fileValid": {"valid": False, "errors": [str(validation_error)], "warnings": []}})
    
    app.logger.debug(f"Validating sumstats file: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        app.logger.warning(f"File not found for validation: {file_path}")
        return jsonify({"fileValid": {"valid": False, "errors": ["File not found"], "warnings": []}})
    
    try:
        file_valid = normalize_sumstats_for_ldsc(file_path, upload_dir, selected_format=selected_format)
        validation_record = {
            "analysis_run_id": reference,
            "source_file": filename,
            "trait": trait,
            "selected_format": selected_format,
            "detected_format": file_valid.get("detected_format"),
            "pipeline_version": file_valid.get("pipeline_version"),
            "status": "validated" if file_valid.get("valid") else "failed",
            "output_location": file_valid.get("normalized_filename") if file_valid.get("valid") else "",
            "validated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "validation_result": file_valid,
        }
        if reference:
            validation_metadata_path = safe_join(upload_dir, "sumstats_validation_metadata.json")
            existing_records = []
            if os.path.exists(validation_metadata_path):
                try:
                    with open(validation_metadata_path) as existing_metadata_file:
                        existing_metadata = json.load(existing_metadata_file)
                    existing_records = existing_metadata.get("validations", [])
                except (OSError, json.JSONDecodeError):
                    existing_records = []
            existing_records = [
                record for record in existing_records
                if not (record.get("source_file") == filename and record.get("trait", "") == trait)
            ]
            existing_records.append(validation_record)
            with open(validation_metadata_path, "w") as metadata_file:
                json.dump({"analysis_run_id": reference, "validations": existing_records}, metadata_file, sort_keys=True, indent=2)
        app.logger.info(f"Sumstats validation metadata for analysis run {reference}: {validation_record}")

        # Keep this disabled for now: running LDSC's validator before/inside upload validation
        # can reject raw PLINK/REGENIE/SAIGE files before users submit the normalized file.
        # If we need stricter checks later, run them against file_valid["normalizedFilename"].
        # if file_valid.get("valid") and file_valid.get("detected_format") == "LDSC-ready":
        #     from ldscore.ldsc_utils import validSumstats
        #     ldsc_valid = validSumstats(file_path)
        #     if isinstance(ldsc_valid, dict):
        #         file_valid["valid"] = bool(ldsc_valid.get("valid"))
        #         file_valid.setdefault("errors", []).extend(ldsc_valid.get("errors", []))
        #         file_valid.setdefault("warnings", []).extend(ldsc_valid.get("warnings", []))
        #     else:
        #         file_valid["valid"] = bool(ldsc_valid)

        app.logger.info(f"Sumstats validation result for {filename}: {file_valid}")

        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"Validation completed ({execution_time}s)")

        return jsonify({"fileValid": file_valid})
    except Exception as e:
        app.logger.error(f"Error validating sumstats file: {e}")
        app.logger.error("".join(traceback.format_exception(None, e, e.__traceback__)))
        return jsonify({"fileValid": {"valid": False, "errors": [str(e)], "warnings": []}})


@app.route("/LDlinkRestWeb/validate_bfile", methods=["GET"])
def validate_bfile():
    """
    Validates bfile (bed/bim/fam) for LDscore calculation.
    Expects 'filename' (base name without extension) and 'reference' as query parameters.
    Returns JSON with 'fileValid' boolean.
    """
    start_time = time.time()
    app.logger.info("Starting bfile validation request")
    
    filename = request.args.get("filename", None)
    reference = request.args.get("reference", None)
    
    if not filename:
        app.logger.warning("Validation request missing filename")
        return jsonify({"fileValid": False, "error": "Missing filename parameter"})
    
    filename = secure_filename(filename)
    if not filename:
        app.logger.warning("Validation request filename invalid after sanitization")
        return jsonify({"fileValid": False, "error": "Invalid filename parameter"})

    # Remove only the bfile extension (.bed, .bim, or .fam) if provided
    if filename.endswith(('.bed', '.bim', '.fam')):
        fileroot = filename[:-4]  # Remove last 4 characters (.bed/.bim/.fam)
    else:
        fileroot = filename

    try:
        _, bfile_path, upload_dir = _resolve_upload_file_path(fileroot, reference)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid bfile validation input: {validation_error}")
        return jsonify({"fileValid": False, "error": str(validation_error)})
    
    app.logger.debug(f"Validating bfile: {bfile_path}")
    
    try:
        compatibility = validate_bfile_compatibility(fileroot, reference, _resolve_upload_file_path, validBfile)
        write_compatibility_metadata(upload_dir, compatibility)
        app.logger.info(f"Bfile compatibility validation result for {filename}: {compatibility}")
        
        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"Bfile validation completed ({execution_time}s)")
        
        return jsonify({"fileValid": compatibility})
    except Exception as e:
        app.logger.error(f"Error validating bfile: {e}")
        app.logger.error("".join(traceback.format_exception(None, e, e.__traceback__)))
        return jsonify({"fileValid": False, "error": str(e)})


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
        results = json.dumps({"error": "An error occurred while retrieving the timestamp"}, sort_keys=True, indent=2)
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
@requires_token
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
    reference = request.args.get("reference", "")
    if not str(reference).strip():
        reference = generate_reference()
    app.logger.debug(
        f"LDscore params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, ldwindow: {ldwindow}, windUnit: {windUnit}, isExample: {isExample}"
    )

    try:
        reference, fileDir = _resolve_upload_dir(reference)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDscore reference: {validation_error}")
        return sendTraceback(str(validation_error))

    inputfilename = "22"
    # print(filename)
    if filename:
        # Split by comma or semicolon (adjust as needed)
        filenames = [secure_filename(f.strip()) for f in filename.replace(";", ",").split(",")]
        # Set inputfilename from the first file (all files should have the same base name)
        if filenames:
            first_fileroot, _ = os.path.splitext(filenames[0])
            inputfilename = first_fileroot
        for fname in filenames:
            fileroot, ext = os.path.splitext(fname)
            
            # Validate that all files have the same base name
            if fileroot != inputfilename:
                error_msg = f"All uploaded files must have the same base name. Expected '{inputfilename}' but got '{fileroot}' for file '{fname}'"
                app.logger.error(error_msg)
                #return  {"result": error_msg}
            
            # Find the chromosome number in the filename
            # file_parts = fname.split(".")
            # file_chromo = None
            # for part in file_parts:
            #     if part.isdigit() and 1 <= int(part) <= 22:
            #         file_chromo = part
            #         break

            #app.logger.info(file_chromo)
            if fname:
                try:
                    safe_fname, new_file_path, _ = _resolve_upload_file_path(fname, reference, create_dir=True)
                except ValueError as validation_error:
                    app.logger.warning(f"Invalid LDscore filename: {validation_error}")
                    return sendTraceback(str(validation_error))
                
                if str(isExample).lower() == "true":
                    # For example files, only allow files under the fixed example directory
                    try:
                        safe_fname, source_path = _resolve_ldscore_example_path(safe_fname)
                        app.logger.info(f"Copying example file from {source_path} to {new_file_path}")
                        shutil.copyfile(source_path, new_file_path)
                        app.logger.info(f"Copied example file {safe_fname} to {new_file_path}")
                    except (ValueError, FileNotFoundError) as copy_error:
                        app.logger.warning(f"Invalid LDscore example file request: {copy_error}")
                        return sendTraceback(str(copy_error))
                    except OSError as copy_error:
                        app.logger.error(f"Failed to copy LDscore example file: {copy_error}")
                        return sendTraceback("Unable to copy requested example file.")
                else:
                    # For uploaded files, they are already in the reference folder from upload endpoint
                    # Just verify the file exists
                    if os.path.exists(new_file_path):
                        app.logger.info(f"Using uploaded file at {new_file_path}")
                    else:
                        app.logger.error(f"Uploaded file not found at {new_file_path}")
                    # os.rename(file_path, new_file_path)
                    # print(f"Copied {file_path} to {new_file_path}")
    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors
 
        compatibility = validate_bfile_compatibility(inputfilename, reference, _resolve_upload_file_path, validBfile, genome_build=genome_build)
        write_compatibility_metadata(fileDir, compatibility)
        if not compatibility.get("valid"):
            app.logger.warning(f"Blocking LDscore calculation for incompatible LD score inputs: {compatibility}")
            return jsonify({"error": "; ".join(compatibility.get("errors", [])), "compatibility": compatibility}), 400

        result = run_ldsc_command(pop, genome_build, inputfilename, ldwindow, windUnit, isExample, reference)
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
            schedule_tmp_cleanup(reference, app.logger)
            schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])
            return filtered_result
            out_json = pretty_out_json

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDscore request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])
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
@requires_token
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
    reference = request.args.get("reference", "")
    if not str(reference).strip():
        reference = generate_reference()
    scale = request.args.get("scale", "observed")
    samp_prev = request.args.get("samp_prev", "")
    pop_prev = request.args.get("pop_prev", "")
    try:
        scale, samp_prev, pop_prev = _validate_ldsc_scale_params(scale, samp_prev, pop_prev)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDherit prevalence input: {validation_error}")
        return sendTraceback(str(validation_error))
    app.logger.debug(
        f"LDherit params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, isexample: {isexample}, scale: {scale}"
    )
    if filename:
        filename = secure_filename(filename)
        fileroot, ext = os.path.splitext(filename)

    try:
        reference, fileDir = _resolve_upload_dir(reference)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDherit reference: {validation_error}")
        return sendTraceback(str(validation_error))

    app.logger.debug(f"LDherit processing filename: {filename}")
    # Handle file copying based on example vs uploaded
    if filename:
        filename = secure_filename(filename)
        try:
            filename, new_file_path, _ = _resolve_upload_file_path(filename, reference, create_dir=True)
        except ValueError as validation_error:
            app.logger.warning(f"Invalid LDherit filename: {validation_error}")
            return sendTraceback(str(validation_error))
        
        if str(isexample).lower() == "true":
            # For example files, only allow files under the fixed example directory
            try:
                safe_filename, source_path = _resolve_ldscore_example_path(filename)
                app.logger.info(f"Copying example file from {source_path} to {new_file_path}")
                shutil.copyfile(source_path, new_file_path)
                app.logger.info(f"Copied example file {safe_filename} to {new_file_path}")
            except (ValueError, FileNotFoundError) as copy_error:
                app.logger.warning(f"Invalid LDherit example file request: {copy_error}")
                return sendTraceback(str(copy_error))
            except OSError as copy_error:
                app.logger.error(f"Failed to copy LDherit example file: {copy_error}")
                return sendTraceback("Unable to copy requested example file.")
        else:
            # For uploaded files, they are already in the reference folder from upload endpoint
            # Just verify the file exists
            if os.path.exists(new_file_path):
                app.logger.info(f"Using uploaded file at {new_file_path}")
            else:
                app.logger.error(f"Uploaded file not found at {new_file_path}")
    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors

        if str(isexample).lower() != "true":
            compatibility = validate_sumstats_preanalysis([filename], reference, fileDir)
            write_compatibility_metadata(fileDir, compatibility)
            if not compatibility.get("valid"):
                app.logger.warning(f"Blocking LDherit calculation before downstream processing: {compatibility}")
                return jsonify({"error": "; ".join(compatibility.get("errors", [])), "compatibility": compatibility}), 400

        result = run_herit_command(filename, fileDir, pop, isexample, scale=scale, samp_prev=samp_prev, pop_prev=pop_prev)
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
            schedule_tmp_cleanup(reference, app.logger)
            schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])
            return filtered_result
            out_json = pretty_out_json

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDherit request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])
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
    reference = request.args.get("reference", "")
    if not str(reference).strip():
        reference = generate_reference()

    try:
        reference, fileDir = _resolve_upload_dir(reference, create_dir=True)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDherit API reference: {validation_error}")
        return jsonify({"error": str(validation_error)}), 400

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    uploaded_filename = secure_filename(file.filename)
    if not uploaded_filename:
        return jsonify({"error": "Invalid filename"}), 400

    try:
        _, saved_file_path, _ = _resolve_upload_file_path(uploaded_filename, reference, create_dir=True)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDherit API filename: {validation_error}")
        return jsonify({"error": str(validation_error)}), 400

    file.save(saved_file_path)

    pop = request.args.get("pop", False)
    genome_build = request.args.get("genome_build", "grch37")
    requested_filename = request.args.get("filename", False)
    isexample = request.args.get("isExample", False)
    scale = request.args.get("scale", "observed")
    samp_prev = request.args.get("samp_prev", "")
    pop_prev = request.args.get("pop_prev", "")
    filename = uploaded_filename

    if requested_filename:
        sanitized_requested_filename = secure_filename(str(requested_filename))
        if sanitized_requested_filename and sanitized_requested_filename != uploaded_filename:
            app.logger.warning(
                f"LDherit API filename mismatch: request filename '{sanitized_requested_filename}' differs from uploaded filename '{uploaded_filename}'. Using uploaded filename."
            )

    try:
        scale, samp_prev, pop_prev = _validate_ldsc_scale_params(scale, samp_prev, pop_prev)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDherit API prevalence input: {validation_error}")
        return sendTraceback(str(validation_error))

    start_time = time.time()

    app.logger.debug(
        f"LDherit API params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, isexample: {isexample}, scale: {scale}"
    )

    app.logger.debug(f"LDherit API processing filename: {filename}")
    try:
        # Make an API call to the ldsc39_container

        # response = requests.get(ldsc39_url)
        # response.raise_for_status()  # Raise an exception for HTTP errors

        result = run_herit_command(filename, fileDir, pop, isexample, scale=scale, samp_prev=samp_prev, pop_prev=pop_prev)

        # Pretty-print the JSON output
        summary_index = result.find("Total Observed scale")
        if summary_index != -1:
            filtered_result = result[summary_index:]
        else:
            filtered_result = result

        # Delete uploaded file after processing
        try:
            os.remove(saved_file_path)
            app.logger.info(f"Deleted file: {saved_file_path}")
        except Exception as e:
            app.logger.error(f"Error deleting file {saved_file_path}: {e}")
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
@requires_token
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
    reference = request.args.get("reference", "")
    if not str(reference).strip():
        reference = generate_reference()
    scale = request.args.get("scale", "observed")
    samp_prev = request.args.get("samp_prev", "")
    pop_prev = request.args.get("pop_prev", "")
    try:
        scale, samp_prev, pop_prev = _validate_ldsc_scale_params(scale, samp_prev, pop_prev, require_pair=True)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDcorrelation prevalence input: {validation_error}")
        return sendTraceback(str(validation_error))
    app.logger.debug(
        f"LDcorrelation params - pop: {pop}, genome_build: {genome_build}, filename: {filename}, isexample: {isexample}, reference: {reference}, scale: {scale}"
    )
    if filename:
        filename = secure_filename(filename)
    if filename2:
        filename2 = secure_filename(filename2)

    try:
        reference, fileDir = _resolve_upload_dir(reference)
    except ValueError as validation_error:
        app.logger.warning(f"Invalid LDcorrelation reference: {validation_error}")
        return sendTraceback(str(validation_error))
    
    # Handle file copying based on example vs uploaded
    for fname in [filename, filename2]:
        if fname:
            try:
                safe_fname, new_file_path, _ = _resolve_upload_file_path(fname, reference, create_dir=True)
            except ValueError as validation_error:
                app.logger.warning(f"Invalid LDcorrelation filename: {validation_error}")
                return sendTraceback(str(validation_error))
            
            if str(isexample).lower() == "true":
                # For example files, only allow files under the fixed example directory
                try:
                    safe_fname, source_path = _resolve_ldscore_example_path(safe_fname)
                    app.logger.info(f"Copying example file from {source_path} to {new_file_path}")
                    shutil.copyfile(source_path, new_file_path)
                    app.logger.info(f"Copied example file {safe_fname} to {new_file_path}")
                except (ValueError, FileNotFoundError) as copy_error:
                    app.logger.warning(f"Invalid LDcorrelation example file request: {copy_error}")
                    return sendTraceback(str(copy_error))
                except OSError as copy_error:
                    app.logger.error(f"Failed to copy LDcorrelation example file: {copy_error}")
                    return sendTraceback("Unable to copy requested example file.")
            else:
                # For uploaded files, they are already in the reference folder from upload endpoint
                # Just verify the file exists
                if os.path.exists(new_file_path):
                    app.logger.info(f"Using uploaded file at {new_file_path}")
                else:
                    app.logger.error(f"Uploaded file not found at {new_file_path}")
    try:
        # Make an API call to the ldsc39_container
        if str(isexample).lower() != "true":
            compatibility = validate_sumstats_preanalysis([filename, filename2], reference, fileDir)
            write_compatibility_metadata(fileDir, compatibility)
            if not compatibility.get("valid"):
                app.logger.warning(f"Blocking LDcorrelation calculation before downstream processing: {compatibility}")
                return jsonify({"error": "; ".join(compatibility.get("errors", [])), "compatibility": compatibility}), 400

        result = run_correlation_command(
            filename,
            filename2,
            fileDir,
            pop,
            isexample,
            scale=scale,
            samp_prev=samp_prev,
            pop_prev=pop_prev,
        )
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
            if summary_index == -1:
                summary_index = result.find("Total Liability scale")
            if summary_index != -1:
                filtered_result = result[summary_index:]
            else:
                filtered_result = result
            # filtered_result = filtered_result.replace("\\n", "\n")
            # out_json = {"result": filtered_result}
            # pretty_out_json = json.dumps(out_json, indent=4)
            # print(pretty_out_json)
            schedule_tmp_cleanup(reference, app.logger)
            schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])
            return filtered_result
            out_json = pretty_out_json

    except requests.RequestException as e:
        # Log the error message
        app.logger.error(f"LDcorrelation request error: {e}")
        out_json = {"error": str(e)}

    end_time = time.time()
    app.logger.info("Executed LDscore (%ss)" % (round(end_time - start_time, 2)))
    schedule_tmp_cleanup(reference, app.logger)
    schedule_tmp_cleanup_ldscore(reference, app.logger, tmp_dir=app.config["UPLOAD_DIR"])
    return jsonify(out_json)


# Web and API route for LDexpress
@app.route("/LDlinkRest/ldexpress", methods=["POST"])
# @app.route('/LDlinkRest2/ldexpress', methods=['POST'])
@app.route("/LDlinkRestWeb/ldexpress", methods=["POST"])
@requires_token
def ldexpress():
    start_time = time.time()
    data = _get_request_json_body()
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
        str(data["reference"]) if "reference" in data else generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    reference = request.args.get("reference") or generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
        data = _get_request_json_body()
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
        reference = generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
            data = _get_request_json_body()
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
            reference = request.args.get("reference") or generate_reference()
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
        reference = generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    reference = request.args.get("reference") or generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    reference = request.args.get("reference") or generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    data = _get_request_json_body()
    snps = data["snps"]
    pop = data["pop"]
    r2_d = data["r2_d"]
    r2_d_threshold = data["r2_d_threshold"]
    window = data["window"].replace(",", "") if "window" in data else "500000"
    token = request.args.get("token", False)
    genome_build = data["genome_build"] if "genome_build" in data else "grch37"
    web = False
    reference = (
        str(data["reference"]) if "reference" in data else generate_reference()
    )

    # differentiate web or api request
    if "LDlinkRestWeb" in request.path:
        # WEB REQUEST
        if request.headers.get("User-Agent"):
            web = True
            if data["ifContinue"]:
                ifContinue = data["ifContinue"]
                ifContinue = bool(ifContinue != "False")
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    r2_d = request.args.get("r2_d", "r2")
    r2_d_threshold = request.args.get("r2_d_threshold", 0.1)
    token = request.args.get("token", False)
    genome_build = request.args.get("genome_build", "grch37")

    # Optional parameters
    window = request.args.get("window", "500000").replace(",", "")

    reference = request.args.get("reference") or generate_reference()

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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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


@app.route("/LDlinkRest/ldexpressget", methods=["GET"])
@app.route("/LDlinkRestWeb/ldexpressget", methods=["GET"])
@requires_token
def ldexpressgwas():
    start_time = time.time()
    # Required parameters
    snps = request.args.get("snps", False)
    pop = request.args.get("pop", False)
    r2_d = request.args.get("r2_d", "r2")
    r2_d_threshold = request.args.get("r2_d_threshold", 0.1)
    p_threshold = request.args.get("p_threshold", 0.1)
    token = request.args.get("token", False)
    # Optional parameters
    tissues = request.args.get(
        "tissues",
        "Adipose_Subcutaneous+Adipose_Visceral_Omentum+Adrenal_Gland+Artery_Aorta+Artery_Coronary+Artery_Tibial+Bladder+Brain_Amygdala+Brain_Anterior_cingulate_cortex_BA24+Brain_Caudate_basal_ganglia+Brain_Cerebellar_Hemisphere+Brain_Cerebellum+Brain_Cortex+Brain_Frontal_Cortex_BA9+Brain_Hippocampus+Brain_Hypothalamus+Brain_Nucleus_accumbens_basal_ganglia+Brain_Putamen_basal_ganglia+Brain_Spinal_cord_cervical_c-1+Brain_Substantia_nigra+Breast_Mammary_Tissue+Cells_EBV-transformed_lymphocytes+Cells_Cultured_fibroblasts+Cervix_Ectocervix+Cervix_Endocervix+Colon_Sigmoid+Colon_Transverse+Esophagus_Gastroesophageal_Junction+Esophagus_Mucosa+Esophagus_Muscularis+Fallopian_Tube+Heart_Atrial_Appendage+Heart_Left_Ventricle+Kidney_Cortex+Kidney_Medulla+Liver+Lung+Minor_Salivary_Gland+Muscle_Skeletal+Nerve_Tibial+Ovary+Pancreas+Pituitary+Prostate+Skin_Not_Sun_Exposed_Suprapubic+Skin_Sun_Exposed_Lower_leg+Small_Intestine_Terminal_Ileum+Spleen+Stomach+Testis+Thyroid+Uterus+Vagina+Whole_Blood",
    )
    window = request.args.get("window", "500000")
    genome_build = request.args.get("genome_build", "grch37")
    reference = request.args.get("reference") or generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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


# Web and API route for SNPchip
@app.route("/LDlinkRest/snpchip", methods=["POST"])
@app.route("/LDlinkRestWeb/snpchip", methods=["POST"])
@requires_token
def snpchip():
    start_time = time.time()
    data = _get_request_json_body()
    snps = data.get("snps")
    genome_build = data.get("genome_build", "grch37")
    platforms = data.get("platforms")
    token = request.args.get("token", False)
    web = False
    reference = (
        str(data["reference"]) if "reference" in data else generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    data = _get_request_json_body()
    snps = data["snps"]
    pop = data["pop"]
    r2_threshold = data["r2_threshold"]
    maf_threshold = data["maf_threshold"]
    token = request.args.get("token", False)
    genome_build = data["genome_build"] if "genome_build" in data else "grch37"
    web = False
    reference = (
        str(data["reference"]) if "reference" in data else generate_reference()
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
            if not toggleLocked(token, 1):
                return sendTraceback("Concurrent API requests restricted. Please limit usage to sequential requests only. Contact system administrator if you have issues accessing API: NCILDlinkWebAdmin@mail.nih.gov")
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
    app.run(host="127.0.0.1", port=port_num, use_evalex=False)
    # app.logger.disabled = True
    # application = DebuggedApplication(app, True)
    app.debug = False
