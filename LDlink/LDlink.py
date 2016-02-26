#!flask/bin/python
from flask import Flask, render_template, Response, abort, request, make_response, url_for, jsonify, redirect
from functools import wraps
from flask import current_app
from flask import jsonify

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
import collections

from LDpair import calculate_pair
from LDproxy import calculate_proxy
from LDmatrix import calculate_matrix
from LDhap import calculate_hap
from SNPclip import calculate_clip
from SNPchip import *

#import os
#from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

tmp_dir = "./tmp/"
# Ensure tmp directory exists
if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
		
app = Flask(__name__, static_folder='', static_url_path='/')
#app.debug = True

#app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')

# copy output files from tools' tmp directory to apache tmp directory
def copy_output_files(reference):
    apache_root = "/analysistools/"
    # check if URL contains the keyword sandbox
    if 'sandbox' in request.url_root:
        apache_root = "/analysistools-sandbox/"

    apache_tmp_dir = apache_root+"public_html/apps/LDlink/tmp/"

    # Ensure apache tmp directory exists
    if not os.path.exists(apache_tmp_dir):
	os.makedirs(apache_tmp_dir)
		
    #copy *<reference_no>.* to htodocs
    os.system("cp "+ tmp_dir+"*"+reference+".* "+apache_tmp_dir);

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

@app.route("/LDlinkRest/demoapp/add", methods=['POST'])
def restAdd():
    print type(request.args)
    for arg in request.args:
        print arg

    data = str(request.args)
    json_dumps = json.dumps(data)

    print "HI"
    first = request.args.get('first', False)
    second = request.form.get('second')
    test = request.form.get('test')
    print "Hi"
    print first
    print json_dumps
    return jsonify(success=True, data=json_dumps)

@app.route('/LDlinkRest/ldpair', methods = ['GET'])
def ldpair():
    # analysistools-sandbox.nci.nih.gov/LDlinkRest/test?snp1=rs2720460&snp2=rs11733615&pop=EUR&reference=28941
    # python LDpair.py rs2720460 rs11733615 EUR 38
    # r1 = '{"corr_alleles":["rs2720460(A) allele is correlated with rs11733615(C) allele","rs2720460(G) allele is correlated with rs11733615(T) allele"],"haplotypes":{"hap1":{"alleles":"AC","count":"576","frequency":"0.573"},"hap2":{"alleles":"GT","count":"361","frequency":"0.359"},"hap3":{"alleles":"GC","count":"42","frequency":"0.042"},"hap4":{"alleles":"AT","count":"27","frequency":"0.027"}},"snp1":{"allele_1":{"allele":"A","count":"603","frequency":"0.599"},"allele_2":{"allele":"G","count":"403","frequency":"0.401"},"coord":"chr4:104054686","rsnum":"rs2720460"},"snp2":{"allele_1":{"allele":"C","count":"618","frequency":"0.614"},"allele_2":{"allele":"T","count":"388","frequency":"0.386"},"coord":"chr4:104157164","rsnum":"rs11733615"},"statistics":{"chisq":"738.354","d_prime":"0.8839","p":"0.0","r2":"0.734"},"two_by_two":{"cells":{"11":"576","12":"27","21":"42","22":"361"},"total":"1006"}'

    print
    print 'Execute TEST'
    print 'Gathering Variables from url'
    var1 = request.args.get('var1', False)
    var2 = request.args.get('var2', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    # reference = "939393"
    print 'var1: ' + var1
    print 'var2: ' + var2
    print 'pop: ' + pop
    print 'request: ' + reference
    print
    out_json = calculate_pair(var1, var2, pop, reference)
    mimetype = 'application/json'

    return current_app.response_class(out_json, mimetype=mimetype)

@app.route('/LDlinkRest/ldproxy', methods = ['GET'])

def ldproxy():
    print
    print 'Execute ldproxy'
    print 'Gathering Variables from url'
    var = request.args.get('var', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    r2_d = request.args.get('r2_d', False)

    print 'var: ' + var
    print 'pop: ' + pop
    print 'request: ' + reference
    print 'r2_d: ' + r2_d
    print

    #out_json,out_script,out_div=calculate_proxy(snp, pop, reference)
    out_script,out_div = calculate_proxy(var, pop, reference, r2_d)

    copy_output_files(reference)

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
    r2_d = request.args.get('r2_d', False)
    print 'snps: ' + snps
    print 'pop: ' + pop
    print 'request: ' + reference
    print 'r2_d: ' + r2_d

    snplst = tmp_dir+'snps'+reference+'.txt'
    print 'snplst: '+snplst

    f = open(snplst, 'w')
    f.write(snps)
    f.close()

    out_script,out_div = calculate_matrix(snplst,pop,reference,r2_d)

    copy_output_files(reference)
    return out_script+"\n "+out_div


@app.route('/LDlinkRest/ldhap', methods = ['GET'])
def ldhap():

    print
    print 'Execute ldhap'
    print 'Gathering Variables from url'

    snps = request.args.get('snps', False)
    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    print 'snps: ' + snps
    print 'pop: ' + pop
    print 'request: ' + reference

    snplst = tmp_dir+'snps'+reference+'.txt'
    print 'snplst: '+snplst

    f = open(snplst, 'w')
    f.write(snps)
    f.close()

    out_json = calculate_hap(snplst,pop,reference)
    copy_output_files(reference)

    return out_json

@app.route('/LDlinkRest/snpclip', methods = ['POST'])
def snpclip():

    #Command line example
    #[ncianalysis@nciws-d275-v LDlinkc]$ python ./SNPclip.py LDlink-rs-numbers.txt YRI 333

    #print
    #print 'Execute snpclip'
    #print 'Gathering Variables from url'

    data = json.loads(request.stream.read())
    print 'Execute snpclip'
    print 'Gathering Variables from url'
    print data
    snps = data['snps']
    pop = data['pop']
    r2_threshold = data['r2_threshold']
    maf_threshold = data['maf_threshold']

    reference = request.args.get('reference', False)
    #print 'snps: ' + snps
    #print 'pop: ' + pop
    #print 'request: ' + reference
    #print 'r2_threshold: ' + r2_threshold
    #print 'maf_threshold: ' + maf_threshold

    snpfile = str(tmp_dir+'snps'+reference+'.txt')
    #print 'snpfile: '+snpfile
    snplist = snps.splitlines()

    f = open(snpfile, 'w')
    for s in snplist:
    	s = s.lstrip()
        if(s[:2].lower() == 'rs'):
            f.write(s.lower()+'\n')

    f.close()
    (snps,snp_list,details) = calculate_clip(snpfile,pop,reference,float(r2_threshold),float(maf_threshold))
    #(snps,snp_list,details) = calculate_clip(snplst,pop,reference)

    #print "Here is the DETAILS"
    #print type(details)
    
    clip={}
    clip["snp_list"] = snp_list
    clip["details"] = details
    #write the snp_list file
    #print json.dumps(details, sort_keys=True, indent=2)

    #SNP List file    
    f = open('tmp/snp_list'+reference+'.txt', 'w')
    for rs_number in snp_list:
        f.write(rs_number+'\n')

    f.close()
    #print "SNP clipped file contents"
    #with open('tmp/snp_list'+reference+'.txt', 'r') as fin:
    #    print fin.read()

    #Detail file
    #print "details . type"
    #print type(details)

    f = open('tmp/details'+reference+'.txt', 'w')
    f.write("RS Number\tPosition\tAlleles\tDetails\n")
    if(type(details) is collections.OrderedDict):
        for snp in snps:
            f.write(snp[0]+"\t"+"\t".join(details[snp[0]]))
            f.write("\n")
#        for key, value in details.iteritems() :
#            f.write(key+"\t")
#            f.write(value[0]+"\t"+value[1]+"\t"+value[2]+"\n")

    f.close()

    #for key, value in details.iteritems() :
    #    print(key+"\t"+value[0]+"\t"+value[1]+"\t"+value[2])

    copy_output_files(reference)

    out_json = json.dumps(clip, sort_keys=False)
    mimetype = 'application/json'

    return current_app.response_class(out_json, mimetype=mimetype)


@app.route('/LDlinkRest/snpchip', methods = ['GET', 'POST'])
def snpchip():

    #Command line example
    #[ncianalysis@nciws-d275-v LDlinkc]$ python ./SNPclip.py LDlink-rs-numbers.txt YRI 333
    print "Hello CHIP"
    print
    print 'Execute snpchip'
    print 'Gathering Variables from url'

    snps = request.args.get('snps', False)
    platforms = request.args.get('platforms', False)
    reference = request.args.get('reference', False)
    print 'snps: ' + snps
    print 'platforms: ' + platforms
    print 'request: ' + reference

    snplst = tmp_dir+'snps'+reference+'.txt'
    print 'snplst: '+snplst

    f = open(snplst, 'w')
    f.write(snps)
    f.close()

    #snp_chip = calculate_chip(snplst,platforms,reference)
    snp_chip = calculate_chip(snplst,platforms,reference)

    chip={}
    chip["snp_chip"] = snp_chip

    copy_output_files(reference)

    #out_json = json.dumps(chip, sort_keys=True, indent=2)
    out_json = json.dumps(snp_chip, sort_keys=True, indent=2)

    mimetype = 'application/json'

    return current_app.response_class(out_json, mimetype=mimetype)


@app.route('/LDlinkRest/snpchip_platforms', methods = ['GET'])
def snpchip_platforms():
    print "Retrieve SNPchip Platforms"

    return get_platform_request()


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

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number", default="9982", help="Sets the Port")
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number);

    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, debug = True)
