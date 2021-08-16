import boto3
import botocore
import yaml
from pymongo import MongoClient
# from bson import json_util

# retrieve config
with open('config.yml', 'r') as f:
    config = yaml.load(f)
aws_info = config['aws']
env = config['env']
api_mongo_addr = config['api']['api_mongo_addr']
mongo_username = config['database']['mongo_user_readonly']
mongo_password = config['database']['mongo_password']
mongo_port = config['database']['mongo_port']

def checkS3File(aws_info, bucket, filePath):
    if ('aws_access_key_id' in aws_info and len(aws_info['aws_access_key_id']) > 0 and 'aws_secret_access_key' in aws_info and len(aws_info['aws_secret_access_key']) > 0):
        session = boto3.Session(
            aws_access_key_id=aws_info['aws_access_key_id'],
            aws_secret_access_key=aws_info['aws_secret_access_key'],
        )
        s3 = session.resource('s3')
    else: 
        s3 = boto3.resource('s3')
    try:
        s3.Object(bucket, filePath).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            return False
    else: 
        return True

def retrieveAWSCredentials():
    if ('aws_access_key_id' in aws_info and len(aws_info['aws_access_key_id']) > 0 and 'aws_secret_access_key' in aws_info and len(aws_info['aws_secret_access_key']) > 0):
        export_s3_keys = "export AWS_ACCESS_KEY_ID=%s; export AWS_SECRET_ACCESS_KEY=%s;" % (aws_info['aws_access_key_id'], aws_info['aws_secret_access_key'])
    else:
        # retrieve aws credentials here
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        export_s3_keys = "export AWS_ACCESS_KEY_ID=%s; export AWS_SECRET_ACCESS_KEY=%s; export AWS_SESSION_TOKEN=%s;" % (credentials.access_key, credentials.secret_key, credentials.token)
    return export_s3_keys

def connectMongoDBReadOnly(web):
    # Connect to 'api_mongo_addr' MongoDB endpoint if app started locally (specified in config.yml)
    if env == 'local':
        mongo_host = api_mongo_addr
    else: 
        mongo_host = 'localhost'
    if web:
        client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host + '/admin', mongo_port)
    else:
        if env == 'local':
            client = MongoClient('mongodb://' + mongo_username + ':' + mongo_password + '@' + mongo_host + '/admin', mongo_port)
        else:
            client = MongoClient('localhost', mongo_port)
    db = client["LDLink"]
    return db