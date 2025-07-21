# Selenium webdriver (required for bokeh image exports) doesn't run properly under mod_wsgi, so we run it under a local flask service at localhost:5000
from flask import Flask, request, jsonify
from LDassoc_plot_sub import calculate_assoc_svg
from LDmatrix_plot_sub import calculate_matrix_svg
from LDproxy_plot_sub import calculate_proxy_svg
from LDcommon import get_config

app = Flask(__name__)

@app.route("/ping", methods=['GET'])
def ping():
    return jsonify({'status': 'ok'}), 200

@app.route("/ldassoc_svg", methods=['POST'])
def ldassocExport():
    try:
        data = request.get_json()
        required = ['file', 'region', 'pop', 'request', 'genome_build', 'args', 'argsName', 'argsOrigin']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required parameters'}), 400
            
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
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Error in ldassocExport: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route("/ldmatrix_svg", methods=['POST'])
def ldmatrixExport():
    try:
        data = request.get_json()
        required = ['snplst', 'pop', 'request', 'genome_build', 'r2_d', 'collapseTranscript', 'annotate']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        result = calculate_matrix_svg(
            data['snplst'],
            data['pop'],
            data['request'],
            data['genome_build'],
            data['r2_d'],
            data['collapseTranscript'] == 'true',
            data['annotate']
        )
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Error in ldmatrixExport: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route("/ldproxy_svg", methods=['POST'])
def ldproxyExport():
    try:
        data = request.get_json()
        required = ['snp', 'pop', 'request', 'genome_build', 'r2_d', 'window', 'collapseTranscript', 'annotate']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required parameters'}), 400
        result = calculate_proxy_svg(
            data['snp'],
            data['pop'],
            data['request'],
            data['genome_build'],
            data['r2_d'],
            int(data['window']),
            data['collapseTranscript'] == 'true' if isinstance(data['collapseTranscript'], str) else bool(data['collapseTranscript']),
            data['annotate']
        )
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error in ldproxyExport: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    param_list = get_config()
    port = param_list.get('bokeh_export_port', 5000)
    app.run(host='0.0.0.0', port=port)