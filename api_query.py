import argparse
import requests
import sys


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Query depsearch online')
    parser.add_argument('--url', default="http://bionlp-www.utu.fi/dep_search_api", help='The base URL of the service to query. Default: %(default)s')
    parser.add_argument('-d', '--db', required=True, help='The treebank to use. One of those visible on http://bionlp-www.utu.fi/dep_search.')
    parser.add_argument('-m', '--retmax', default=1000, help='How many trees to get?')
    parser.add_argument('query', nargs=1, help='The query to issue')
    args = parser.parse_args()
    
    r=requests.get(args.url,params={u"db":args.db, u"search":args.query, u"retmax":args.retmax},stream=True)
    for line in r.iter_lines():
        print line
