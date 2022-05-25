#!/usr/bin/env python3
import yaml


# Set data directories using config.yml
def get_config(path='config.yml'):
    param_list = {}
    with open(path, 'r') as yml_file:
        config = yaml.safe_load(yml_file)
    
    param_list['env'] = config['env']
    param_list['dbsnp_version'] = config['data']['dbsnp_version']
    param_list['population_samples_dir'] = config['data']['population_samples_dir']
    param_list['ldassoc_example_dir'] =  config['data']['ldassoc_example_dir'] 
    param_list['data_dir'] = config['data']['data_dir']
    param_list['tmp_dir'] = config['data']['tmp_dir']
    param_list['genotypes_dir'] = config['data']['genotypes_dir']
    param_list['ldtrait_src'] = config['data']['ldtrait_src']
    param_list['aws_info'] = config['aws']
    param_list['num_subprocesses'] = config['performance']['num_subprocesses']
    
   
    return (param_list)

def get_config_admin():
    param_list = {}
    with open('config.yml', 'r') as yml_file:
        config = yaml.safe_load(yml_file)
    
    param_list['api_mongo_addr'] = config['database']['api_mongo_addr']
    param_list['mongo_username'] = config['database']['mongo_user_readonly']
    param_list['mongo_username_api'] = config['database']['mongo_user_api']
    param_list['mongo_password'] = config['database']['mongo_password']
    param_list['mongo_port'] = config['database']['mongo_port']
    param_list['email_account'] = config['api']['email_account']
        
    param_list['require_token'] = config['api']['require_token']
    param_list['token_expiration'] = config['api']['token_expiration']
    param_list['token_expiration_days'] = config['api']['token_expiration_days']
    param_list['log_dir'] = config['log']['log_dir']
    param_list['log_filename'] = config['log']['filename']
    param_list['log_level'] = config['log']['log_level']

    return (param_list)
