import flask
import json
import sys
import subprocess as sproc
import glob
import random
import os.path

help_response="""\
<html>
<body>
<h1>/</h1>
<ul>
   <li>search: the query to run</li>
   <li>db: corpus,corpus,corpus</li>
   <li>retmax: max number of results (will be capped at 100K by us)</li>
   <li>dl: set headers to offer file for download</li>
   <li>i: case insensitive search</li>
</ul>
<h1>/metadata</h1>
Returns a json with the list of available corpora, etc...
</body>
</html>
"""

app = flask.Flask(__name__)

ABSOLUTE_RETMAX=100000

@app.route("/metadata",methods=["GET"],strict_slashes=False)
def get_metadata():
    with open("corpora.json","rt") as f:
        corpora=json.load(f)
    res={"corpus_list":sorted(corpora.keys())}
    return json.dumps(res)

@app.route("/",methods=["GET"])
def run_query():
    with open("corpora.json","rt") as f:
        corpora=json.load(f)
    if "search" not in flask.request.args:
        return flask.Response(help_response)
    retmax=int(flask.request.args.get("retmax",1000)) #default is 1000
    retmax=min(retmax,ABSOLUTE_RETMAX)

    extra_args=[]
    if "i" in flask.request.args:
        extra_args.append("-i")
    
    dbs=[]
    for corpus in flask.request.args.get("db","").split(","):
        path=corpora.get(corpus)
        if path is None:
            continue
        dbs.extend(glob.glob(os.path.join(path,"*.db")))
    dbs=sorted(dbs)

    def generate():
        args=["python","query.py"]+extra_args+["-m",str(retmax),flask.request.args["search"].encode("utf-8"),"--dblist"]+dbs
        print >> sys.stderr, "Running", args
        proc=sproc.Popen(args=args,cwd="..",stdout=sproc.PIPE)
        for line in proc.stdout:
            yield line
    resp=flask.Response(flask.stream_with_context(generate()),content_type="text/plain; charset=utf-8")
    if "dl" in flask.request.args:
        resp.headers["Content-Disposition"]="attachment; filename=query_result.conllu"
    return resp

if __name__=="__main__":
    host='0.0.0.0'
    port=45678
    app.run(host=host, port=port, debug=False, use_reloader=True)


