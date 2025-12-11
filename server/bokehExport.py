# Selenium webdriver (required for bokeh image exports) doesn't run properly under mod_wsgi, so we run it under a local flask service at localhost:5000
from flask import Flask, request, jsonify
from LDassoc_plot_sub import calculate_assoc_svg
from LDmatrix_plot_sub import calculate_matrix_svg
from LDproxy_plot_sub import calculate_proxy_svg
from LDcommon import get_config
import sys
import traceback
import logging
import time

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
    app.run(host='0.0.0.0', port=port)