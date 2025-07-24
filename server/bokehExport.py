# Selenium webdriver (required for bokeh image exports) doesn't run properly under mod_wsgi, so we run it under a local flask service at localhost:5000
from flask import Flask, request, jsonify
from LDassoc_plot_sub import calculate_assoc_svg
from LDmatrix_plot_sub import calculate_matrix_svg
from LDproxy_plot_sub import calculate_proxy_svg
from LDcommon import get_config
import sys
import traceback

app = Flask(__name__)

@app.route("/ping", methods=['GET'])
def ping():
    print(f"[ping] Ping request received from {request.remote_addr}", flush=True)
    return jsonify({'status': 'ok'}), 200

@app.route("/ldassoc_svg", methods=['POST'])
def ldassocExport():
    request_id = request.get_json().get('request', 'unknown') if request.get_json() else 'unknown'
    print(f"[{request_id}] LDassoc SVG export request received from {request.remote_addr}", flush=True)
    try:
        data = request.get_json()
        print(f"[{request_id}] LDassoc request data: {data}", flush=True)
        
        required = ['file', 'region', 'pop', 'request', 'genome_build', 'args', 'argsName', 'argsOrigin']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            print(f"[{request_id}] LDassoc missing required parameters: {missing}", flush=True)
            return jsonify({'error': 'Missing required parameters'}), 400
            
        print(f"[{request_id}] LDassoc calling calculate_assoc_svg with parameters: file={data['file']}, region={data['region']}, pop={data['pop']}, genome_build={data['genome_build']}", flush=True)
        
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
        
        print(f"[{request_id}] LDassoc SVG export completed successfully", flush=True)
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"[{request_id}] Error in ldassocExport: {str(e)}", flush=True)
        print(f"[{request_id}] LDassoc error traceback: {traceback.format_exc()}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route("/ldmatrix_svg", methods=['POST'])
def ldmatrixExport():
    request_id = request.get_json().get('request', 'unknown') if request.get_json() else 'unknown'
    print(f"[{request_id}] LDmatrix SVG export request received from {request.remote_addr}", flush=True)
    try:
        data = request.get_json()
        print(f"[{request_id}] LDmatrix request data: {data}", flush=True)
        
        required = ['snplst', 'pop', 'request', 'genome_build', 'r2_d', 'collapseTranscript', 'annotate']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            print(f"[{request_id}] LDmatrix missing required parameters: {missing}", flush=True)
            return jsonify({'error': 'Missing required parameters'}), 400
            
        print(f"[{request_id}] LDmatrix calling calculate_matrix_svg with parameters: snplst={data['snplst']}, pop={data['pop']}, genome_build={data['genome_build']}, r2_d={data['r2_d']}", flush=True)
        
        result = calculate_matrix_svg(
            data['snplst'],
            data['pop'],
            data['request'],
            data['genome_build'],
            data['r2_d'],
            data['collapseTranscript'],
            data['annotate']
        )
        
        print(f"[{request_id}] LDmatrix SVG export completed successfully", flush=True)
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"[{request_id}] Error in ldmatrixExport: {str(e)}", flush=True)
        print(f"[{request_id}] LDmatrix error traceback: {traceback.format_exc()}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route("/ldproxy_svg", methods=['POST'])
def ldproxyExport():
    request_id = request.get_json().get('request', 'unknown') if request.get_json() else 'unknown'
    print(f"[{request_id}] LDproxy SVG export request received from {request.remote_addr}", flush=True)
    try:
        data = request.get_json()
        print(f"[{request_id}] LDproxy request data: {data}", flush=True)
        
        required = ['snp', 'pop', 'request', 'genome_build', 'r2_d', 'window', 'collapseTranscript', 'annotate']
        if not all(k in data for k in required):
            missing = [k for k in required if k not in data]
            print(f"[{request_id}] LDproxy missing required parameters: {missing}", flush=True)
            return jsonify({'error': 'Missing required parameters'}), 400
            
        print(f"[{request_id}] LDproxy calling calculate_proxy_svg with parameters: snp={data['snp']}, pop={data['pop']}, genome_build={data['genome_build']}, r2_d={data['r2_d']}, window={data['window']}", flush=True)
        
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
        
        print(f"[{request_id}] LDproxy SVG export completed successfully", flush=True)
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"[{request_id}] Error in ldproxyExport: {str(e)}", flush=True)
        print(f"[{request_id}] LDproxy error traceback: {traceback.format_exc()}", flush=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("[startup] Starting bokehExport Flask service...", flush=True)
    param_list = get_config()
    port = param_list.get('bokeh_export_port', 5000)
    print(f"[startup] Bokeh export service will run on port {port}", flush=True)
    app.run(host='0.0.0.0', port=port)