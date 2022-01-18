from opensearchpy import OpenSearch
import yaml
import requests

with open('../../LDlink/config.yml', 'r') as yml_file:
    config = yaml.load(yml_file)
opensearch_endpoint = config['aws']['opensearch_endpoint']
opensearch_user = config['aws']['opensearch_user']
opensearch_password = config['aws']['opensearch_password']

_index = "platforms"

# client = OpenSearch(
#     hosts = [{'host': opensearch_endpoint}],
#     http_auth = (opensearch_user, opensearch_password),
#     use_ssl = True,
#     verify_certs = True
#     # connection_class = RequestsHttpConnection
# )

# # Search for the document.
# q = ''
# query = {
#   'size': 100,
#   'query': {
#     'multi_match': {
#       'query': q,
#     #   'fields': ['title^2', 'director']
#     }
#   }
# }

# response = client.search(
#     body = query,
#     index = _index
# )

# print("response", response)

url = opensearch_endpoint + "/" + _index + "/" + "_search?&size=100&pretty&filter_path=hits.hits._source"
r = requests.get(url, auth=(opensearch_user, opensearch_password)) # requests.get, post, and delete have similar syntax

print(r.text)