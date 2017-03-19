import pysolr
import gzip
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
import py_tree_lmdb
import py_store_lmdb
import binascii 
import solr_index
import db_util

ID,FORM,LEMMA,UPOS,XPOS,FEATS,HEAD,DEPREL,DEPS,MISC=range(10)

symbs=re.compile(ur"[^A-Za-z0-9_]",re.U)

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
    res=("".join(indices))
    return res

doc_url_re=re.compile(r'^###C:<doc id=.+url="(.*?)"')
def get_doc_url(comments):
    for c in comments:
        match=doc_url_re.match(c)
        if match:
            return match.group(1)
    else:
        return None
    
if __name__=="__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train')
    parser.add_argument('-d', '--dir', required=True, help='Directory name to save the index. Will be wiped and recreated.')
    parser.add_argument('--max', type=int, default=0, help='How many sentences to read from stdin? 0 for all. default: %(default)d')
    parser.add_argument('--wipe', default=False, action="store_true", help='Wipe the target directory before building the index.')
    parser.add_argument('--solr', default="http://localhost:8983/solr/dep_search",help='Solr url. default: %(default)s')
    parser.add_argument('--lang', default="unknown", help='Language. default: %(default)s')
    parser.add_argument('--source', default="unknown", help='Source (like UDv2, fi_pbank). default: %(default)s')
    args = parser.parse_args()
#    gather_tbl_names(codecs.getreader("utf-8")(sys.stdin))
    os.system("mkdir -p "+args.dir)
    if args.wipe:
        print >> sys.stderr, "Wiping target"
        cmd="rm -f %s/*.mdb %s/set_dict.pickle"%(args.dir,args.dir)
        print >> sys.stderr, cmd
        os.system(cmd)
        pysolr.Solr(args.solr,timeout=10000000).delete(q="*:*")

    solr_idx=solr_index.SolrIDX(args)
        
    src_data=read_conll(sys.stdin, args.max)
    set_dict={}
    lengths=0
    counter=0
    db = py_store_lmdb.Py_LMDB()
    db.open(args.dir)
    db.start_transaction()

    tree_id=0
    from collections import Counter
    setarr_count = Counter([])



    print
    print
    for counter,(sent,comments) in enumerate(src_data):
        if len(sent)>256:
            continue #Skip too long sentences
        if max(len(cols[FORM]) for cols in sent)>50 or max(len(cols[LEMMA]) for cols in sent)>50:
            continue

        #sys.stdout.write('\r' + str(counter))
        if (counter+1)%10000 == 0:
            print "At tree ", counter+1
            sys.stdout.flush()
        s=py_tree_lmdb.Py_Tree()
        blob, form =s.serialize_from_conllu(sent,comments,db) #Form is the struct module format for the blob, not used anywhere really

        s.deserialize(blob)
        lengths+=len(blob)
        counter+=len(blob)
        set_cnt = struct.unpack('=H', blob[2:4])
        arr_cnt = struct.unpack('=H', blob[4:6])
        set_indexes = struct.unpack('=' + str(set_cnt[0]) + 'I', blob[6:6+set_cnt[0]*4])
        arr_indexes = struct.unpack('=' + str(arr_cnt[0]) + 'I', blob[6+set_cnt[0]*4:6+set_cnt[0]*4+arr_cnt[0]*4])
        setarr_count.update(set_indexes + arr_indexes)

        doc_url=get_doc_url(comments)
        if doc_url is not None:
            solr_idx.new_doc(doc_url,u"fi")
        tree_id=solr_idx.add_to_idx(sent)

        # print >> sys.stderr, comments
        # print >> sys.stderr
        # sys.stderr.flush()
        
        #storing
        ### Comment out the four lines below when ready to use solr
        #for flag_number in set_indexes:
        #    db.store_tree_flag_val(tree_id, flag_number)
        #for flag_number in arr_indexes:
        #    db.store_tree_flag_val(tree_id, flag_number)
        db.store_tree_data(tree_id, blob, len(blob))#sys.getsizeof(blob))
    else:
        solr_idx.commit(force=True) #WHatever remains


    print "Average tree length:", lengths/float(counter)
    db.finish_indexing()
