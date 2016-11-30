from libcpp cimport bool
from db_util cimport DB
from setlib.pytset cimport PyTSet, PyTSetArray
from libc.stdlib cimport malloc

cdef extern from "tset.h" namespace "tset":
    cdef cppclass TSet:
        int tree_length
        int array_len
        TSet(int) except +
        void intersection_update(TSet *)
        void minus_update(TSet *)
        void union_update(TSet *)
        void add_item(int)
        bool has_item(int)
        void fill_ones()
        bool is_empty()
        void print_set()
        void erase()
        void set_length(int tree_length)
        void complement()
        void copy(TSet *other)

    cdef cppclass TSetArray:
        int tree_length
        int array_len
        TSetArray(int length) except +
        void intersection_update(TSetArray *other)
        void union_update(TSetArray *other)
        void minus_update(TSetArray *other)
        void erase()
        void get_set(int index, TSet *result)
        void deserialize(const void *data, int size)
        void print_array()
        void set_length(int tree_length)
        void copy(TSetArray *other)
        void filter_direction(bool direction)
        void make_lin(int window)
        void make_lin_2(int window, int begin)

        void extend_subtrees(TSetArray* other)
        void add_arch(int a, int b)
        TSet get_all_children(int id, TSet * other)



cdef extern from "query_functions.h":
    void pairing(TSet *index_set, TSet *other_set, TSetArray *mapping, bool negated)


cdef class Search:  # base class for all searches
    cdef void **sets  #Pointers to stuff coming from the DB: array 1 and set 2 (we don't need 0)
    cdef int *set_types

    cdef TSet* exec_search(self):
        pass

    cdef void initialize(self):
        pass

    def next_result(self, DB db):
        cdef int size=len(self.query_fields)
        cdef PyTSet py_result=PyTSet(0)
        cdef TSet *result
        cdef int graph_id
        cdef int rows=0
        while db.next()==0:
            rows+=1
            graph_id=db.get_integer(0)
            db.fill_sets(self.sets,self.set_types,size)
            self.initialize()
            result=self.exec_search()
            if not result.is_empty():
                py_result.acquire_thisptr(result)
                return graph_id,py_result,rows
        return None,None,rows
