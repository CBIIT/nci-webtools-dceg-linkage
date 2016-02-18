import os
import re
import string
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from socket import gethostname


app = Flask(__name__)

#with open('test.r') as fh:
#    rcode = os.linesep.join(line.strip() for line in fh)
#    wrapper = SignatureTranslatedAnonymousPackage(rcode, "wrapper")
    
@app.route('/')
def index():
    return return_template('index.html')

    
@app.route("/demoapp/add", methods=['POST'])
def restAdd():
    print "HI"
    first = request.form.get('first')
    second = request.form.get('second')
    test = request.form.get('test')
    print "HIi"
    return "aa"

 #   return wrapper.addNumbers(first, second)[0]

@app.route('/demoapp/testGET', methods=['GET'])
def testGET():
    print request.args

import argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port_number", default="9999", help="Sets the Port") 
    # Default port is production value; prod, stage, dev = 8040, sandbox = 9040
    args = parser.parse_args()
    port_num = int(args.port_number)

    hostname = gethostname()
    app.run(host='0.0.0.0', port=port_num, debug = False) 
