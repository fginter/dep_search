import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import re
import zlib
import importlib

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
    results=db_conn.execute('SELECT conllu_comment_compressed FROM graph WHERE graph_id=?',(str(graph_id),))
    for sent in results.fetchall():
        print zlib.decompress(sent[0])


def load(pyxFile):
    from distutils.core import setup
    from Cython.Build import cythonize
    setup(ext_modules = cythonize(
           pyxFile+".pyx",                 # our Cython source
           language="c++",             # generate C++ code
      ),script_args=["build_ext","--inplace"])
    mod=importlib.import_module(pyxFile)
    return mod


import argparse
import db_util
if __name__=="__main__":
    #q,args=query([u"token_s_koiran",u"!lemma_s_koira",u"!gov_a_nsubj-cop",u"tag_s_V"])
    #print q,args
    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=500, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-d', '--database', default="/mnt/ssd/sdata/sdata_v7_1M_trees.db",help='Name of the database to query. Default: %(default)s.')
    parser.add_argument('search', default="parsubj",help='The name of the search to run (without .pyx) Default: %(default)s.')
    args = parser.parse_args()

    mod=load(args.search)
    query_obj=mod.GeneratedSearch()
    #query_obj=q.equeries.ParSearch()
    sql_query,sql_args=query(query_obj.query_fields)
    db=db_util.DB()
    db.open_db(unicode(args.database))
    res_db=sqlite3.connect(args.database)
    print "EQ", db.exec_query(sql_query,sql_args)
    print sql_query, sql_args
    counter=0
    sql_counter=0
    while True:
        idx,r,rows=query_obj.next_result(db)
        sql_counter+=rows
        if r==None:
            break
        print "graph id:",idx
        get_data_from_db(res_db,idx)
        counter+=1
    print sql_counter,"rows from database"
    print counter, "hits"
    db.close_db()
    res_db.close()
    
    # conn=sqlite3.connect(args.database)

    # from test_search import SearchKoska, SearchPtv, SearchNSubjCop
    # s=SearchPtv()
    # s=SearchKoska()
    # s=SearchNSubjCop()
    # out8=codecs.getwriter("utf-8")(sys.stdout)
    # for counter,(t,res_set) in enumerate(query_search(conn,s)):
    #     print res_set
    #     #t.to_conll(out8,highlight=res_set)
    #     if args.max>0 and counter+1>=args.max:
    #         break
    # conn.close()
