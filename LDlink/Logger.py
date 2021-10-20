#LOGGER.PY
import yaml
import logging
import os
import sys
import datetime
from logging.handlers import TimedRotatingFileHandler

# retrieve config
with open('config.yml', 'r') as f:
    config = yaml.load(f)

log_dir = config['log']['log_dir']
logFilename = config['log']['filename']
logLevel = config['log']['log_level']
today = datetime.datetime.now()
timestamp = today.strftime("%m-%d-%y_%H:%M:%S")

if (logLevel == 'DEBUG'):
    logLevel = logging.DEBUG
elif (logLevel == 'INFO'):
    logLevel = logging.INFO
elif (logLevel == 'WARNING'):
    logLevel = logging.WARNING
elif (logLevel == 'ERROR'):
    logLevel = logging.ERROR
elif (logLevel == 'CRITICAL'):
    logLevel = logging.CRITICAL
else:
    logLevel = logging.DEBUG

logging.basicConfig(filename=log_dir + logFilename + "." + timestamp, 
                format='%(levelname)s : %(asctime)s : %(message)s', 
                filemode='w', level=logLevel, datefmt='%m-%d-%Y %I:%M:%S')
log = logging.getLogger("LDLink")
#log.propagate = False

#handler to rotate log file at specified time
handler = TimedRotatingFileHandler(logFilename, when="midnight", interval=1)
handler.suffix = "%Y%m%d"
log.addHandler(handler)

def logDebug(message):
    log.debug(message)

def logInfo(message):
    log.info(message)

def logWarning(message):
    log.warning(message)

def logError(message):
    log.error(message, exc_info=True)

def logCritical(message):
    log.critical(message)
