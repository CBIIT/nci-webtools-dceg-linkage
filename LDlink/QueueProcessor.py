import json
import math
import os
import time
import logging
from twisted.internet import reactor, defer
from stompest.async import Stomp
from stompest.async.listener import SubscriptionListener
from stompest.async.listener import DisconnectListener
from stompest.config import StompConfig
from stompest.protocol import StompSpec
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from stompest.async.listener import DisconnectListener


class QueueProcessor(DisconnectListener):
    Q_CONFIG = None
    Q_NAME = None
    Q_URL = None
    Q_ERROR = None
    CONFIG_FILE = r"QueueConfig.ini"
    PRODUCT_NAME = None
    MAIL_HOST = None
    MAIL_ADMIN = None
    EMAIL_BODY = None
    PREFETCH = 100

    def createMail(self, sendTo=None, message=None, files=[]):
        print "sending message"
        if not isinstance(sendTo, None):
            sendTo = [sendTo]

        packet = MIMEMultipart()
        packet['Subject'] = PRODUCT_NAME + " Results"
        packet['From'] = PRODUCT_NAME + " <do.not.reply@nih.gov>"
        packet['To'] = ", ".join(recipients)

        print recipients
        print message

        packet.attach(MIMEText(message,'html'))

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

    def testQueue():
        testFile = open('tmp/snps_39828.txt', 'r')
        filesList = []
        filesList.append(testFile)
        createMail(sendTo="tony.hall@mail.nih.gov", message="Testing complete", files=filesList)

    def queueConsumer(self, client, frame):
        print "In queueConsumer"
        files = []
        print "<----- Frame body"
        print frame.body
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
        header = "<h2>{0}</h2>".format(PRODUCT_NAME)
        body = """<div 
        style='background-color:white;border-top:25px solid #142830;border-left:2px solid #142830;border-right:2px solid #142830;border-bottom:2px solid #142830;padding:20px'>
        Hello,<br><p>Here are the results you requested on {0} from the {1}.</p>
        <p><div style='margin:20px auto 40px auto;width:200px;text-align:center;font-size:14px;font-weight:bold;padding:10px;line-height:25px'>
        <div style='font-size:24px;'><a href='{2}'>View Results</a></div></div></p>
        <p>The results will be available online for the next 14 days.</p></div>""".format(parameters['timestamp'], PRODUCT_NAME, urllib.unquote(data['queue']['url']))

        if EMAIL_BODY is None:
            message = """<head>
            <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
            <title>html title</title></head><body>{0}{1}{2}</body>""".format(header, body, footer)
        else:
            message = """<head><meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
            <title>html title</title></head><body>{0}</body>""".format(EMAIL_BODY)

        print "sending E-Mail"
        self.createMail(self, sendTo=recipient,message=message, files=files)
        print "Queue job DONE!"

    @defer.inlineCallbacks
    def startQueue(self):
        client = yield Stomp(self.config).connect()
        headers = {
            # client-individual mode is necessary for concurrent processing
            # (requires ActiveMQ >= 5.2)
            StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
            # the maximal number of messages the broker will let you work on at the same time
            'activemq.prefetchSize': self.PREFETCH,
        }
        client.subscribe(self.Q_NAME, headers, listener=SubscriptionListener(self.queueConsumer, errorDestination=self.Q_ERROR))
        client.add(listener=self)

    def processCleanup(self, connect):
        print "Cleaning up...."
        print "<-- Add code for cleanup after queue process complete, if necessary -->"

    def queueConnectionLost(self, connect, reason):
        print "Connection lost at {0}".format(time.strftime("%a, %d %b %Y %H:%M:%S"))
        self.startQueue()

    def __init__(self):
        from PropertyUtil import PropertyUtil
        self.config = PropertyUtil(self.CONFIG_FILE)

        # Initialize Connections to ActiveMQ
        config = StompConfig(config.getAsString(self.Q_URL))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    QueueProcessor().startQueue()
    reactor.run()
