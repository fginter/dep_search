import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree


def query(conn,words=[],lemmas=[],data=[]):
    # """
    # words: a list of words the trees should have, or empty
    # lemmas: a list of lemmas the trees should have, or empty
    # data: What data to return? 
    #       Possible values are these strings
    #       d_govs_*   (* is a deptype like nsubj)
    #       d_deps_*   (* is a deptype like nsubj)
    #       govs
    #       deps
    #       tags_*     (* is a tag like N or CASE_Gen)
    # """
    sentence_table=u"sentence" #if there are no restrictions, this will get changed to "main"
    select_c=[]
    where_c=[] #list of conditions
    joins=[]
    args=[]
    if words:
        #Base the search on the word index first
        from_c=u"FROM token_index main"
        where_c.append(u"main.token=?")
        args.append(words[0])
        words.pop(0)
    elif not lemmas:
        from_c=u"FROM lemma_index main"
        where_c.append(u"main.lemma=?")
        args.append(lemmas[0])
        lemmas.pop(0)
    else:
        from_c=u"FROM sentence main"
        sentence_table=u"main"
    for i,w in enumerate(words):
        joins.append("JOIN token_index ti%d ON main.sentence_id=ti%d.sentence_id"%(i,i))
        where_c.append("ti%d.token=?"%i)
        args.append(word)
    for i,l in enumerate(lemmas):
        joins.append("JOIN lemma_index li%d ON main.sentence_id=li%d.sentence_id"%(i,i))
        where_c.append("li%d.lemma=?"%i)
        args.append(lemma)
    if sentence_table==u"sentence":
        joins.append("JOIN sentence ON sentence.sentence_id=main.sentence_id")
    select_c.insert(0,sentence_table+u".*")


    q=u"SELECT %s"%(u", ".join(select_c))
    q+=u"\n"+from_c
    q+=u"\n"+(u"\n".join(j for j in joins))
    q+=u"\nWHERE\n"+(u" and ".join(w for w in where_c))
    q+=u"\n"

    BATCH=1000
    rset=conn.execute(q,args)
    while True:
        rows=rset.fetchmany(BATCH)
        if not rows:
            break
        for d in rows:
            tree=pickle.loads(str(d[1]))
            yield tree, d
    


from test_search import search_koska, search_ptv
def query_on_words(conn,word,match_pred):
    BATCH=1000
    if word is not None:
        q=u"SELECT sentence.* from sentence JOIN token_index ti ON ti.sentence_id=sentence.sentence_id WHERE TI.token=?"
        rset=conn.execute(q,(word,))
    else:
        q=u"SELECT sentence.* from sentence"
        rset=conn.execute(q)
    while True:
        rows=rset.fetchmany(BATCH)
        if not rows:
            break
        for _,sent_pickle in rows:
            tree=pickle.loads(str(sent_pickle))
            if match_pred(tree):
                yield tree

if __name__=="__main__":
    conn=sqlite3.connect("/mnt/ssd/sdata/sdata_v3.db")

    # out8=codecs.getwriter("utf-8")(sys.stdout)
    # for t in query_on_words(conn,None,search_ptv):
    #     t.to_conll(out8)

    
    for x in query(conn,words=[u"koira"]):
        print x


    #for t in query(conn,[u"."],[],[]):
    #    print t
    conn.close()
