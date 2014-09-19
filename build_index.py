import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import json
import re


ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

def gather_tbl_names(inp):
    deprel_s,pos_s,feat_s=set(),set(),set()
    for line_no,line in enumerate(inp):
        line=line.strip()
        if not line or line.startswith(u"#"):
            continue
        cols=line.split(u"\t")
        deprel,pos,feat=cols[DEPREL],cols[POS],cols[FEAT]
        if feat=="_":
            feat=[]
        else:
            feat=feat.split(u"|")
        deprel_s.add(deprel)
        pos_s.add(pos)
        for f in feat:
            feat_s.add(f)
        if line_no>10000000:
            break
        if line_no%100000==0:
            print >> sys.stderr, line_no
    s=json.dumps((sorted(deprel_s),sorted(pos_s),sorted(feat_s)))
    print s

        
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
       sentence_id INTEGER
    );
    CREATE TABLE lemma_index (
       lemma TEXT,
       sentence_id INTEGER
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
        tokens=set()
        lemmas=set()
        for cols in sent:
            token=cols[1]
            if token in tokens: #Try not to write duplicates into the DB top make its life easier
                continue
            else:
                tokens.add(token)
            conn.execute('INSERT INTO token_index VALUES(?,?)', [token,sent_idx])

            lemma=cols[2]
            if lemma in lemmas: #Try not to write duplicates into the DB top make its life easier
                continue
            else:
                lemmas.add(lemma)
            conn.execute('INSERT INTO lemma_index VALUES(?,?)', [lemma,sent_idx])
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
    conn=sqlite3.connect("/mnt/ssd/sdata/jennas_test.db")
    prepare_tables(conn)
#    wipe_db(conn)
    src_data=get_sentences(codecs.getreader("utf-8")(sys.stdin),1000)
    fill_db(conn,src_data)
    build_indices(conn)
    conn.close()
