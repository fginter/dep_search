#!/usr/bin/env python

import sys
import os.path
import subprocess

import flask

# App settings. IMPORTANT: set DEBUG = False for publicly accessible
# installations, the debug mode allows arbitrary code execution.
DEBUG = False
HOST = 'epsilon-it.utu.fi'
PORT = 5042
STATIC_PATH = '/static'
QUERY_PARAMETER = 'q'

# Template-related constants
INDEX_TEMPLATE = 'index.html'
RESULT_TEMPLATE = 'index.html'
SERVER_URL_PLACEHOLDER = '{{ SERVER_URL }}'
QUERY_PLACEHOLDER = '{{ QUERY }}'
CONTENT_START = '<!-- CONTENT-START -->'
CONTENT_END = '<!-- CONTENT-END -->'

# Visualization wrapping
visualization_start = '<pre><code class="conllu">'
visualization_end = '</code></pre>'

def server_url(host=HOST, port=PORT):
    url = '%s:%d' % (host, port)
    if not url.startswith('http://'):
        url = 'http://' + url # TODO do this properly
    return url

def perform_query(query):
    # sorry, this is pretty clumsy ...
    script_dir = os.path.dirname(os.path.realpath(__file__))
    query_cmd = os.path.join(script_dir, '..', 'query.py')

    #args = [query_cmd, '-d', 'tmp_data/*.db', '-m', '100', query]
    args = [query_cmd, '-d', '/mnt/ssd/sdata/all/*.db', '-m', 100, query]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    return out

def get_index(fn=INDEX_TEMPLATE):
    with open(fn) as f:
        return f.read()

def get_template(fn=RESULT_TEMPLATE):
    with open(fn) as f:
        return f.read()

def fill_template(template, content, query=''):
    # TODO: use jinja
    assert CONTENT_START in template
    assert CONTENT_END in template
    header = template[:template.find(CONTENT_START)]
    trailer = template[template.find(CONTENT_END):]
    filled = header + content + trailer
    filled = filled.replace(SERVER_URL_PLACEHOLDER, server_url())
    filled = filled.replace(QUERY_PLACEHOLDER, query)
    return filled

app = flask.Flask(__name__, static_url_path=STATIC_PATH)

@app.route("/", methods=['GET', 'POST'])
def root():
    query = flask.request.args.get(QUERY_PARAMETER)

    if not query:
        # no query, just show index
        template = get_index()
        return fill_template(template, '', '')
    else:
        template = get_template()
        results = perform_query(query)
        # non-empty query, search and display
        # plug in separate visualizations to allow for progressive loading
        visualizations = []
        for block in results.split('\n\n'):
            visualizations.append(visualization_start + 
                                  block + '\n\n' + 
                                  visualization_end)
        return fill_template(template, ''.join(visualizations), query)

@app.route('/css/<path:path>')
def serve_css(path):
    return flask.send_from_directory('css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    return flask.send_from_directory('js', path)

def print_debug_warning(out):
    print >> out, """
##############################################################################
#
# WARNING: RUNNING IN DEBUG MODE. NEVER DO THIS IN PRODUCTION, IT
# ALLOWS ARBITRARY CODE EXECUTION.
#
##############################################################################
"""

def main(argv):
    if not DEBUG:
        host='0.0.0.0'
    else:
        print_debug_warning(sys.stdout)
        host='127.0.0.1'
    app.run(host=host, port=PORT, debug=DEBUG)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
