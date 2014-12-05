#!flask/bin/python
from flask import Flask, render_template, Response, abort, request, make_response, url_for, jsonify, redirect
from functools import wraps
from flask import current_app

import cgi
import shutil
import os
from xml.sax.saxutils import escape, unescape
from socket import gethostname
import json
import pandas as pd
import numpy as np
from pandas import DataFrame
import urllib
from LDpair import calculate_pair
from LDproxy import calculate_proxy
from LDmatrix import calculate_matrix
from LDhap import calculate_hap

#import os
#from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

UPLOAD_FOLDER = '/h1/kneislercp/nci-analysis-tools-web-presence/src/LDlink/tmp'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__, static_folder='', static_url_path='/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.debug = True

#app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')

def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            #mimetype = 'application/javascript'
            mimetype = 'application/json'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function


def setRWorkingDirectory():
    sourceReturn1 = robjects.r("path")
    return ""
'''
@app.route('/riskStratAdvRest/cal', methods = ['POST'])
@jsonp
def callRFunction():
    rSource = robjects.r('source')
    rSource('./input.R')
    r_getname_getData = robjects.globalenv['getDataJSON']
    thestream=request.stream.read();
    print " input stream "+str(thestream);
    jsondata = r_getname_getData(thestream)
    print "json string >> "+str(jsondata[0]);
    return jsondata[0]
'''


@app.route('/LDlinkRest/ldpair', methods = ['GET'])
def ldpair():
    # analysistools-sandbox.nci.nih.gov/LDlinkRest/test?snp1=rs2720460&snp2=rs11733615&pop=EUR&reference=28941
    # python LDpair.py rs2720460 rs11733615 EUR 38
    # r1 = '{"corr_alleles":["rs2720460(A) allele is correlated with rs11733615(C) allele","rs2720460(G) allele is correlated with rs11733615(T) allele"],"haplotypes":{"hap1":{"alleles":"AC","count":"576","frequency":"0.573"},"hap2":{"alleles":"GT","count":"361","frequency":"0.359"},"hap3":{"alleles":"GC","count":"42","frequency":"0.042"},"hap4":{"alleles":"AT","count":"27","frequency":"0.027"}},"snp1":{"allele_1":{"allele":"A","count":"603","frequency":"0.599"},"allele_2":{"allele":"G","count":"403","frequency":"0.401"},"coord":"chr4:104054686","rsnum":"rs2720460"},"snp2":{"allele_1":{"allele":"C","count":"618","frequency":"0.614"},"allele_2":{"allele":"T","count":"388","frequency":"0.386"},"coord":"chr4:104157164","rsnum":"rs11733615"},"statistics":{"chisq":"738.354","d_prime":"0.8839","p":"0.0","r2":"0.734"},"two_by_two":{"cells":{"11":"576","12":"27","21":"42","22":"361"},"total":"1006"}'

    print
    print 'Execute TEST'
    print 'Gathering Variables from url'
    snp1 = request.args.get('snp1', False)
    snp2 = request.args.get('snp2', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    # reference = "939393"
    print 'snp1: ' + snp1
    print 'snp2: ' + snp2
    print 'pop: ' + pop
    print 'request: ' + reference
    print
    out_json = calculate_pair(snp1, snp2, pop, reference)
    mimetype = 'application/json'

    return current_app.response_class(out_json, mimetype=mimetype)

@app.route('/LDlinkRest/ldproxy', methods = ['GET'])
def ldproxy():
    print
    print 'Execute ldproxy'
    print 'Gathering Variables from url'
    snp = request.args.get('snp', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    print 'snp: ' + snp
    print 'pop: ' + pop
    print 'request: ' + reference
    print

    #out_json,out_script,out_div=calculate_proxy(snp, pop, reference)
    out_script,out_div = calculate_proxy(snp, pop, reference)

    return out_script+"\n "+out_div


@app.route('/LDlinkRest/ldmatrix', methods = ['GET'])
def ldmatrix():
    # python LDmatrix.py snps.txt EUR 5
    #http://analysistools-sandbox.nci.nih.gov/LDlinkRest/ldmatrix?pop=EUR&reference=5&snp=sr3
    #http://analysistools-sandbox.nci.nih.gov/LDlinkRest/ldmatrix?filename=get+from+input&pop=LWK%2BGWD&reference=76178
    print
    print 'Execute ldmatrix'
    print 'Gathering Variables from url'

    snps = request.args.get('snps', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    print 'snps: ' + snps
    print 'pop: ' + pop
    print 'request: ' + reference

    snplst = './tmp/snps'+reference+'.txt'
    print 'snplst: '+snplst

    f = open(snplst, 'w')
    f.write(snps)
    f.close()

    out_script,out_div = calculate_matrix(snplst,pop,reference)
    return out_script+"\n "+out_div
    #return request.method


@app.route('/LDlinkRest/ldhap', methods = ['GET'])
def ldhap():
    # python LDmatrix.py snps.txt EUR 5
    #http://analysistools-sandbox.nci.nih.gov/LDlinkRest/ldmatrix?pop=EUR&reference=5&snp=sr3
    #http://analysistools-sandbox.nci.nih.gov/LDlinkRest/ldmatrix?filename=get+from+input&pop=LWK%2BGWD&reference=76178
    print
    print 'Execute ldhap'
    print 'Gathering Variables from url'

    snps = request.args.get('snps', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    print 'snps: ' + snps
    print 'pop: ' + pop
    print 'request: ' + reference

    snplst = './tmp/snps'+reference+'.txt'
    print 'snplst: '+snplst

    f = open(snplst, 'w')
    f.write(snps)
    f.close()

    out_json = calculate_hap(snplst,pop,reference)
    return out_json


@app.route('/LDlinkRest/test', methods=['GET', 'POST'])
def test():
    print 'In /LDlinkRest/test'
    print 'request.headers[Content-Type]'
    print request.headers['Content-Type']
    print ''
    print 'request.data'
    print request.data
    print 'request.args'
    print json.dumps(request.args)

    print 'request.files'
    print request.files

    print 'request.method'
    print request.method

    print
    print 'Execute ldmatrix'
    print 'Gathering Variables from url'
    snps = request.args.get('snps', False)
    #filename = request.args.get('filename', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    print 'snp: ' + snp
    print 'pop: ' + pop
    print 'request: ' + reference
    print
    snplst = 'snps2.txt'

    if request.headers['Content-Type'] == 'text/plain':
        return "Text Message: " + request.data

    elif request.headers['Content-Type'] == 'application/json':
        return "JSON Message: " + json.dumps(request.json)

    elif request.headers['Content-Type'] == 'application/octet-stream':
        f = open('./binary', 'wb')
        f.write(request.data)
        f.close()
        return "Binary message written!"
    elif request.headers['Content-Type'] == 'multipart/form-data':
        return 'multipart/form-data'
    elif request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
        return 'application/x-www-form-urlencoded'

    else:
        return "415 Unsupported Media Type ;)"


@app.route('/LDlinkRest/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        rec = Photo(filename=filename, user=g.user.id)
        rec.store()
        flash("Photo saved.")
        return redirect(url_for('show', id=rec.id))
    return render_template('upload.html')


import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number", default="9982", help="Sets the Port")
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number);

    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, debug = True)
