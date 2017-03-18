# distutils: include_dirs = . setlib
# distutils: language = c++
# distutils: libraries = lmdb
# distutils: sources = setlib/tset.cpp
# distutils: sources = [fetch_lmdb.cpp, tree_lmdb.cpp, fetch_lmdb.cpp, setlib/tset.cpp]

import os
from libcpp cimport bool
from libc.stdlib cimport malloc, free
#http://www.sqlite.org/cintro.html
from setlib.pytset cimport PyTSet, PyTSetArray 
import ctypes
from libc.stdint cimport uint32_t
import struct
import json
import zlib
import sys
import requests
import re
import StringIO

field_re=re.compile(ur"^(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
cdef class DB:

    def __cinit__(self):
        self.thisptr= new LMDB_Fetch()

    #Solr_url is here now!
    cpdef open(self, solr_url, db_name):
        print >> sys.stderr, 'db_util:opening', solr_url
        self.thisptr.open(db_name)

    cpdef close(self):
        print 'closing!'
        self.thisptr.close()

    cpdef get_ids_from_solr(self,extras_dict, compulsory_items,solr):
        terms=[]
        for c in compulsory_items:
            match=field_re.match(c)
            assert match, ("Not a known field description", c)
            if match.group(1) in (u"gov",u"dep"):
                terms.append(u'+relations:"%s"'%match.group(3))
            elif match.group(1)==u"tag":
                terms.append(u'+feats:"%s"'%match.group(3))
            elif match.group(1)==u"lemma":
                terms.append(u'+lemmas:"%s"'%match.group(3))
            elif match.group(1)==u"token":
                terms.append(u'+words:"%s"'%match.group(3))
        qry=u" ".join(terms)
        #### XXX TODO How many rows?
        r=requests.get(solr+"/select",params={u"q":qry,u"wt":u"csv",u"rows":500000,u"fl":u"id",u"sort":u"id asc"})
        row_count=r.text.count(u"\n")-1 #how many lines? minus one header line
        cdef uint32_t *id_array=<uint32_t *>malloc(row_count*sizeof(uint32_t))
        r_txt=StringIO.StringIO(r.text)
        col_name=r_txt.next() #column name
        assert col_name==u"id\n", repr(col_name)
        for idx,id in enumerate(r_txt):
            assert idx<row_count, (idx,row_count)
            id_array[idx]=int(id)
        print "Hits from solr:", row_count
        self.thisptr.tree_ids=id_array
        self.thisptr.tree_ids_count=row_count

        for idx in range(row_count):
            print id_array[idx]
        print
        
    cpdef bool has_id(self, unicode key):
        cdef bytes key8=key.encode("utf-8")
        cdef char* c_string=key8
        #self.thisptr.store_a_vocab_item(<void*> key8, len(key8))  
        self.thisptr.get_id_for(c_string, len(key8))
        return self.thisptr.has_id(c_string, len(key8))

    #Here's the modified begin_search, pretty simple changes, huh?
    #XXX TODO Need solr address here
    cpdef begin_search(self, extras_dict, compulsory_items, noncompulsory_items):

        #I have no idea if non_compulsory items provides any value, but its here nonetheless
        print 'compulsory', compulsory_items
        print 'voluntary', noncompulsory_items
        print 'extras', extras_dict

        #This, I guess, is the place in which the list of tree_ids will appear.

        self.get_ids_from_solr(extras_dict,compulsory_items,"http://localhost:8983/solr/dep_search")
        '''
    	#array for sets
        cdef uint32_t *sets_array = <uint32_t *>malloc(len(sets) * sizeof(uint32_t))
        for i, s in enumerate(sets):
            sets_array[i] = s
	    
        cdef uint32_t *maps_array = <uint32_t *>malloc(len(arrays) * sizeof(uint32_t))
        for i, s in enumerate(arrays):
            maps_array[i] = s

        self.thisptr.begin_search(len(sets), len(arrays), sets_array, maps_array, rarest)
        '''

    cpdef int get_next_fitting_tree(self):
        return self.thisptr.get_next_fitting_tree()

    cdef int fill_sets(self, void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size):
        tree  = self.thisptr.tree
        return tree.fill_sets(set_pointers, indices, types, optional, size)

    cdef bool finished(self):
        return self.thisptr.finished

    cpdef uint32_t get_id_for(self, unicode key):

        cdef bytes key8=key.encode("utf-8")
        cdef char* c_string=key8
        #self.thisptr.store_a_vocab_item(<void*> key8, len(key8))  
        self.thisptr.get_id_for(c_string, len(key8))
        return self.thisptr.get_tag_id()

    cpdef uint32_t get_count_for(self, int idx):
         self.thisptr.get_count_for(<uint32_t>idx)
         return self.thisptr.get_count()


    def get_tree_text(self):
        cdef Tree * tree  = self.thisptr.tree
        cdef char * tree_text_data=tree.zipped_tree_text
        return zlib.decompress(tree_text_data[:tree.zipped_tree_text_length])
    


