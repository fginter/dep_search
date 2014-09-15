import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree


def query(conn,words=[],lemmas=[],data=[]):
    """
    words: a list of words the trees should have, or empty
    lemmas: a list of lemmas the trees should have, or empty
    data: What data to return? 
          Possible values are these strings
          d_govs_*   (* is a deptype like nsubj)
          d_deps_*   (* is a deptype like nsubj)
          govs
          deps
          tags_*     (* is a tag like N or CASE_Gen)
    """
    q=\
        """
SELECT s.*, g.*
FROM token_index ti0
JOIN d_govs dg0 ON dg0.sentence_id=ti0.sentence_id AND dg0.dtype='dobj'
JOIN d_govs dg1 ON dg1.sentence_id=ti0.sentence_id AND dg1.dtype='nsubj'
JOIN sentence s ON s.sentence_id=ti0.sentence_id 
LEFT JOIN govs g ON g.sentence_id=ti0.sentence_id
WHERE ti0.token=?
"""
    BATCH=1000
    rset=conn.execute(q,(words[0],))
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
    for t in query(conn,[u"."],[],[]):
        print t
    conn.close()
