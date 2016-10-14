#!/usr/bin/env python
import json
import logging

from stompest.async import Stomp
from stompest.config import StompConfig
from stompest.protocol import StompSpec
from QueueProcessor import QueueProcessor
import os, sys, time
from flask import jsonify, json

def toQueue(email, tokenId):
    # print "in toQueue"
    resp = ""
    try:
        qp = QueueProcessor(
            PRODUCT_NAME = "LDlink Batch Processing Module",
            CONFIG_FILE = r"QueueConfig.ini",
            Q_NAME = 'queue.name',
            Q_URL = 'queue.url',
            Q_PORT = 'queue.port',
            Q_ERROR = 'queue.error.name',
            MAIL_HOST = 'mail.host',
            MAIL_ADMIN = 'mail.admin')

        batchFile = open(os.path.join('tmp', tokenId))
        # print batchFile

        ts = time.strftime("%Y-%m-%d")
        data = json.dumps({ 
            "filepath": batchFile.name,
            "token": tokenId,
            "timestamp": ts
        })

        print "before client connect"
        print "Stomp( {0}, {1} )".format(qp.Q_URL, qp.Q_PORT)

        print type(qp.Q_URL)
        print type(qp.Q_PORT)
        
        client = Stomp("tcp://{0}:{1}".format(qp.Q_URL, qp.Q_PORT))

        #opening connection to queue
        client.connect()
        client.send(qp.Q_NAME, data)
        client.disconnect()

        return jsonify({ "message": "The batch process has begun. The results will be emailed to " + email })
    except Exception, e:
        errorType, error, traceback = sys.exc_info()
        print errorType
        print error
        print traceback
        print e.args[1:]
        resp = jsonify({ "message" : e.args })
        resp.status_code = 400
        return resp