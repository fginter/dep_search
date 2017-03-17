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

cdef class DB:

    def __cinit__(self):
        self.thisptr= new LMDB_Fetch()

    #Solr_url is here now!
    cpdef open(self, solr_url):
        print >> sys.stderr, 'db_util:opening', solr_url
        #self.thisptr.open(db_name)

    cpdef close(self):
        print 'closing!'
        #self.thisptr.close()

    #Here's the modified begin_search, pretty simple changes, huh?
    cpdef begin_search(self, extras_dict, compulsory_items, noncompulsory_items):

        #I have no idea if non_compulsory items provides any value, but its here nonetheless
        print 'compulsory', compulsory_items
        print 'voluntary', noncompulsory_items
        print 'extras', extras_dict

        #This, I guess, is the place in which the list of tree_ids will appear.

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
    


