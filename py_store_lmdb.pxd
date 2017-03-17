cdef extern from "store_lmdb.h":
    cdef cppclass LMDB_Store:
        int open_db(const char *name)
        int start_transaction()
        int restart_transaction()
        int finish_indexing()
        int store_tree_flag(unsigned int tree_id, unsigned int flag_number)
        int store_tree_data(unsigned int tree_id, void *t_data, int size)
        int store_key_tree(unsigned int tree_id, void *key_data, int key_size)
        int store_tree_flag_val(unsigned int tree_id, unsigned int flag_number)
        int incerement_a_vocab_item_count(void *key_data, int key_size)
        int store_a_vocab_item(void *key_data, int key_size)

cdef class Py_LMDB:
    cdef LMDB_Store *thisptr
