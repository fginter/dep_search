import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import re

def query(conn,words=None,lemmas=None,data=[]):
    """
    words: a list of words the trees should have, or None
    lemmas: a list of lemmas the trees should have, or None
    data: A list of strings describing the data to fetch
          Each string names a set to retrieve
          d_govs_*, d_deps_*, and tags_*  can be preceded with
          ! which means that only non-empty sets are of interest
          Possible values are these strings:
          d_govs_*   (* is a deptype like nsubj)
          d_deps_*   (* is a deptype like nsubj)
          govs
          deps
          tags_*     (* is a tag like N or CASE_Gen)
    
    Example:
    query(conn,words=[u"dog",u"cat"],data=[u"d_govs_nsubj",u"d_deps_nsubj",u"!d_deps_obj"])
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
    if sentence_table==u"sentence":
        joins.append("JOIN sentence ON sentence.sentence_id=main.sentence_id")

    for i,d in enumerate(data):
        if u"d_govs" in d or u"d_govs" in d:
            compulsory,table,val=re.match(ur"^(!?)(d_.*?)_(.*)$",d).groups()
            if compulsory==u"!":
                join=u"JOIN"
            else:
                join=u"LEFT JOIN"
            joins.append(u"%s %s %s_%d ON %s_%d.sentence_id=main.sentence_id AND %s_%d.dtype=?"%(join,table,table,i,table,i,table,i))
            join_args.append(val)
            select_c.append("%s_%d.sdata AS %s_%s_sdata"%(table,i,table,val))
            columns.append((table,val,set()))
        elif u"tags_" in d:
            compulsory,table,val=re.match(ur"^(!?)(tags)_(.*)$",d).groups()
            if compulsory==u"!":
                join=u"JOIN"
            else:
                join=u"LEFT JOIN"
            joins.append(u"%s %s %s_%d ON %s_%d.sentence_id=main.sentence_id AND %s_%d.tag=?"%(join,table,table,i,table,i,table,i))
            join_args.append(val)
            select_c.append("%s_%d.sdata AS %s_%s_sdata"%(table,i,table,val))
            columns.append((table,val,set()))
        elif d in (u"govs",u"deps"):
            table=d
            joins.append(u"JOIN %s %s_%d ON %s_%d.sentence_id=main.sentence_id"%(table,table,i,table,i))
            select_c.append("%s_%d.sdata AS %s_sdata"%(table,i,table))
            columns.append((table,None)) #I leave this at none to cause an error if a tree ever needs the default here, which should never happen

    select_c.insert(0,sentence_table+u".sdata AS sentence_sdata") #...always want the sentence
    q=u"SELECT %s"%(u", ".join(select_c))
    q+=u"\n"+from_c
    q+=u"\n"+(u"\n".join(j for j in joins))
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
            tree=pickle.loads(str(row[0])) #The first column is the serialized data
            for col,data in zip(columns,row[1:]):
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
            yield tree, d

if __name__=="__main__":
    conn=sqlite3.connect("/mnt/ssd/sdata/sdata_v3.db")

    # out8=codecs.getwriter("utf-8")(sys.stdout)
    # for t in query_on_words(conn,None,search_ptv):
    #     t.to_conll(out8)

    
    for x in query(conn,lemmas=[u"olla"],data=[u"d_govs_nsubj",u"d_deps_nsubj",u"!d_govs_dobj",u"!tags_N"]):
        print x


    #for t in query(conn,[u"."],[],[]):
    #    print t
    conn.close()
