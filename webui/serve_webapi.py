import flask
import json
import sys
import subprocess as sproc
import glob
import random
import os.path

app = flask.Flask(__name__)

ABSOLUTE_RETMAX=100000

with open("corpora.json","rt") as f:
    corpora=json.load(f)

@app.route("/",methods=["GET"])
def run_query():
    if "q" not in flask.request.args:
        return flask.Response("<html><body><ul><li>q: the query to run</li><li>corpora: corpus,corpus,corpus</li><li>max: max number of results (will be capped at 100K by us)</li><li>dl: set headers to offer file for download</li></body></html>")
    retmax=int(flask.request.args.get("max",1000)) #default is 1000
    retmax=min(retmax,ABSOLUTE_RETMAX)

    dbs=[]
    for corpus in flask.request.args.get("corpora","").split(","):
        path=corpora.get(corpus)
        if path is None:
            continue
        dbs.extend(glob.glob(os.path.join(path,"*.db")))
    dbs=sorted(dbs)

    def generate():
        args=["python","query.py","-m",str(retmax),flask.request.args["q"],"--dblist"]+dbs
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
    app.run(host=host, port=port, debug=True, use_reloader=True)


