import yaml
import logging
import logging.handlers
import re

with open('config.yml', 'r') as f:
    config = yaml.load(f)

log_dir = config['log']['log_dir']
log_filename = config['log']['filename']
log_level = config['log']['log_level']

logger = logging.getLogger('LDlink')

# Add the log message handler to the logger
handler = logging.handlers.TimedRotatingFileHandler(log_dir + log_filename, when='M', interval=2, backupCount=0)
handler.suffix = "%Y-%m-%d_%H:%M:%S.backup"
logFormatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(logFormatter)

logger.addHandler(handler)

if (log_level == 'DEBUG'):
    logger.setLevel(logging.DEBUG)
elif (log_level == 'INFO'):
    logger.setLevel(logging.INFO)
elif (log_level == 'WARNING'):
    logger.setLevel(logging.WARNING)
elif (log_level == 'ERROR'):
    logger.setLevel(logging.ERROR)
elif (log_level == 'CRITICAL'):
    logger.setLevel(logging.CRITICAL)
else:
    logger.setLevel(logging.DEBUG)