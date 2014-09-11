import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree

def wipe_db(conn):
    build=[\
    """
    DROP TABLE IF EXISTS sentence;
    """,
    """
    DROP TABLE IF EXISTS token_index;
    """,
    """
    DROP TABLE IF EXISTS lemma_index;
    """,
    """
    CREATE TABLE IF NOT EXISTS sentence (
       sentence_id INTEGER,
       serialized_data BLOB
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS token_index (
       token TEXT,
       sentence_id INTEGER
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS lemma_index (
       lemma TEXT,
       sentence_id INTEGER
    );
    """
    ]
    
    for q in build:
        conn.execute(q)
    conn.commit()

def build_indices(conn):
    conn.execute("CREATE UNIQUE INDEX tok_sent ON token_index(token,sentence_id);")
    conn.execute("CREATE UNIQUE INDEX lemma_sent ON lemma_index(lemma,sentence_id);")
    conn.execute("CREATE UNIQUE INDEX sid ON sentence(sentence_id);")


def get_sentences(inp):
    """
    `inp` file for reading unicode lines
    """
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
                curr_sent=[]
        curr_sent.append(line.split(u"\t"))

def fill_db(conn,src_data):
    """
    `src_data` - iterator over sentences -result of get_sentences()
    """
    for sent_idx,sent in enumerate(src_data):
        t=Tree.from_conll(sent)
        tpickle=pickle.dumps(t,pickle.HIGHEST_PROTOCOL)
        conn.execute('INSERT OR IGNORE INTO sentence VALUES(?,?)', [sent_idx,buffer(tpickle)])
        tokens=set()
        lemmas=set()
        for cols in sent:
            token=cols[1]
            if token in tokens: #Try not to write duplicates into the DB top make its life easier
                continue
            else:
                tokens.add(token)
            conn.execute('INSERT OR IGNORE INTO token_index VALUES(?,?)', [token,sent_idx])

            lemma=cols[2]
            if lemma in lemmas: #Try not to write duplicates into the DB top make its life easier
                continue
            else:
                lemmas.add(lemma)
            conn.execute('INSERT OR IGNORE INTO lemma_index VALUES(?,?)', [lemma,sent_idx])


        if sent_idx%10000==0:
            print str(datetime.now()), sent_idx
        if sent_idx%10000==0:
            conn.commit()
        if sent_idx>=50000:
            break
    conn.commit()


if __name__=="__main__":
    conn=sqlite3.connect("/mnt/ssd/sdata/sdata_tmp.db")
    wipe_db(conn)
    src_data=get_sentences(codecs.getreader("utf-8")(sys.stdin))
    fill_db(conn,src_data)
    build_indices(conn)
    conn.close()
