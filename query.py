#!/usr/bin/env python

import sys
import os

THISDIR=os.path.dirname(os.path.abspath(__file__))
os.chdir(THISDIR)

import subprocess
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import re
import zlib
import importlib
import argparse
import db_util
import glob
import tempfile

field_re=re.compile(ur"^(!?)(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
def query(query_fields):
    """
    query_fields: A list of strings describing the data to fetch
          Each string names a set to retrieve

          (gov|dep)_(a|s)_deptype
          - gov -> retrieve a from-governor-to-dependent mapping/set
          - dep -> retrieve a from-dependent-to-governor mapping/set
          - a -> retrieve a mapping (i.e. used as the third argument of the pairing() function
          - s -> retrieve a set (i.e. the set of governors or dependents of given type)
          - deptype -> deptype or u"anytype"
          prefixed with "!" means that only non-empty sets are of interest

          tag_s_TAG  -> retrieve the token set for a given tag
          prefixed with "!" means that only non-empty sets are of interest

          token_s_WORD -> retrieve the token set for a given token
          lemma_s_WORD -> retrieve the token set for a given lemma
          prefixed with "!" means that only non-empty sets are of interest
    """

    joins=[(u"FROM graph",[])]
    wheres=[]
    args=[]
    selects=[u"graph.graph_id",u"graph.token_count"]
    for i,f in enumerate(query_fields):
        match=field_re.match(f)
        assert match
        req,ftype,stype,res=match.groups() #required? field-type?  set-type?  restriction
        if req==u"!":
            j_type=u""
        elif not req:
            j_type=u"LEFT "
        else:
            assert False #should never happen
        if ftype in (u"gov",u"dep"):
            joins.append((u"%sJOIN rel AS t_%d ON graph.graph_id=t_%d.graph_id and t_%d.dtype=?"%(j_type,i,i,i),[res]))
            if stype==u"s":
                selects.append(u"t_%d.token_%s_set"%(i,ftype))
            elif stype==u"a":
                selects.append(u"t_%d.token_%s_map"%(i,ftype))
        elif ftype in (u"token",u"lemma",u"tag"):
            joins.append((u"%sJOIN %s_index AS t_%d ON graph.graph_id=t_%d.graph_id and t_%d.%s=?"%(j_type,ftype,i,i,i,ftype),[res]))
            selects.append(u"t_%d.token_set"%i)
    
    joins.sort() #This is a horrible hack, but it will sort FROM JOIN ... LEFT JOIN the right way and help the QueryPlan generator
    q=u"SELECT %s"%(u", ".join(selects))
    q+=u"\n"+(u"\n".join(j[0] for j in joins))
    q+=u"\n"
    args=[]
    for j in joins:
        args.extend(j[1])
    return q,args

def get_data_from_db(db_conn,graph_id):
    results=db_conn.execute('SELECT conllu_data_compressed,conllu_comment_compressed FROM graph WHERE graph_id=?',(str(graph_id),))
    for sent,comment in results.fetchall():
        return zlib.decompress(sent).strip(),zlib.decompress(comment).strip()
    return None,None

def load(pyxFile):
    """Loads a search pyx file, returns the module"""
    ###I need to hack around this, because this thing is messing stdout
    print >> sys.stderr, "Loading", pyxFile
    error=subprocess.call(["python","compile_ext.py",pyxFile], stdout=sys.stderr, stderr=sys.stderr)
    if error!=0:
        print >> sys.stderr, "Cannot compile search code, error:",error
        sys.exit(1)
    mod=importlib.import_module(pyxFile)
    return mod

def get_url(comments):
    for c in comments:
        if c.startswith(u"# URL:"):
            return c.split(u":",1)[1].strip()
    return None

def query_from_db(q_obj,db_name,sql_query,sql_args,max_hits,context):
    db=db_util.DB()
    db.open_db(unicode(db_name))
    res_db=sqlite3.connect(unicode(db_name))
    db.exec_query(sql_query,sql_args)
    print >> sys.stderr, sql_query, sql_args
    counter=0
    sql_counter=0
    while True:
        idx,r,rows=query_obj.next_result(db)
        sql_counter+=rows
        if r==None:
            break
        print "# graph id:",idx
        for x in r:
            print "# visual-style\t%s\tbgColor:lightgreen"%(x+1)
        hit,hit_comment=get_data_from_db(res_db,idx)
        if hit_comment:
            print hit_comment
        if context>0:
            hit_url=get_url(hit_comment.decode("utf-8"))
            texts=[]
            # get +/- 2 sentences from db
            for i in range(idx-context,idx+context+1):
                if i==idx:
                    data=hit
                else:
                    data,data_comment=get_data_from_db(res_db,i)
                    if data is None or get_url(data_comment.decode("utf-8"))!=hit_url:
                        continue
                text=u" ".join(t.split(u"\t",2)[1] for t in data.decode(u"utf-8").split(u"\n"))
                if i<idx:
                    texts.append(u"# context-before: "+text)
                elif i==idx:
                    texts.append(u"# context-hit: "+text)
                else:
                    texts.append(u"# context-after: "+text)
            print (u"\n".join(text for text in texts)).encode(u"utf-8")
        print hit
        print
        counter+=1
        if max_hits!=0 and counter>=max_hits:
            print >> sys.stderr, "--max ",max_hits
            print >> sys.stderr, counter, "hits in", db_name
            sys.exit(0)
    print >> sys.stderr, sql_counter,"rows from database",db_name
    print >> sys.stderr, counter, "hits in", db_name
    db.close_db()
    res_db.close()
    return counter
    
def main(argv):
    global query_obj

    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=500, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-d', '--database', default="/mnt/ssd/sdata/pb-10M/*.db",help='Name of the database to query or a wildcard of several DBs. Default: %(default)s.')
    parser.add_argument('-o', '--output', default=None, help='Name of file to write to. Default: STDOUT.')
    parser.add_argument('search', nargs="?", default="parsubj",help='The name of the search to run (without .pyx), or a query expression. Default: %(default)s.')
    parser.add_argument('--context', required=False, action="store", default=0, type=int, metavar='N', help='Print the context (+/- N sentences) as comment. Default: %(default)d.')
    parser.add_argument('--keep_query', required=False, action='store_true',default=False, help='Do not delete the compiled query after completing the search.')

    args = parser.parse_args(argv[1:])

    if args.output is not None:
        sys.stdout = open(args.output, 'w')

    if os.path.exists(args.search+".pyx"):
        print >> sys.stderr, "Loading "+args.search+".pyx"
        mod=load(args.search)
    else:
        path = '/'.join(args.database.split('/')[:-1])
        json_filename = path + '/symbols.json' 
        #This is a query, compile first
        import pseudocode_ob_3 as pseudocode_ob

        import hashlib
        m = hashlib.md5()
        m.update(args.search)
        temp_file_name = 'qry_' + m.hexdigest() + '.pyx'
        if not os.path.isfile(temp_file_name):
            f = open('qry_' + m.hexdigest() + '.pyx', 'wt')
            pseudocode_ob.generate_and_write_search_code_from_expression(args.search, f, json_filename=json_filename)
        mod=load(temp_file_name[:-4])

    query_obj=mod.GeneratedSearch()
    sql_query,sql_args=query(query_obj.query_fields)
    
    dbs=glob.glob(args.database)
    dbs.sort()

    total_hits=0
    for d in dbs:
        total_hits+=query_from_db(query_obj,d,sql_query,sql_args,args.max,args.context)
        if total_hits > args.max:
            break
    print >> sys.stderr, "Total number of hits:",total_hits

    if not args.keep_query:
        try:
            os.remove(temp_file_name)
            os.remove(temp_file_name[:-4] + '.cpp')
            os.remove(temp_file_name[:-4] + '.so')
        except:
            pass

if __name__=="__main__":
    sys.exit(main(sys.argv))
