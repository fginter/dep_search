# distutils: language = c++
# distutils: sources = store_lmdb.cpp
# distutils: libraries = lmdb

import ctypes
from libc.stdint cimport uint32_t
cdef class Py_LMDB:
    #cdef LMDB *thisptr ## defined in .pxd

    def __cinit__(self):
        self.thisptr = new LMDB_Store()

    def open(self,name):
        self.thisptr.open_db(name)

    def start_transaction(self):
        self.thisptr.start_transaction()

    def finish_indexing(self):
        self.thisptr.finish_indexing()
    
    def store_tree_flag(self, unsigned int tree_id, unsigned int flag_number):
        self.thisptr.store_tree_flag(tree_id, flag_number);

    def store_key_tree(self, unsigned int tree_id, unicode key):
        key8=key.encode("utf-8")
        self.thisptr.store_key_tree(tree_id, <void*> key8, len(key8));

    def store_tree_flag_val(self, unsigned int tree_id, unsigned int flag_number):
        self.thisptr.store_tree_flag_val(tree_id, flag_number);

    def store_tree_data(self, unsigned int tree_id, char* t_data, int size):
        self.thisptr.store_tree_data(tree_id, <void *> t_data, size)

    def incerement_a_vocab_item_count(self, unicode key):
        cdef bytes key8=key.encode("utf-8")
        cdef char* c_string=key8
        self.thisptr.incerement_a_vocab_item_count(c_string, len(key8))

    def store_a_vocab_item(self, unicode key):
        cdef bytes key8=key.encode("utf-8")
        cdef char* c_string=key8
        self.thisptr.store_a_vocab_item(c_string, len(key8))

    cpdef uint32_t get_id_for(self, unicode key):
        cdef bytes key8=key.encode("utf-8")
        cdef char* c_string=key8
        return self.thisptr.get_id_for(c_string, len(key8))

    def continue_and_get_max_tree_id(self):

        starting_token_id = self.thisptr.update_t_idx()
        max_tree_id = self.thisptr.get_max_tree_id()
        return starting_token_id, max_tree_id

      
