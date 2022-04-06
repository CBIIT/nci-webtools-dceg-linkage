#!/usr/bin/env python3
import yaml


# Set data directories using config.yml
def get_config():
    param_list = {}
    with open('config.yml', 'r') as yml_file:
        config = yaml.safe_load(yml_file)
    
    param_list['env'] = config['env']
    param_list['dbsnp_version'] = config['data']['dbsnp_version']
    param_list['population_samples_dir'] = config['data']['population_samples_dir']
    param_list['data_dir'] = config['data']['data_dir']
    param_list['tmp_dir'] = config['data']['tmp_dir']
    param_list['genotypes_dir'] = config['data']['genotypes_dir']
    param_list['ldtrait_src'] = config['data']['ldtrait_src']
    param_list['aws_info'] = config['aws']
    param_list['num_subprocesses'] = config['performance']['num_subprocesses']
   

    return (param_list)