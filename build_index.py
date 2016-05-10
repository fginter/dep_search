import argparse
import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree, SymbolStats
import json
import re
import struct
import os
import setlib.pytset as pytset
import zlib
import itertools
import os.path
import traceback

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
        token_gov_map BLOB,
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
            cols=line.split(u"\t")
            if cols[0].isdigit():
                sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments

    if isinstance(inp,basestring):
        f.close() #Close it if you opened it

def add_doc_comments(sents):
    """
    in goes an iterator over sent,comments pairs
    out goes an iterator with comments enriched by URLs
    """
    urlRe=re.compile(ur'url="(.*?)"',re.U)
    doc_counter,sent_in_doc_counter=-1,0
    current_url=None
    for sent,comments in sents:
        ###PB3 style URLs
        if len(sent)==1 and sent[0][1].startswith("####FIPBANK-BEGIN-MARKER:"):
            current_url=sent[0][1].split(u":",1)[1]
            doc_counter+=1
            sent_in_doc_counter=0
            continue
        ###Todo: PB4 style URL comments
        for c in comments:
            if c.startswith(u"###C:</doc"):
                current_url=None
            elif c.startswith(u"###C:<doc"):
                match=urlRe.search(c)
                if not match: #WHoa!
                    print >> sys.stderr, "Missing url", c.encode("utf-8")
                else:
                    current_url=match.group(1)
        ###C:<doc id="3-1954112" length="1k-10k" crawl_date="2014-07-26" url="http://parolanasema.blogspot.fi/2013/02/paris-paris-maison-objet-messut-osa-1.html" langdiff="0.37">
        if current_url is not None:
            comments.append(u"# URL: "+current_url)
            comments.append(u"# DOC/SENT: %d/%d"%(doc_counter,sent_in_doc_counter))
        yield sent,comments
        sent_in_doc_counter+=1

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


def fill_db(conn,src_data,stats):
    """
    `src_data` - iterator over sentences -result of read_conll()
    """
    counter=0
    for sent_idx,(sent,comments) in enumerate(add_doc_comments(src_data)):
        if len(sent)>256:
            print >> sys.stderr, "skipping length", len(sent)
            sys.stderr.flush()
            continue
        counter+=1
        t=Tree.from_conll(comments,sent,stats)
        
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
            conn.execute('INSERT INTO rel VALUES(?,?,?,?)', [sent_idx,dtype,buffer(serialize_as_tset_array(len(sent),govs)),buffer(serialize_as_tset_array(len(sent),deps))])
        if sent_idx%10000==0:
            print str(datetime.now()), sent_idx
        if sent_idx%10000==0:
            conn.commit()
    conn.commit()
    return counter

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Train')
    parser.add_argument('-d', '--dir', required=True, help='Directory name to save the index. Will be wiped and recreated.')
    parser.add_argument('-p', '--prefix', required=True, default="trees", help='Prefix name of the database files. Default: %(default)s')
    parser.add_argument('--max', type=int, default=0, help='How many sentences to read from stdin? 0 for all. default: %(default)d')
    parser.add_argument('--wipe', default=False, action="store_true", help='Wipe the target directory before building the index.')
    args = parser.parse_args()
#    gather_tbl_names(codecs.getreader("utf-8")(sys.stdin))
    os.system("mkdir -p "+args.dir)
    if args.wipe:
        print >> sys.stderr, "Wiping target"
        cmd="rm -f %s/*.db %s/symbols.json"%(args.dir,args.dir)
        print >> sys.stderr, cmd
        os.system(cmd)

    stats=SymbolStats()
    src_data=read_conll(sys.stdin,args.max)
        
    batch=500000
    counter=0
    while True:
        db_name=args.dir+"/%s_%05d.db"%(args.prefix,counter)
        if os.path.exists(db_name):
            os.system("rm -f "+db_name)
        conn=sqlite3.connect(db_name)
        prepare_tables(conn)
        it=itertools.islice(src_data,batch)
        filled=fill_db(conn,it,stats)
        if filled==0:
            break
        build_indices(conn)
        conn.close()
        counter+=1
        try:
            if os.path.exists(os.path.join(args.dir,"symbols.json")):
                stats.update_with_json(os.path.join(args.dir,"symbols.json"))
        except:
            traceback.print_exc()
        stats.save_json(os.path.join(args.dir,"symbols.json"))


