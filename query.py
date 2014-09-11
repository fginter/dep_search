import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree

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
    conn=sqlite3.connect("/mnt/ssd/sdata/sdata.db")

    out8=codecs.getwriter("utf-8")(sys.stdout)
    for t in query_on_words(conn,u"koska",search_koska):
        t.to_conll(out8)
    conn.close()
