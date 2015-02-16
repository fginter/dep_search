import argparse
import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import json
import re
import struct
import os
import setlib.pytset as pytset
import zlib
import itertools

ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

symbs=re.compile(ur"[^A-Za-z0-9_]",re.U)

def prepare_tables(conn):
    build=\
    """
    CREATE TABLE graph (
       graph_id INTEGER,
       token_count INTEGER,
       conllu_data_compressed BLOB,
       conllu_comment_compressed BLOB
    );
    CREATE TABLE token_index (
       token TEXT,
       graph_id INTEGER,
       token_set BLOB
    );
    CREATE TABLE lemma_index (
       lemma TEXT,
       graph_id INTEGER,
       token_set BLOB
    );
    CREATE TABLE tag_index (
        graph_id INTEGER,
        tag TEXT,
        token_set BLOB
    );
    CREATE TABLE rel (
        graph_id INTEGER,
        dtype TEXT,
        token_gov_set BLOB,
        token_gov_map BLOB,
        token_dep_set BLOB,
        token_dep_map BLOB
    );
    """
    
    for q in build.split(";"):        
        q=q.strip()
        if q:
            print q
            conn.execute(q)
    conn.commit()

def build_indices(conn):
    build=\
    """
    CREATE UNIQUE INDEX tok_gid ON token_index(token,graph_id);
    CREATE UNIQUE INDEX lemma_gid ON lemma_index(lemma,graph_id);
    CREATE UNIQUE INDEX gid_tag ON tag_index(graph_id,tag);
    CREATE INDEX tag_gid ON tag_index(tag,graph_id);
    CREATE UNIQUE INDEX gid ON graph(graph_id);
    CREATE UNIQUE INDEX gid_dtype ON rel(graph_id,dtype);
    analyze;
    """
    for q in build.split(";"):
        if q.strip():
            print q
            conn.execute(q)
    conn.commit()


def read_conll(inp,maxsent=0):
    """ Read conll format file and yield one sentence at a time as a list of lists of columns. If inp is a string it will be interpreted as fi
lename, otherwise as open file for reading in unicode"""
    if isinstance(inp,basestring):
        f=codecs.open(inp,u"rt",u"utf-8")
    else:
        f=codecs.getreader("utf-8")(inp) # read inp directly
    count=0
    sent=[]
    comments=[]
    for line in f:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                yield sent, comments
                if maxsent!=0 and count>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith(u"#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments

    if isinstance(inp,basestring):
        f.close() #Close it if you opened it

def serialize_as_tset_array(tree_len,sets):
    """
    tree_len -> length of the tree to be serialized
    sets: array of tree_len sets, each set holding the indices of the elements
    """
    indices=[]
    for set_idx,s in enumerate(sets):
        for item in s:
            indices.append(struct.pack("@HH",set_idx,item))
    #print "IDXs", len(indices)
    res=struct.pack("@H",tree_len)+("".join(indices))
    return res


def fill_db(conn,src_data):
    """
    `src_data` - iterator over sentences -result of read_conll()
    """
    counter=0
    for sent_idx,(sent,comments) in enumerate(src_data):
        counter+=1
        t=Tree.from_conll(comments,sent)
        
        conn.execute('INSERT INTO graph VALUES(?,?,?,?)', [sent_idx,len(sent),buffer(zlib.compress(t.conllu.encode("utf-8"))),buffer(zlib.compress(t.comments.encode("utf-8")))])
        for token, token_set in t.tokens.iteritems():
            conn.execute('INSERT INTO token_index VALUES(?,?,?)', [token,sent_idx,buffer(token_set.tobytes())])
        for lemma, token_set in t.lemmas.iteritems():
            conn.execute('INSERT INTO lemma_index VALUES(?,?,?)', [lemma,sent_idx,buffer(token_set.tobytes())])
        for tag, token_set in t.tags.iteritems():
            conn.execute('INSERT INTO tag_index VALUES(?,?,?)', [sent_idx,tag,buffer(token_set.tobytes())])
        for dtype, (govs,deps) in t.rels.iteritems():
            ne_g=[x for x in govs if x]
            ne_d=[x for x in deps if x]
            assert ne_g and ne_d
            gov_set=pytset.PyTSet(len(sent),(idx for idx,s in enumerate(govs) if s))
            dep_set=pytset.PyTSet(len(sent),(idx for idx,s in enumerate(deps) if s))
            conn.execute('INSERT INTO rel VALUES(?,?,?,?,?,?)', [sent_idx,dtype,buffer(gov_set.tobytes()),buffer(serialize_as_tset_array(len(sent),govs)),buffer(dep_set.tobytes()),buffer(serialize_as_tset_array(len(sent),deps))])
        if sent_idx%10000==0:
            print str(datetime.now()), sent_idx
        if sent_idx%10000==0:
            conn.commit()
    conn.commit()
    return counter

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Train')
    parser.add_argument('-d', '--dir', required=True, help='Directory name to save the index. Will be wiped and recreated.')
    parser.add_argument('--max', type=int, default=10000, help='How many sentences to read from stdin? default: %(default)d')
    args = parser.parse_args()
#    gather_tbl_names(codecs.getreader("utf-8")(sys.stdin))
    os.system("mkdir -p "+args.dir)
    os.system("rm -f %s/*.db"%args.dir)
    src_data=read_conll(sys.stdin,args.max)
        
    batch=500000
    counter=0
    while True:
        conn=sqlite3.connect(args.dir+"/trees_%05d.db"%counter)
        prepare_tables(conn)
        it=itertools.islice(src_data,batch)
        filled=fill_db(conn,it)
        if filled==0:
            break
        build_indices(conn)
        conn.close()
        counter+=1

