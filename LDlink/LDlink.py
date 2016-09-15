#!flask/bin/python
from flask import Flask, render_template, Response, abort, request, make_response, url_for, jsonify, redirect
from functools import wraps
from flask import current_app
from flask import jsonify
import sys, getopt
import cgi
import shutil
import os
import sys, traceback
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
from LDassoc import calculate_assoc
from SNPclip import calculate_clip

from SNPchip import *

#import os
#from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename
from werkzeug.debug import DebuggedApplication

tmp_dir = "./tmp/"
# Ensure tmp directory exists
if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

app = Flask(__name__, static_folder='', static_url_path='/')
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024
app.config['UPLOAD_DIR'] = os.path.join(os.getcwd(), 'tmp')
app.debug = True

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

def sendTraceback():
    custom = {}
    print "Unexpected error:", sys.exc_info()[0]
    traceback.print_exc()
    custom["error"] = "Raised when a generated error does not fall into any category."
    custom["traceback"] = traceback.format_exc()
    out_json = json.dumps(custom, sort_keys=False)
    return current_app.response_class(out_json, mimetype='application/json')

def sendJSON(inputString):
    out_json = json.dumps(inputString, sort_keys=False)
    return current_app.response_class(out_json, mimetype='application/json')

@app.route('/LDlinkRest/upload', methods=['POST'])
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
        #print dir(request.files)
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
            print 'file.filename '+file.filename
            print('file and allowed_file')
            filename = secure_filename(file.filename)
            print "About to SAVE file"
            print "filename = "+filename
            file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
            return 'Hello. File was saved'
    #        print "FILE SAVED.  Alright!"
    #        return '{"status" : "File was saved"}'
    #print filename

    #message = fileUploadService.upload_file(request, 'ldassocFile', os.path.join(app.config['UPLOAD_DIR']))
    #return message
    #return 'No Success'


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
    try:
        out_json = calculate_pair(var1, var2, pop, reference)
    except:
        return sendTraceback()

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
    try:
        out_script,out_div = calculate_proxy(var, pop, reference, r2_d)
    except:
        return sendTraceback()


    #copy_output_files(reference)

    return out_script+"\n "+out_div

@app.route('/LDlinkRest/ldmatrix', methods = ['GET'])
def ldmatrix():

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

    try:
        out_script,out_div = calculate_matrix(snplst,pop,reference,r2_d)
    except:
        return sendTraceback()

    #copy_output_files(reference)
    return out_script+"\n "+out_div


@app.route('/LDlinkRest/ldhap', methods = ['GET'])
def ldhap():

    print
    print 'Execute ldhap'
    print 'working'
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

    try:
        out_json = calculate_hap(snplst,pop,reference)
    except:
        return sendTraceback()

    #copy_output_files(reference)

    return sendJSON(out_json)

@app.route('/LDlinkRest/snpclip', methods = ['POST'])
def snpclip():

    #Command line example
    #[ncianalysis@nciws-d275-v LDlinkc]$ python ./SNPclip.py LDlink-rs-numbers.txt YRI 333
    mimetype = 'application/json'
    data = json.loads(request.stream.read())
    print 'Execute snpclip'
    snps = data['snps']
    pop = data['pop']
    r2_threshold = data['r2_threshold']
    maf_threshold = data['maf_threshold']

    reference = str(data['reference'])

    snpfile = str(tmp_dir+'snps'+reference+'.txt')
    snplist = snps.splitlines()

    f = open(snpfile, 'w')
    for s in snplist:
    	s = s.lstrip()
        if(s[:2].lower() == 'rs'):
            f.write(s.lower()+'\n')

    f.close()

    clip={}

    try:
        (snps,snp_list,details) = calculate_clip(snpfile,pop,reference,float(r2_threshold),float(maf_threshold))
    except:
        return sendTraceback()

    clip["snp_list"] = snp_list
    clip["details"] = details
    clip["snps"] = snps
    clip["filtered"] = collections.OrderedDict()

    # Print output
    with open(tmp_dir+"clip"+reference+".json") as f:
        json_dict=json.load(f)

    try:
        json_dict["error"]
    except KeyError:
        #print ""
        print "LD Thinned SNP list ("+pop+"):"
        for snp in snp_list:
            print snp

        print "The snps.."
        for snp in snps:
            print snp
        
        print ""
        print "RS Number\tPosition\tAlleles\tDetails"
        for snp in snps:
            print snp[0]+"\t"+"\t".join(details[snp[0]])
            clip["filtered"][snp[0]] =details[snp[0]]

        try:
            json_dict["warning"]

        except KeyError:
            print ""
        else:
            print ""
            print "WARNING: "+json_dict["warning"]+"!"
            print ""
            clip["warning"] = json_dict["warning"]

    else:
        print ""
        print json_dict["error"]
        print ""
        clip["error"] = json_dict["error"]

    #SNP List file    
    f = open('tmp/snp_list'+reference+'.txt', 'w')
    for rs_number in snp_list:
        f.write(rs_number+'\n')

    f.close()

    f = open('tmp/details'+reference+'.txt', 'w')
    f.write("RS Number\tPosition\tAlleles\tDetails\n")
    if(type(details) is collections.OrderedDict):
        for snp in snps:
            f.write(snp[0]+"\t"+"\t".join(details[snp[0]]))
            f.write("\n")

    f.close()
    #copy_output_files(reference)
    out_json = json.dumps(clip, sort_keys=False)
    return current_app.response_class(out_json, mimetype=mimetype)


@app.route('/LDlinkRest/snpchip', methods = ['GET', 'POST'])
def snpchip():

    #Command line example
    #[ncianalysis@nciws-d275-v LDlinkc]$ python ./SNPclip.py LDlink-rs-numbers.txt YRI 333
    print "snpChip"

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

    try:
        snp_chip = calculate_chip(snplst,platforms,reference)
    except:
        return sendTraceback()

    chip={}
    chip["snp_chip"] = snp_chip
    #copy_output_files(reference)
    out_json = json.dumps(snp_chip, sort_keys=True, indent=2)

    return current_app.response_class(out_json, mimetype='application/json')


@app.route('/LDlinkRest/snpchip_platforms', methods = ['GET'])
def snpchip_platforms():
    print "Retrieve SNPchip Platforms"
    return get_platform_request()

@app.route('/LDlinkRest/ldassoc', methods = ['GET'])
def ldassoc():

    myargs = argparse.Namespace()

    print "LDassoc"
    print 'Gathering Variables from url'

    print type(request.args)
    for arg in request.args:
        print arg

    data = str(request.args)
    json_dumps = json.dumps(data)

    pop = request.args.get('pop', False)
    reference = request.args.get('reference', False)
    filename = request.args.get('filename', False)
    matrixVariable = request.args.get('matrixVariable')
    region = request.args.get('calculateRegion')

    myargs.dprime = bool(request.args.get("dprime") == "True")
    print "dprime: "+str(myargs.dprime)

    #Column settings
    myargs.chr = str(request.args.get('columns[chromosome]'))
    myargs.bp = str(request.args.get('columns[position]'))
    myargs.pval = str(request.args.get('columns[pvalue]'))

    print "myargs:"
    print type(myargs.chr)
    #regionValues = json.loads(request.args.get('region'))
    #variantValues = json.loads(request.args.get('variant'))
    #columns = json.loads(request.args.get('columns'))
    filename = "/local/content/ldlink/data/assoc/meta_assoc.meta"

    print 'filename: ' + filename
    print 'region: ' + region
    print 'pop: ' + pop
    print 'reference: ' + reference
    print 'region: ' + region

    if region == "variant":
        print "Region is variant"
        myargs.origin = "rs234"

    if region == "gene":
        print "Region is gene"
        myargs.origin = "rs234"

    if region == "region":
        print "Region is region"
        myargs.start = str(request.args.get('region[start]'))
        myargs.end = str(request.args.get('region[end]'))
        myargs.window = str(request.args.get('region[index]'))
        myargs.name = "hello"
        myargs.origin = str(request.args.get('region[index]'))

    myargs.window=None

    try:
        out_json = calculate_assoc(filename,region,pop,reference,myargs)
    except:
        return sendTraceback()

    #copy_output_files(reference)
    print "out_json:"
    print out_json

    return sendJSON(out_json)


import argparse
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number", default="9982", help="Sets the Port")
    parser.add_argument("-d", dest="debug", default="False", help="Sets the Debugging Option")
    # Default port is production value; prod,stage,dev = 9982, sandbox=9983
    args = parser.parse_args()
    port_num = int(args.port_number);
    debugger = args.debug == 'True'

    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, debug = debugger,use_evalex = False)
    application = DebuggedApplication(app, True)
