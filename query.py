import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import re

class Query(object):

    def __init__(self):
        self.query_fields=[]
        self.words=None
        self.lemmas=None

    def match(self,tree):
        assert False #You need to override this in your searches

def query_search(conn,search):
    for t in query(conn,search.words,search.lemmas,search.query_fields):
        res_set=search.match(t)
        if res_set:
            yield t,res_set

def query(conn,words=None,lemmas=None,query_fields=[]):
    """
    words: a list of words the trees should have, or None
    lemmas: a list of lemmas the trees should have, or None
    query_fields: A list of strings describing the data to fetch
          Each string names a set to retrieve
          d_govs_*, d_deps_*, and tags_*  can be preceded with
          ! which means that only non-empty sets are of interest
          Possible values are these strings:
          d_govs_*   (* is a deptype like nsubj)
          d_deps_*   (* is a deptype like nsubj)
          type_govs_*
          type_deps_*
          govs
          deps
          tags_*     (* is a tag like N or CASE_Gen)
    
    Example:
    query(conn,words=[u"dog",u"cat"],query_fields=[u"d_govs_nsubj",u"d_deps_nsubj",u"!d_deps_obj"])
    ...will search for all trees with the words dog and cat in them,
    and will produce a Tree() object for each of them with
    d_govs["nsubj"] and d_deps["nsubj"] set of they are present, and empty set if not.
    d_deps["obj"] is also set, and it is guaranteed to be non-empty.
    """

    sentence_table=u"sentence" #if there are no restrictions, this will get changed to "main"
    select_c=[] #list of the items in select
    where_c=[] #list of conditions to place into the where clause
    joins=[] #list of join statements
    join_args=[] #list of arguments to supply for the SQL query execute, these are in the JOINS and will come first
    where_args=[] #list of arguments to supply for the SQL query execute, there are in the WHERE and will come second
    columns=[] #a list which explains the select results Each item is a tuple. A triple (x,y,z) means set t.x[y]=z, while a pair (x,y) means set t.x=y when deserializing

    #This if .. elif .. else chooses the main table in "FROM"
    if words is not None:
        #Base the search on the word index first
        from_c=u"FROM token_index main"
        where_c.append(u"main.token=?")
        where_args.append(words[0])
        words.pop(0)
    elif lemmas is not None:
        from_c=u"FROM lemma_index main"
        where_c.append(u"main.lemma=?")
        where_args.append(lemmas[0])
        lemmas.pop(0)
    else:
        from_c=u"FROM sentence main"
        sentence_table=u"main"
    if words is not None:
        for i,w in enumerate(words):
            joins.append("JOIN token_index ti%d ON main.sentence_id=ti%d.sentence_id"%(i,i))
            where_c.append("ti%d.token=?"%i)
            where_args.append(w)
    if lemmas is not None:
        for i,l in enumerate(lemmas):
            joins.append("JOIN lemma_index li%d ON main.sentence_id=li%d.sentence_id"%(i,i))
            where_c.append("li%d.lemma=?"%i)
            where_args.append(l)
    ##I won't join the sentence table in, unless I have to
    #if sentence_table==u"sentence":
    #    joins.append("JOIN sentence ON sentence.sentence_id=main.sentence_id")

    for i,d in enumerate(query_fields):
        if u"d_govs" in d or u"d_deps" in d:
            compulsory,table,val=re.match(ur"^(!?)(d_.*?)_(.*)$",d).groups()
            table_alias=table+u"_"+unicode(i) #just a unique name for this table
            if compulsory==u"!":
                join=u"JOIN"
            else:
                join=u"LEFT JOIN"
            joins.append(u"%(join)s %(table)s %(table_alias)s ON %(table_alias)s.sentence_id=main.sentence_id AND %(table_alias)s.dtype=?"%{u"join":join,u"table":table,u"table_alias":table_alias})
            join_args.append(val)
            select_c.append("%(table_alias)s.sdata AS %(table_alias)s_sdata"%{u"table_alias":table_alias})
            columns.append((table,val,set()))
        elif u"type_govs" in d or u"type_deps" in d:
            compulsory,col_name,val=re.match(ur"^(!?)(type_.*?)_(.*)$",d).groups()
            table=col_name.replace(u"type",u"d",1)
            table_alias=table+u"_"+unicode(i) #just a unique name for this table
            if compulsory==u"!":
                join=u"JOIN"
            else:
                join=u"LEFT JOIN"
            joins.append(u"%(join)s %(table)s %(table_alias)s ON %(table_alias)s.sentence_id=main.sentence_id AND %(table_alias)s.dtype=?"%{u"join":join,u"table":table,u"table_alias":table_alias})
            join_args.append(val)
            select_c.append("%(table_alias)s.%(col_name)s AS %(table_alias)s_%(col_name)s"%{u"table_alias":table_alias,u"col_name":col_name})
            columns.append((col_name,val,{}))
        elif u"tags_" in d:
            compulsory,table,val=re.match(ur"^(!?)(tags)_(.*)$",d).groups()
            table_alias=table+u"_"+unicode(i) #just a unique name for this table
            if compulsory==u"!":
                join=u"JOIN"
            else:
                join=u"LEFT JOIN"
            joins.append(u"%(join)s %(table)s %(table_alias)s ON %(table_alias)s.sentence_id=main.sentence_id AND %(table_alias)s.tag=?"%{u"join":join,u"table":table,u"table_alias":table_alias})
            join_args.append(val)
            select_c.append("%(table_alias)s.sdata AS %(table_alias)s_sdata"%{u"table_alias":table_alias})
            columns.append((table,val,set()))
        elif d in (u"govs",u"deps"):
            table=d
            table_alias=table+u"_"+unicode(i) #just a unique name for this table
            joins.append(u"JOIN %(table)s %(table_alias)s ON %(table_alias)s.sentence_id=main.sentence_id"%{u"table":table,u"table_alias":table_alias})
            select_c.append("%(table_alias)s.sdata AS %(table_alias)s_sdata"%{"table_alias":table_alias})
            columns.append((table,None)) #I leave this at none to cause an error if a tree ever needs the default here, which should never happen

    #select_c.insert(0,sentence_table+u".sdata AS sentence_sdata") #...don't grab the sentence data
    q=u"SELECT %s"%(u", ".join(select_c))
    q+=u"\n"+from_c
    q+=u"\n"+(u"\n".join(j for j in joins))
    if where_c:
        q+=u"\nWHERE\n"+(u" and ".join(w for w in where_c))
    q+=u"\n"

    print >> sys.stderr, q, join_args+where_args

    BATCH=1000
    rset=conn.execute(q,join_args+where_args)
    while True:
        rows=rset.fetchmany(BATCH)
        if not rows:
            break
        for row in rows:
            tree=Tree()#pickle.loads(str(row[0])) #The first column is the serialized data
            for col,data in zip(columns,row):
                if len(col)==3: #(x,y,z) tree.x[y]=z
                    d,key,default=col
                    if data is not None:
                        val=pickle.loads(str(data))
                    else:
                        val=default
                    tree.__dict__.setdefault(d,{})[key]=val
                elif len(col)==2: #(x,y) tree.x=y
                    d,default=col
                    if data is not None:
                        val=pickle.loads(str(data))
                    else:
                        val=default
                    tree.__dict__[d]=val
            yield tree



import argparse
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=500, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-d', '--database', default="/mnt/ssd/sdata/sdata_v5_1M_trees.db",help='Name of the database to query. Default: %(default)s.')

    args = parser.parse_args()
    
    conn=sqlite3.connect(args.database)

    from test_search import SearchKoska, SearchPtv, SearchNSubjCop
    s=SearchPtv()
    out8=codecs.getwriter("utf-8")(sys.stdout)
    for counter,(t,res_set) in enumerate(query_search(conn,s)):
        #t.to_conll(out8,highlight=res_set)
        if args.max>0 and counter+1>=args.max:
            break
    conn.close()
