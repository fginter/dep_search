from libc.stdint cimport uint16_t

cdef extern from "tree_lmdb.h":
    cdef cppclass Tree:
        uint16_t tree_length

cdef class Py_Tree:
    cdef Tree *thisptr

