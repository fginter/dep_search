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

ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

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

if __name__=="__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train')
    parser.add_argument('-d', '--dir', required=True, help='Directory name to save the index. Will be wiped and recreated.')
    parser.add_argument('--max', type=int, default=0, help='How many sentences to read from stdin? 0 for all. default: %(default)d')
    parser.add_argument('--wipe', default=False, action="store_true", help='Wipe the target directory before building the index.')
    args = parser.parse_args()
#    gather_tbl_names(codecs.getreader("utf-8")(sys.stdin))
    os.system("mkdir -p "+args.dir)
    if args.wipe:
        print >> sys.stderr, "Wiping target"
        cmd="rm -f %s/*.mdb %s/set_dict.pickle"%(args.dir,args.dir)
        print >> sys.stderr, cmd
        os.system(cmd)

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

    try:
        inf = open(args.dir+"/"+'set_dict.pickle','rb')
        set_dict, setarr_count = pickle.load(inf)
        inf.close()
    except:
        pass

    print
    print
    for sent,comments in src_data:
        if (tree_id+1)%10000 == 0:
            print "At tree ", tree_id+1
            sys.stdout.flush()
        s=py_tree_lmdb.Py_Tree()
        blob, form =s.serialize_from_conllu(sent,comments,set_dict) #Form is the struct module format for the blob, not used anywhere really

        s.deserialize(blob)
        lengths+=len(blob)
        counter+=len(blob)
        set_cnt = struct.unpack('=H', blob[2:4])
        arr_cnt = struct.unpack('=H', blob[4:6])
        set_indexes = struct.unpack('=' + str(set_cnt[0]) + 'I', blob[6:6+set_cnt[0]*4])
        arr_indexes = struct.unpack('=' + str(arr_cnt[0]) + 'I', blob[6+set_cnt[0]*4:6+set_cnt[0]*4+arr_cnt[0]*4])
        setarr_count.update(set_indexes + arr_indexes)

        #storing
        for flag_number in set_indexes:
            db.store_tree_flag_val(tree_id, flag_number)
        for flag_number in arr_indexes:
            db.store_tree_flag_val(tree_id, flag_number)
        db.store_tree_data(tree_id, blob, len(blob))#sys.getsizeof(blob))
        tree_id+=1

    print "Average tree length:", lengths/float(counter)
    print "Length of set dict: ", len(set_dict)
    db.finish_indexing()
    print "Most_common(10)", setarr_count.most_common(10)
    out = open(args.dir+"/"+'set_dict.pickle','wb')
    pickle.dump([set_dict, setarr_count], out)
    out.close()

