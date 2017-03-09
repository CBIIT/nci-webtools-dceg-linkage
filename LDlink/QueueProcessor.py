import json
import math
import os, sys

import rpy2.robjects as robjects
import smtplib
import time
import logging
import urllib
from stompest.async.listener import SubscriptionListener
from stompest.async.listener import DisconnectListener
from stompest.config import StompConfig
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twisted.internet import reactor, defer
from PropertyUtil import PropertyUtil
from flask import jsonify

class QueueProcessor(DisconnectListener):
    CONFIG_FILE = None
    Q_NAME = None
    Q_URL = None
    Q_PORT = None
    Q_ERROR = None
    MAIL_HOST = None
    MAIL_ADMIN = None
    EMAIL_BODY = None
    PREFETCH = 100
    PRODUCT_NAME = None

    # Initialize Connections to ActiveMQ
    QUEUE = None

    def createMail(self, sendTo=None, message=None, files=[]):
        try:
            print "sending message"
            recipients = []
            if sendTo is not None:
                recipients = [ sendTo ]

            packet = MIMEMultipart()
            packet['Subject'] = self.PRODUCT_NAME + " Results"
            packet['From'] = self.PRODUCT_NAME + " <do.not.reply@nih.gov>"
            packet['To'] = ", ".join(recipients)

            print sendTo
            print message

            packet.attach(MIMEText(message, 'html'))

            for file in files:
                with open(file,"rb") as openfile:
                    packet.attach(MIMEApplication(
                        openfile.read(),
                        Content_Disposition = 'attachment; filename="%s"' % os.path.basename(file),
                        Name = os.path.basename(file)
                    ))

            print self.MAIL_HOST
            smtp = smtplib.SMTP(self.MAIL_HOST)
            smtp.sendmail("do.not.reply@nih.gov", recipients, packet.as_string())
        except Exception, e:
            print "Error Type: {0} Error: {1} Trace: {2}".format(errorType, error, traceback)
            resp = jsonify({ "message": e.args })
            resp.status_code = 400

    def testQueue():
        try:
            print "testQueue"
            testFile = open('tmp/snps_39828.txt', 'r')
            filesList = []
            filesList.append(testFile)
            self.createMail(sendTo="tony.hall@mail.nih.gov", message="Testing complete", files=filesList)
        except Exception, e:
            print "Error Type: {0} Error: {1} Trace: {2}".format(errorType, error, traceback)
            resp = jsonify({ "message": e.args })
            resp.status_code = 400

    def queueConsumer(self, client, frame):
        resp = ""
        try:
            files = []
            print "<----- Frame body"
            print frame.body
            print frame.body.decode()
            parameters = json.loads(frame.body)

            print "<----------- Params"
            print parameters
            token = parameters['token']
            batchFilename = parameters['batchFile']
            recipient = parameters['recipientEmail']
            fname = os.path.join("tmp", batchFilename)
            timestamp = ['timestamp']

            print token
            print fname

            # --------------- THIS MAY CHANGE
            with open(fname) as content_file:
                contents = content_file.read()

            fileContents = json.loads(contents)
            print fileContents

            # Place calls to R scripts here
            #     rSource = robjects.r['source']('< WrapperFilename>')
            #     robjects.r['getFittedResultWrapper'](parameters['batchFile'], fileContents)
            print "After calculation"

            link = "<a href='{0}'> Here </a>".format(urllib.unquote(data['queue']['url']))
            header = "<h2>{0}</h2>".format(self.PRODUCT_NAME)
            body = """<div 
            style='background-color:white;border-top:25px solid #142830;border-left:2px solid #142830;border-right:2px solid #142830;border-bottom:2px solid #142830;padding:20px'>
            Hello,<br><p>Here are the results you requested on {0} from the {1}.</p>
            <p><div style='margin:20px auto 40px auto;width:200px;text-align:center;font-size:14px;font-weight:bold;padding:10px;line-height:25px'>
            <div style='font-size:24px;'><a href='{2}'>View Results</a></div></div></p>
            <p>The results will be available online for the next 14 days.</p></div>""".format(parameters['timestamp'], self.PRODUCT_NAME, urllib.unquote(data['queue']['url']))

            footer = """<div><p>(Note:  Please do not reply to this email. If you need assistance, please contact NCILDlinkWebAdmin@mail.nih.gov)</p></div>
            <div style="background-color:#ffffff;color:#888888;font-size:13px;line-height:17px;font-family:sans-serif;text-align:left">
              <p>
                  <strong>About<em>""" + self.PRODUCT_NAME + """</em></strong></em><br>
                  <!-- LDBatch E-Mail description -->
                  <strong>For more information, visit <a target="_blank" style="color:#888888" href="http://analysistools.nci.nih.gov">analysistools.nci.nih.gov/ldlink?tab=ldbatch</a>
                  </strong>
              </p>
              <p style="font-size:11px;color:#b0b0b0">If you did not request a calculation please ignore this email. Your privacy is important to us.  
              Please review our <a target="_blank" style="color:#b0b0b0" href="http://www.cancer.gov/policies/privacy-security">Privacy and Security Policy</a>.
              </p>
              <p align="center"><a href="http://cancercontrol.cancer.gov/">Division of Cancer Control & Population Sciences</a>, 
              <span style="white-space:nowrap">a Division of <a href="www.cancer.gov">National Cancer Institute</a></span><br>
              BG 9609 MSC 9760 | 9609 Medical Center Drive | Bethesda, MD 20892-9760 | <span style="white-space:nowrap"><a target="_blank" value="+18004006916" href="tel:1-800-422-6237">1-800-4-CANCER</a></span>
              </p></div>"""
            if self.EMAIL_BODY is None:
                message = """<head><meta http-equiv='Content-Type' content='text/html; charset=utf-8'><title>html title</title></head><body>{0}{1}{2}</body>""".format(header, body, footer)
            else:
                message = """<head><meta http-equiv='Content-Type' content='text/html; charset=utf-8'><title>html title</title></head><body>{0}</body>""".format(self.EMAIL_BODY)

            print "sending E-Mail"
            self.createMail(sendTo=data['queue']['email'],message=message, files=files)
            print "Queue job DONE!"
            resp = jsonify({ "message": "The batch process has begun. The results will be emailed to '" + recipient + "'" })
        except Exception, e:
            print "Error Type: {0} Error: {1} Trace: {2}".format(errorType, error, traceback)
            resp = jsonify({ "message": e.args })
            resp.status_code = 400
        finally:
            return resp

    @defer.inlineCallbacks
    def startQueue(self):
        try:
            print "in startQueue"

            if self.QUEUE is not None:
                conf = Stomp(self.QUEUE)
                client = yield conf.connect()
                print self.PREFETCH
                headers = {
                    # client-individual mode is necessary for concurrent processing
                    # (requires ActiveMQ >= 5.2)
                    StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
                    # the maximal number of messages the broker will let you work on at the same time
                    'activemq.prefetchSize': self.PREFETCH
                }
                client.subscribe(self.Q_NAME, headers, listener=SubscriptionListener(self.queueConsumer, errorDestination=self.Q_ERROR))
                client.add(listener=self)
        except Exception, e:
            errorType, error, traceback = sys.exc_info()
            print "Error Type: {0} Error: {1}".format(errorType, error)
            print traceback

    def processCleanup(self, connect):
        print "in proccessCleanup, Cleaning up...."
        print "<-- Add code for cleanup after queue process complete, if necessary -->"

    def queueConnectionLost(self, connect, reason):
        print "in queueConnectionLost, Connection lost at {0}".format(time.strftime("%a, %d %b %Y %H:%M:%S"))
        self.startQueue()

    def __init__(self, CONFIG_FILE=None, Q_NAME=None, Q_URL=None, Q_PORT=None, Q_ERROR=None, PRODUCT_NAME="", MAIL_HOST=None, MAIL_ADMIN=None, EMAIL_BODY=None, PREFETCH=100):
        print sys.argv[1:]

        self.CONFIG_FILE = CONFIG_FILE
        self.config = PropertyUtil(CONFIG_FILE)

        print "File: "
        print self.config

        # Initialize Connections to ActiveMQ
        self.QUEUE = StompConfig(self.config[Q_URL])
        self.Q_NAME = self.config[Q_NAME]
        self.Q_URL = self.config[Q_URL]
        self.Q_ERROR = self.config[Q_ERROR]
        self.MAIL_HOST = self.config[MAIL_HOST]
        self.MAIL_ADMIN = self.config[MAIL_ADMIN]

        self.PRODUCT_NAME = PRODUCT_NAME

        # self.EMAIL_BODY = self.CONFIG_FILE.getAsString(EMAIL_BODY)
        self.PREFETCH = int(PREFETCH)
        self.Q_PORT = int(self.config[Q_PORT])
            

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    QueueProcessor().startQueue()
    reactor.run()