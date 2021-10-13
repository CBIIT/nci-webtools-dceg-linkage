#LOGGER.PY
import yaml
import logging
import os
import sys

# retrieve config
with open('config.yml', 'r') as f:
    config = yaml.load(f)
log_dir = config['data']['log_dir']

logging.basicConfig(filename=log_dir + "ldlink.log", 
                format='%(levelname)s : %(asctime)s : %(message)s', 
                filemode='w', level=logging.INFO, datefmt='%m-%d-%Y %I:%M:%S')
log = logging.getLogger("LDLink")
#log.propagate = False

def logDebug(message):
    log.debug(message)

def logInfo(message):
    log.info(message)

def logWarning(message):
    log.warning(message)

def logError(message):
    log.error(message)

def logCritical(message):
    log.critical(message)
