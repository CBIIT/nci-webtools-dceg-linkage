import sys
import json
import yaml
import requests

with open('../../LDlink/config.yml', 'r') as yml_file:
    config = yaml.load(yml_file)
opensearch_endpoint = config['aws']['opensearch_endpoint']
opensearch_user = config['aws']['opensearch_user']
opensearch_password = config['aws']['opensearch_password']

print("opensearch_endpoint", opensearch_endpoint)
print("opensearch_user", opensearch_user)
print("opensearch_password", opensearch_password)

filename = sys.argv[1]
filename_output = "platforms_insert.json"
print("filename", filename)
print("filename_output", filename_output)

with open(filename, "r") as f_r:
    with open(filename_output, "a") as f_w:
        for line in f_r:
            index_operation = {
                "index": {}
            }
            line_document = json.loads(line)
            print(line_document)
            f_w.write(json.dumps(index_operation) + "\n")
            f_w.write(json.dumps({
                "platform": line_document["platform"],
                "code": line_document["code"]
            }) + "\n")

_index = "platforms"
_type = "_doc"
insert_type = "_bulk"

url = opensearch_endpoint + "/" + _index + "/" + _type + "/" + insert_type

print("curl -XPOST -u '%s:%s' '%s' --data-binary @%s -H 'Content-Type: application/json'" % (opensearch_user, opensearch_password, url, filename_output))
