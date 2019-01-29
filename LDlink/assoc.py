#!/usr/local/Python-2.7.2/bin/python
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

tmp_dir = "./tmp/"
# Ensure tmp directory exists
def sendTraceback():
	custom = {}
	print "Unexpected error:", sys.exc_info()[0]
	traceback.print_exc()
	custom["error"] = "Raised when a generated error does not fall into any category."
	custom["traceback"] = traceback.format_exc()
	out_json = json.dumps(custom, sort_keys=False)
	print out_json

def sendJSON(inputString):
	out_json = json.dumps(inputString, sort_keys=False)
	print out_json


def main():
	print "This line will be printed."
	request = "35872"
	pop = "ALL"
	#reference = request.args.get('reference', False)

	print 'pop: ' + pop
	print 'request: ' + request

	snplst = tmp_dir+'snps'+request+'.txt'
	print 'snplst: '+snplst
	file = "meta_assoc.meta"
	region = "variant"
	args = {}
	args["origin"] = "rs1231"
	print args
	try:
		out_json = calculate_hap(snplst,pop,request, false)
		#out_json = calculate_assoc(file,region,pop,request,args)
	except:
		return sendTraceback()

	#copy_output_files(reference)

	return sendJSON(out_json)


if __name__ == "__main__":
	main()

