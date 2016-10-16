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

    cpdef open(self,unicode db_name):
        print >> sys.stderr, 'db_util:opening', db_name
        self.thisptr.open(db_name)

    cpdef close(self):
        print 'closing!'
        self.thisptr.close()

    cpdef begin_search(self, sets, arrays, int rarest):

    	#array for sets
        cdef uint32_t *sets_array = <uint32_t *>malloc(len(sets) * sizeof(uint32_t))
        for i, s in enumerate(sets):
            sets_array[i] = s
	    
        cdef uint32_t *maps_array = <uint32_t *>malloc(len(arrays) * sizeof(uint32_t))
        for i, s in enumerate(arrays):
            maps_array[i] = s

        self.thisptr.begin_search(len(sets), len(arrays), sets_array, maps_array, rarest)

    cpdef int get_next_fitting_tree(self):
        return self.thisptr.get_next_fitting_tree()

    cdef int fill_sets(self, void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size):
        tree  = self.thisptr.tree
        return tree.fill_sets(set_pointers, indices, types, optional, size)

    cdef bool finished(self):
        return self.thisptr.finished

    
    def get_tree_text(self):
        cdef Tree * tree  = self.thisptr.tree
        cdef char * tree_text_data=tree.zipped_tree_text
        return zlib.decompress(tree_text_data[:tree.zipped_tree_text_length])
    


