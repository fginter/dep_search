import flask
import json
import sys
import subprocess as sproc
import glob
import random
import os.path
import available_corpora
from local_config import SOLR_URL,LMDB_PATH

DEFAULT_PORT=45678

THISDIR=os.path.abspath(os.path.dirname(__file__))

help_response="""\
<html>
<body>
<h1>/</h1>
<ul>
   <li>search: the query to run</li>
   <li>db: corpus,corpus,corpus</li>
   <li>retmax: max number of results (will be capped at 100K by us)</li>
   <li>dl: set headers to offer file for download</li>
   <li>shuffle: randomly shuffle the tree index databases (note: trees still returned in their document order, though!)</li>
   <li>i or case=False or case=false: case insensitive search</li>
   <li>context: number of sentences of context to include in the result. Currently capped at 10.</li>
</ul>
<h1>/metadata</h1>
Returns a json with the list of available corpora, etc...
</body>
</html>
"""

app = flask.Flask(__name__)

ABSOLUTE_RETMAX=100000
MAXCONTEXT=10

@app.route("/metadata",methods=["GET"],strict_slashes=False)
def get_metadata():
    corpora=available_corpora.get_corpora(os.path.join(THISDIR,"corpora.yaml"),SOLR_URL)
    corpus_groups=available_corpora.get_corpus_groups(os.path.join(THISDIR,"corpus_groups.yaml"),corpora)
    res={"corpus_groups":corpus_groups}
    return json.dumps(res)

@app.route("/",methods=["GET"])
def run_query():
    #corpora=available_corpora.get_corpora(os.path.join(THISDIR,"corpora.yaml"),SOLR_URL)
    if "search" not in flask.request.args:
        return flask.Response(help_response)
    retmax=int(flask.request.args.get("retmax",1000)) #default is 1000
    retmax=min(retmax,ABSOLUTE_RETMAX)

    extra_args=[]
    if "i" in flask.request.args or flask.request.args.get("case","true").lower()=="false":
        extra_args.append("-i")
    ctx=flask.request.args.get("context",0)
    try:
        ctx=int(ctx)
    except ValueError:
        return "<html><body>Incorrect context value</body></html>"
    if ctx>0:
        ctx=min(ctx,MAXCONTEXT)
        extra_args.append("--context")
        extra_args.append(str(ctx))
    #if "shuffle" in flask.request.args
    sources=list(s.strip() for s in flask.request.args["db"].split(","))
    sources=" OR ".join(sources)
    extra_args.extend(["--extra",'+source:(%s)'%sources])
    
    def generate():
        args=["python","query.py"]+["--solr",SOLR_URL,"-d",LMDB_PATH]+extra_args+["-m",str(retmax),flask.request.args["search"].encode("utf-8")]
        print >> sys.stderr, "Running", args
        proc=sproc.Popen(args=args,cwd="..",stdout=sproc.PIPE)
        for line in proc.stdout:
            yield line
    resp=flask.Response(flask.stream_with_context(generate()),content_type="text/plain; charset=utf-8")
    if "dl" in flask.request.args:
        resp.headers["Content-Disposition"]="attachment; filename=query_result.conllu"
    return resp

if __name__=="__main__":
    #DEFAULT_PORT set at the top of this file, defaults to 45678
    host='0.0.0.0'
    app.run(host=host, port=DEFAULT_PORT, debug=True, use_reloader=True)


