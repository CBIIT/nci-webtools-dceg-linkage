from LDcommon import connectMongoDBReadOnly
from flask import Flask

app = Flask(__name__)

@app.route("/LDlinkRest/ping", strict_slashes=False)
def ping():
    connectMongoDBReadOnly().command('ping')
    return "true"
