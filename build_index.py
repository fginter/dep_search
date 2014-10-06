import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import json
import re

ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

symbs=re.compile(ur"[^A-Za-z0-9_]",re.U)

def prepare_tables(conn):
    build=\
    """
    CREATE TABLE sentence (
       sentence_id INTEGER,
       sdata BLOB
    );
    CREATE TABLE token_index (
       token TEXT,
       sentence_id INTEGER,
       token_set BLOB
    );
    CREATE TABLE lemma_index (
       lemma TEXT,
       sentence_id INTEGER,
       lemma_set BLOB
    );
    CREATE TABLE d_govs (
        sentence_id INTEGER,
        dtype TEXT,
        sdata BLOB,
        type_govs BLOB
    );
    CREATE TABLE d_deps (
        sentence_id INTEGER,
        dtype TEXT,
        sdata BLOB,
        type_deps BLOB
    );
    CREATE TABLE govs (
        sentence_id INTEGER,
        sdata BLOB
    );
    CREATE TABLE deps (
        sentence_id INTEGER,
        sdata BLOB
    );
    CREATE TABLE tags (
        sentence_id INTEGER,
        tag TEXT,
        sdata BLOB
    );
    """
    
    for q in build.split(";"):
        if q:
            print q
            conn.execute(q)
    conn.commit()

def build_indices(conn):
    build=\
    """
    CREATE UNIQUE INDEX tok_sent ON token_index(token,sentence_id);
    CREATE UNIQUE INDEX lemma_sent ON lemma_index(lemma,sentence_id);
    CREATE UNIQUE INDEX sid ON sentence(sentence_id);
    CREATE UNIQUE INDEX sid_govtype ON d_govs(sentence_id,dtype);
    CREATE UNIQUE INDEX sid_dtype ON d_deps(sentence_id,dtype);
    CREATE UNIQUE INDEX sid_govs ON govs(sentence_id);
    CREATE UNIQUE INDEX sid_deps ON deps(sentence_id);
    CREATE UNIQUE INDEX sid_tag ON tags(sentence_id,tag);
    """
    for q in build.split(";"):
        if q.strip():
            print q
            conn.execute(q)
    conn.commit()

def get_sentences(inp,max_rank=None):
    """
    `inp` file for reading unicode lines
    """
    counter=0
    curr_sent=[]
    for line in inp:
        line=line.strip()
        if not line:
            continue
        if line.startswith(u"#"):
            continue
        if line.startswith(u"1\t"):
            if curr_sent:
                yield curr_sent
                counter+=1
                if max_rank is not None and max_rank==counter:
                    break
                curr_sent=[]
        curr_sent.append(line.split(u"\t"))

def fill_db(conn,src_data):
    """
    `src_data` - iterator over sentences -result of get_sentences()
    """
    for sent_idx,sent in enumerate(src_data):
        t=Tree.from_conll(sent)
        tpickle=pickle.dumps(t)
        conn.execute('INSERT INTO sentence VALUES(?,?)', [sent_idx,buffer(tpickle)])
        for token, token_set in t.dict_tokens.iteritems():
            conn.execute('INSERT INTO token_index VALUES(?,?,?)', [token,sent_idx,pickle.dumps(token_set)])
        for lemma, lemma_set in t.dict_lemmas.iteritems():
            conn.execute('INSERT INTO lemma_index VALUES(?,?,?)', [lemma,sent_idx,pickle.dumps(lemma_set)])
        for dtype,s in t.d_govs.iteritems():
            d=t.type_govs.get(dtype,None)
            assert d is not None
            conn.execute('INSERT INTO d_govs VALUES(?,?,?,?)', [sent_idx,dtype,pickle.dumps(s),pickle.dumps(d)])
        for dtype,s in t.d_deps.iteritems():
            d=t.type_deps.get(dtype,None)
            assert d is not None
            conn.execute('INSERT INTO d_deps VALUES(?,?,?,?)', [sent_idx,dtype,pickle.dumps(s),pickle.dumps(d)])
        for tag,s in t.tags.iteritems():
            conn.execute('INSERT INTO tags VALUES(?,?,?)', [sent_idx,tag,pickle.dumps(s)])
        conn.execute('INSERT INTO govs VALUES(?,?)', [sent_idx, pickle.dumps(t.govs)])
        conn.execute('INSERT INTO deps VALUES(?,?)', [sent_idx, pickle.dumps(t.deps)])
        if sent_idx%10000==0:
            print str(datetime.now()), sent_idx
        if sent_idx%10000==0:
            conn.commit()
    conn.commit()


if __name__=="__main__":
#    gather_tbl_names(codecs.getreader("utf-8")(sys.stdin))
    #conn=sqlite3.connect("/mnt/ssd/sdata/sdata_v3_4M_trees.db")
    conn=sqlite3.connect("/mnt/ssd/sdata/sdata_v6_1M_trees.db")
    #prepare_tables(conn)
#    wipe_db(conn)
    #src_data=get_sentences(codecs.getreader("utf-8")(sys.stdin),1000000)
    #fill_db(conn,src_data)
    build_indices(conn)
    conn.close()
