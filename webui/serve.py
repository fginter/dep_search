#!/usr/bin/env python

import sys
import os.path
import subprocess
import codecs
import json

from collections import defaultdict

import flask

# Name of JSON containing information on available DBs.
CORPORA_FILENAME = 'corpora.json'
CORPORA_LISTFILE = 'available_corpora.json'
# App settings. IMPORTANT: set DEBUG = False for publicly accessible
# installations, the debug mode allows arbitrary code execution.
DEBUG = False
HOST = 'localhost'
PORT = 80
STATIC_PATH = '/static'
DB_PARAMETER = 'db'
QUERY_PARAMETER = 'search'

# Template-related constants
INDEX_TEMPLATE = 'index.html'
RESULT_TEMPLATE = 'index.html'
SERVER_URL_PLACEHOLDER = '{{ SERVER_URL }}'
QUERY_PLACEHOLDER = '{{ QUERY }}'
DBS_PLACEHOLDER = '{{ OPTIONS }}'
DB_PLACEHOLDER = '{{ DBNAME }}'
CONTENT_START = '<!-- CONTENT-START -->'
CONTENT_END = '<!-- CONTENT-END -->'
ERROR_PLACEHOLDER = '{{ ERROR }}'

# Visualization wrapping
visualization_start = '<pre><code class="conllu">'
visualization_end = '</code></pre>'

def server_url(host=HOST, port=PORT):
    url = host#:%d' % (host, port)
    if not url.startswith('http://'):
        url = 'http://' + url # TODO do this properly
    return url

def load_corpora(filename=CORPORA_FILENAME):
    try:
        with open(filename) as f:
            return json.loads(f.read())
    except Exception, e:
        print 'Failed to load data on corpora from', filename
        raise

def load_corpora_list(filename=CORPORA_LISTFILE):

    try:
        with open(filename) as f:
            return json.loads(f.read())
    except Exception, e:
        print 'Failed to load data on corpora from', filename
        raise

def get_database_directory(dbname):
    return load_corpora().get(dbname, '')

def get_database_symbols(dbname):
    dbdir = get_database_directory(dbname)
    with open(os.path.join(dbdir, 'symbols.json')) as f:
        return json.loads(f.read())

def perform_query(dbname, query):
    # sorry, this is pretty clumsy ...
    script_dir = os.path.dirname(os.path.realpath(__file__))
    query_cmd = os.path.join(script_dir, '..', 'query.py')

    dbdir = get_database_directory(dbname)
    dbs = os.path.join(dbdir, '*.db')
    args = [query_cmd, '-d', dbs, '-m', '100', query.encode('utf-8')]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    return out, err

def get_index(fn=INDEX_TEMPLATE):
    with codecs.open(fn, encoding='utf-8') as f:
        return f.read()

def get_template(fn=RESULT_TEMPLATE):
    with codecs.open(fn, encoding='utf-8') as f:
        return f.read()

def render_dbs(selected):
    corpora = load_corpora_list()
    print corpora
    options = []
    for name in corpora:
        s = ' selected="selected"' if name == selected else ''
        options.append('<option value="%s"%s>%s</option>' % (name, s, name))
    return '\n'.join(options)

def fill_template(template, content='', error='', dbname='', query=''):
    # TODO: use jinja
    if dbname is None:
        dbname = ''
    assert CONTENT_START in template
    assert CONTENT_END in template
    header = template[:template.find(CONTENT_START)]
    trailer = template[template.find(CONTENT_END):]
    print type(header), type(content), type(trailer)
    filled = header + content + trailer
    filled = filled.replace(SERVER_URL_PLACEHOLDER, server_url())
    t_q = query[:]
    t_q = t_q.replace('"', '&quot;')
    filled = filled.replace(QUERY_PLACEHOLDER, t_q)
    filled = filled.replace(DBS_PLACEHOLDER, render_dbs(dbname))
    filled = filled.replace(DB_PLACEHOLDER, dbname)
    if len(error) < 1:
        filled = filled.replace(ERROR_PLACEHOLDER, '')
    else:
        filled = filled.replace(ERROR_PLACEHOLDER, '<div style="background-color:black; color:white; padding:20px;"><p>' + error.decode('utf8') + '</p></div>')
    return filled

app = flask.Flask(__name__, static_url_path=STATIC_PATH)

def query_and_fill_template(dbname, query):
    template = get_template()
    try:
        results, error = perform_query(dbname, query)
    except Exception, e:
        return "Internal error: %s" % (str(e))
    # plug in separate visualizations to allow for progressive loading
    #error = []
    if 'raise' not in error:
        error = ''
    else:
        if 'ExpressionError:' in error:
            error = error.split('ExpressionError:')[-1]
            #error.replace('\n', '<p>')

    visualizations = []
    for block in results.split('\n\n')[:-1]:
        block = block.decode('utf-8')
        visualizations.append(visualization_start +
                              block + '\n\n' +
                              visualization_end)
    return fill_template(template, ''.join(visualizations), error, dbname, query)

def _types(db):
    symbols = get_database_symbols(db)
    # symbols is a dict with a structure like this:
    # "nummod": [ [ "DTYPE", null, 2401 ] ]
    # group by the first value ("DTYPE" above)
    groups = defaultdict(list)
    for key, value in symbols.iteritems():
        for item in value:
            groups[item[0]].append((key, item))

    # sort each group
    for group in groups.keys():
        groups[group].sort()

    # convert each group to HTML
    output = {}
    for group in groups:
        html = ['<h3>%s</h3>\n<ul>' % group]
        for type_, item in groups[group]:
            # Note: currently just writing out the type name, not any
            # of the other information in the file.
            html.append('<li>%s</li>' % type_)
        html.append('</ul')
        output[group] = '\n'.join(html)
    merged = '\n'.join(output.values())

    # fill template and return
    template = get_index()
    return fill_template(template, merged, db)

@app.route("/types/<db>")
def types(db):
    try:
        return _types(db)
    except Exception, e:
        import traceback
        return "Internal error: %s\n%s" % (str(e), traceback.format_exc())

def _root():
    dbname = flask.request.args.get(DB_PARAMETER)
    query = flask.request.args.get(QUERY_PARAMETER)

    if not dbname or not query:
        # missing info, just show index
        template = get_index()
        return fill_template(template, dbname=dbname)
    else:
        # non-empty query, search and display
        return query_and_fill_template(dbname, query)

@app.route("/", methods=['GET', 'POST'])
def root():
    try:
        return _root()
    except Exception, e:
        import traceback
        return "Internal error: %s\n%s" % (str(e), traceback.format_exc())

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
    app.run(host=host, port=PORT, debug=DEBUG, use_reloader=True)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
