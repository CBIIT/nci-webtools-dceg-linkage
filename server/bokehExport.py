# Selenium webdriver (required for bokeh image exports) doesn't run properly under mod_wsgi, so we run it under a local flask service at localhost:5000
from flask import Flask, request, jsonify
from LDassoc_plot_sub import calculate_assoc_svg
from LDmatrix_plot_sub import calculate_matrix_svg
from LDproxy_plot_sub import calculate_proxy_svg
from LDcommon import get_config
import hmac
import os
import sys
import traceback
import logging
import time
import uuid

app = Flask(__name__)

# Configure logging for bokeh export service
param_list = get_config()
log_level = getattr(logging, param_list.get("log_level", "INFO").upper(), logging.INFO)
formatter = logging.Formatter("[%(name)s] [%(asctime)s] [%(levelname)s] - %(message)s", "%Y-%m-%d %H:%M:%S")
handler = logging.StreamHandler(stream=sys.stderr)
handler.setLevel(log_level)
handler.setFormatter(formatter)

app.logger = logging.getLogger("bokehexport")
app.logger.setLevel(log_level)
app.logger.addHandler(handler)


def _is_loopback(remote_addr):
    return remote_addr in {"127.0.0.1", "::1", "localhost"}


def _invalid_parameter_response(parameter, reason):
    app.logger.warning(
        f"Rejected export request: path={request.path}, remote={request.remote_addr}, parameter={parameter}, reason={reason}"
    )
    return jsonify({"error": f"Invalid {parameter} parameter."}), 400


def _is_valid_uuid_reference(value):
    normalized_value = str(value).strip()
    try:
        parsed_uuid = uuid.UUID(normalized_value)
    except (TypeError, ValueError, AttributeError):
        return False
    return parsed_uuid.version == 4 and str(parsed_uuid) == normalized_value.lower()


def _validate_reference(parameter, value):
    normalized_value = str(value or "").strip()
    if not normalized_value or not _is_valid_uuid_reference(normalized_value):
        return _invalid_parameter_response(parameter, "request identifier must be a canonical UUIDv4 string")
    return None


def _validate_export_file(parameter, value):
    if value is None:
        return None

    path_value = str(value).strip()
    if not path_value or "\x00" in path_value:
        return _invalid_parameter_response(parameter, "empty or null-containing path")

    real_path = os.path.realpath(path_value)
    tmp_dir = param_list.get("tmp_dir")
    data_dir = param_list.get("data_dir")
    allowed_roots = [os.path.realpath(root) for root in (tmp_dir, data_dir) if str(root or "").strip()]
    for root in allowed_roots:
        if os.path.commonpath([root, real_path]) == root:
            return None
    return _invalid_parameter_response(parameter, "path is outside allowed export roots")


@app.before_request
def export_request_guard():
    if request.path == "/ping" or request.method == "OPTIONS":
        return None

    expected_internal_token = os.environ.get("LDLINK_INTERNAL_AUTH_TOKEN", "").strip()
    provided_internal_token = request.headers.get("X-Internal-Auth", "").strip()
    if expected_internal_token:
        if not hmac.compare_digest(provided_internal_token, expected_internal_token):
            app.logger.warning(f"Rejected export request with invalid internal auth from {request.remote_addr}")
            return jsonify({"error": "Forbidden"}), 403
    elif not _is_loopback(request.remote_addr):
        app.logger.warning(f"Rejected export request from non-loopback source {request.remote_addr}")
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    response = _validate_reference("request", data.get("request"))
    if response:
        return response

    if "file" in data:
        response = _validate_export_file("file", data.get("file"))
        if response:
            return response
    if "snplst" in data:
        response = _validate_export_file("snplst", data.get("snplst"))
        if response:
            return response

    return None

@app.route("/ping", methods=['GET'])
def ping():
    app.logger.debug(f"Health check ping received from {request.remote_addr}")
    return jsonify({'status': 'ok'}), 200

@app.route("/ldassoc_svg", methods=['POST'])
def ldassocExport():
    start_time = time.time()
    request_id = request.get_json().get('request', 'unknown') if request.get_json() else 'unknown'
    app.logger.info(f"[{request_id}] Starting LDassoc SVG export request from {request.remote_addr}")
    
    try:
        data = request.get_json()
        app.logger.debug(f"[{request_id}] LDassoc request parameters: file={data.get('file', 'N/A')}, region={data.get('region', 'N/A')}, pop={data.get('pop', 'N/A')}, genome_build={data.get('genome_build', 'N/A')}")
        
        required = ['file', 'region', 'pop', 'request', 'genome_build', 'args', 'argsName', 'argsOrigin']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            app.logger.warning(f"[{request_id}] LDassoc missing required parameters: {missing}")
            return jsonify({'error': 'Missing required parameters'}), 400
            
        app.logger.debug(f"[{request_id}] LDassoc calling calculate_assoc_svg")
        
        result = calculate_assoc_svg(
            data['file'],
            data['region'],
            data['pop'],
            data['request'],
            data['genome_build'],
            data['args'],
            data['argsName'],
            data['argsOrigin']
        )
        
        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"[{request_id}] LDassoc SVG export completed successfully ({execution_time}s)")
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        execution_time = round(time.time() - start_time, 2)
        app.logger.error(f"[{request_id}] LDassoc SVG export failed ({execution_time}s): {str(e)}")
        app.logger.error(f"[{request_id}] LDassoc error traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route("/ldmatrix_svg", methods=['POST'])
def ldmatrixExport():
    start_time = time.time()
    request_id = request.get_json().get('request', 'unknown') if request.get_json() else 'unknown'
    app.logger.info(f"[{request_id}] Starting LDmatrix SVG export request from {request.remote_addr}")
    
    try:
        data = request.get_json()
        app.logger.debug(f"[{request_id}] LDmatrix request parameters: snplst={data.get('snplst', 'N/A')}, pop={data.get('pop', 'N/A')}, genome_build={data.get('genome_build', 'N/A')}, r2_d={data.get('r2_d', 'N/A')}")
        
        required = ['snplst', 'pop', 'request', 'genome_build', 'r2_d', 'collapseTranscript', 'annotate']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            app.logger.warning(f"[{request_id}] LDmatrix missing required parameters: {missing}")
            return jsonify({'error': 'Missing required parameters'}), 400
            
        app.logger.debug(f"[{request_id}] LDmatrix calling calculate_matrix_svg")
        
        result = calculate_matrix_svg(
            data['snplst'],
            data['pop'],
            data['request'],
            data['genome_build'],
            data['r2_d'],
            data['collapseTranscript'],
            data['annotate']
        )
        
        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"[{request_id}] LDmatrix SVG export completed successfully ({execution_time}s)")
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        execution_time = round(time.time() - start_time, 2)
        app.logger.error(f"[{request_id}] LDmatrix SVG export failed ({execution_time}s): {str(e)}")
        app.logger.error(f"[{request_id}] LDmatrix error traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route("/ldproxy_svg", methods=['POST'])
def ldproxyExport():
    start_time = time.time()
    request_id = request.get_json().get('request', 'unknown') if request.get_json() else 'unknown'
    app.logger.info(f"[{request_id}] Starting LDproxy SVG export request from {request.remote_addr}")
    
    try:
        data = request.get_json()
        app.logger.debug(f"[{request_id}] LDproxy request parameters: snp={data.get('snp', 'N/A')}, pop={data.get('pop', 'N/A')}, genome_build={data.get('genome_build', 'N/A')}, r2_d={data.get('r2_d', 'N/A')}, window={data.get('window', 'N/A')}")
        
        required = ['snp', 'pop', 'request', 'genome_build', 'r2_d', 'window', 'collapseTranscript', 'annotate']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            app.logger.warning(f"[{request_id}] LDproxy missing required parameters: {missing}")
            return jsonify({'error': 'Missing required parameters'}), 400
            
        app.logger.debug(f"[{request_id}] LDproxy calling calculate_proxy_svg")
        
        result = calculate_proxy_svg(
            data['snp'],
            data['pop'],
            data['request'],
            data['genome_build'],
            data['r2_d'],
            int(data['window']),
            data['collapseTranscript'],
            data['annotate']
        )
        
        execution_time = round(time.time() - start_time, 2)
        app.logger.info(f"[{request_id}] LDproxy SVG export completed successfully ({execution_time}s)")
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        execution_time = round(time.time() - start_time, 2)
        app.logger.error(f"[{request_id}] LDproxy SVG export failed ({execution_time}s): {str(e)}")
        app.logger.error(f"[{request_id}] LDproxy error traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.logger.info("Starting bokehExport Flask service")
    port = param_list.get('bokeh_export_port', 5000)
    app.logger.info(f"Bokeh export service will run on port {port}")
    app.logger.info(f"Log level: {param_list.get('log_level', 'INFO')}")
    app.run(host='127.0.0.1', port=port)