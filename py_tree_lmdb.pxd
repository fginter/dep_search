from libc.stdint cimport uint16_t

cdef extern from "tree_lmdb.h":
    cdef cppclass Tree:
        uint16_t zipped_tree_text_length
        void deserialize(void *serialized_data)

cdef class Py_Tree:
    cdef Tree *thisptr

