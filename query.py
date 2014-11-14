import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import re


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

    joins=[u"FROM graph"]
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
            joins.append(u"%sJOIN rel AS t_%d ON graph.graph_id=t_%d.graph_id"%(j_type,i,i))
            wheres.append(u"t_%d.dtype=?"%i)
            args.append(res)
            if stype==u"s":
                selects.append(u"t_%d.token_%s_set"%(i,ftype))
            elif stype==u"a":
                selects.append(u"t_%d.token_%s_map"%(i,ftype))
        elif ftype in (u"token",u"lemma",u"tag"):
            joins.append(u"%sJOIN %s_index AS t_%d ON graph.graph_id=t_%d.graph_id"%(j_type,ftype,i,i))
            wheres.append(u"t_%d.%s=?"%(i,ftype))
            args.append(res)
            selects.append(u"t_%d.token_set"%i)
    
    joins.sort() #This is a horrible hack, but it will sort FROM JOIN ... LEFT JOIN the right way and help the QueryPlan generator
    q=u"SELECT %s"%(u", ".join(selects))
    q+=u"\n"+(u"\n".join(j for j in joins))
    if wheres:
        q+=u"\nWHERE\n"+(u" and ".join(w for w in wheres))
    q+=u"\n"
    return q,args

import argparse
import setlib.example_queries as equeries
import setlib.db_util as db_util
if __name__=="__main__":
    #q,args=query([u"token_s_koiran",u"!lemma_s_koira",u"!gov_a_nsubj-cop",u"tag_s_V"])
    #print q,args
    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=500, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-d', '--database', default="sdata_v7.db",help='Name of the database to query. Default: %(default)s.')
    args = parser.parse_args()

    query_obj=equeries.SimpleSearch()
    sql_query,sql_args=query(query_obj.query_fields)
    db=db_util.DB()
    db.open_db(unicode(args.database))
    print >> sys.stderr, sql_query, sql_args
    db.exec_query(sql_query,sql_args)
    for x in equeries.iterate_results(query_obj,db):
        print x
    db.close_db()
    
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
