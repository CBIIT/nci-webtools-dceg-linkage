#!/usr/bin/env python
import QueueProcessor

def toQueue(email, batchFile, tokenId):
    client = Stomp(qp)

    data = json.dumps({ 
        "filepath": batchFile,
        "token": tokenId,
        "timestamp": time.strftime("%Y-%m-%d")
    })

    #opening connection to queue
    client.connect()
    client.send(qp.Q_NAME, data)
    client.disconnect()

    return jsonify({ message: "The batch process has begun. The results will be emailed to '{0}'".format(email) })

if __name__ == '__main__':
    from PropertyUtil import PropertyUtil
    qp = QueueProcessor
    qp.CONFIG_FILE = PropertyUtil(r"QueueConfig.ini")
    qp.PRODUCT_NAME = "LDlink Batch Processing Module"
    qp.Q_CONFIG = qp.CONFIG_FILE.getAsString('queue.config')
    qp.Q_NAME = qp.CONFIG_FILE.getAsString('queue.name')
    qp.Q_URL = qp.CONFIG_FILE.getAsString('queue.url')
    qp.Q_ERROR = qp.CONFIG_FILE.getAsString('queue.error.name')
    qp.MAIL_HOST= qp.CONFIG_FILE.getAsString('mail.host')