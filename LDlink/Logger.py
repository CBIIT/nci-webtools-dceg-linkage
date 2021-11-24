import yaml
import logging
import logging.handlers

with open('config.yml', 'r') as f:
    config = yaml.load(f)

log_dir = config['log']['log_dir']
log_filename = config['log']['filename']
log_level = config['log']['log_level']

logger = logging.getLogger('LDlink')

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

# Add the log message handler to the logger
handler = logging.handlers.TimedRotatingFileHandler(log_dir + log_filename, when='M',  interval=10)
handler.suffix = "%m-%d-%y_%H:%M:%S"
logFormatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%m-%d-%Y %I:%M:%S')
handler.setFormatter(logFormatter)

logger.addHandler(handler)