#!flask/bin/python
from flask import Flask, render_template, Response, abort, request, make_response, url_for, jsonify
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

app = Flask(__name__, static_folder='', static_url_path='/')
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

@app.route('/LDlinkRest/hello', methods = ['GET'])
def hello():
    return 'hello'

@app.route('/LDlinkRest/ldhap', methods = ['GET'])
def ldhap():
    r1 = 'Calling ldhap'
    return r1

@app.route('/LDlinkRest/ldproxy', methods = ['GET'])
def ldproxy():
    r1 = 'Calling ldproxy'
    return r1

@app.route('/LDlinkRest/ldpair', methods = ['GET'])
def ldpair():
    r1 = '{"corr_alleles":["rs2720460(A) allele is correlated with rs11733615(C) allele","rs2720460(G) allele is correlated with rs11733615(T) allele"],"haplotypes":{"hap1":{"alleles":"AC","count":"576","frequency":"0.573"},"hap2":{"alleles":"GT","count":"361","frequency":"0.359"},"hap3":{"alleles":"GC","count":"42","frequency":"0.042"},"hap4":{"alleles":"AT","count":"27","frequency":"0.027"}},"snp1":{"allele_1":{"allele":"A","count":"603","frequency":"0.599"},"allele_2":{"allele":"G","count":"403","frequency":"0.401"},"coord":"chr4:104054686","rsnum":"rs2720460"},"snp2":{"allele_1":{"allele":"C","count":"618","frequency":"0.614"},"allele_2":{"allele":"T","count":"388","frequency":"0.386"},"coord":"chr4:104157164","rsnum":"rs11733615"},"statistics":{"chisq":"738.354","d_prime":"0.8839","p":"0.0","r2":"0.734"},"two_by_two":{"cells":{"11":"576","12":"27","21":"42","22":"361"},"total":"1006"}'
    return r1

@app.route('/LDlinkRest/ldheat', methods = ['GET'])
def ldheat():
    r1 = 'Calling ldheat'
    return r1

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number", default="9982", help="Sets the Port") 
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number);
    
    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, debug = True)
