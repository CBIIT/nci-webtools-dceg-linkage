#!/usr/bin/env python3
import datetime
import dateutil.parser
from os import environ
from dotenv import load_dotenv

load_dotenv()

# config_path='.env'
# config_abs_path= '/analysistools/public_html/apps/LDlink/app/config.yml'
# Set data directories using config.yml

def get_config():
    config = {}
    config['env'] = environ.get('ENV')
    config['base_url'] = environ.get('BASE_URL')
    config['log_level'] = environ.get('LOG_LEVEL')
    config['num_subprocesses'] = int(environ.get('NUM_SUBPROCESSES'))

    config['dbsnp_version'] = environ.get('DBSNP_VERSION')
    config['s3_bucket'] = environ.get('S3_BUCKET')
    config['s3_bucket_data_dir'] = environ.get('S3_BUCKET_DATA_DIR')
    config['data_dir'] = environ.get('DATA_DIR')
    config['tmp_dir'] = environ.get('TMP_DIR')
    config['ldassoc_example_dir'] = environ.get('LDASSOC_EXAMPLE_DIR')
    config['population_samples_dir'] = environ.get('POPULATION_SAMPLES_DIR')
    config['genotypes_dir'] = environ.get('GENOTYPES_DIR')
    config['ldtrait_src'] = environ.get('LDTRAIT_SRC')

    config['mongodb_host'] = environ.get('MONGODB_HOST')
    config['mongodb_port'] = int(environ.get('MONGODB_PORT'))
    config['mongodb_database'] = environ.get('MONGODB_DATABASE')
    config['mongodb_username'] = environ.get('MONGODB_USERNAME')
    config['mongodb_password'] = environ.get('MONGODB_PASSWORD')

    config['require_token'] = environ.get('REQUIRE_TOKEN') == 'YES'
    config['token_expiration'] = environ.get('TOKEN_EXPIRATION') == 'YES'
    config['token_expiration_days'] = int(environ.get('TOKEN_EXPIRATION_DAYS'))
    config['restrict_concurrency'] = environ.get('RESTRICT_CONCURRENCY') == 'YES'
    config['token_lock_timeout'] = int(environ.get('TOKEN_LOCK_TIMEOUT', 900))

    config['email_smtp_host'] = environ.get('EMAIL_SMTP_HOST')
    config['email_admin'] = environ.get('EMAIL_ADMIN')
    config['email_superuser'] = environ.get('EMAIL_SUPERUSER')

    config['aws_info'] = {
        "bucket": environ.get('S3_BUCKET'),
        "data_subfolder": environ.get('S3_BUCKET_DATA_DIR')
    }
   
    return config

def array_split(arr, n):
    size, rem = divmod(len(arr), n)
    return [arr[i * size + min(i, rem):(i + 1) * size + min(i + 1, rem)] for i in range(n)]

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# unlock stale tokens at scheduled time
def unlock_stale_tokens(db, lock_timeout = 15 * 60):
    users = db.api_users
    # current datetime
    present = getDatetime()
    unlockTokens = []
    # look at each token
    for user in users.find():
        if "locked" in user:
            locked = user["locked"]
            if locked != 0 and locked != -1:
                if isinstance(locked, datetime.datetime):
                    diff = present - locked
                else:
                    diff = present - dateutil.parser.parse(locked, ignoretz=True)
                diffSeconds = (diff.seconds % 3600)
                # if token is locked for over 15 mins, unlock
                if diffSeconds > lock_timeout:
                    unlockTokens.append(user["token"])
    for token in unlockTokens:
        users.find_one_and_update({"token": token}, { "$set": {"locked": 0}})
