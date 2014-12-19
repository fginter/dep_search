# distutils: include_dirs = . ./liblmdb
# distutils: language = c++
# distutils: libraries = lmdb
# distutils: sources = tree_lmdb.cpp
# distutils: library_dirs = ./liblmdb


cdef class Py_LMDB:
    #cdef LMDB *thisptr ## defined in .pxd

    def __cinit__(self):
        self.thisptr = new LMDB()

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
    
