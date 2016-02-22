from libcpp cimport bool
from libc.stdint cimport uint16_t
from libc.stdint cimport uint32_t


cdef extern from "tset.h" namespace "tset":
    cdef cppclass TSet:
        int tree_length
        TSet(int) except +
        void intersection_update(TSet *)
        void minus_update(TSet *)
        void union_update(TSet *)
        void add_item(int)
        bool has_item(int)
        void start_iteration()
        bool next_item(TSet *)
        char * get_data_as_char(int *)
        void deserialize(const void *)
        void erase()
        void set_length(int tree_length)
        void print_set()
        void copy(TSet *other)
    cdef cppclass TSetArray:
        void deserialize(const void *data, int size)
        void erase()
        void set_length(int tree_length)
        void print_array()
        void union_update(TSetArray *other)
        void intersection_update(TSetArray *other)
        void copy(TSetArray *other)

cdef extern from "tree_lmdb.h":
    cdef cppclass Tree:
        uint16_t zipped_tree_text_length
        void deserialize(void *serialized_data)
        int fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count)

cdef extern from "fetch_lmdb.h":
    cdef cppclass LMDB_Fetch:
        Tree *tree
        int open_env(const char *)
        int open_dbs()
        int start_transaction()
        int set_search_cursor_key(unsigned int)
        int cursor_get_next_tree_id(unsigned int)
        int cursor_get_next_tree(unsigned int)
        int cursor_load_tree()
        bool check_current_tree(uint32_t *, int , uint32_t *, int)
        int get_next_fitting_tree(uint32_t, uint32_t[], int , uint32_t[], int)
        uint32_t* get_first_fitting_tree()
        uint32_t* get_next_fitting_tree()
        void set_set_map_pointers(int ls, int la, uint32_t *lsets, uint32_t* larrays, uint32_t rarest)

cdef class DB:
    cdef LMDB_Fetch *thisptr
    #cdef void fill_tset(self, TSet *out, int column_index, int tree_length)
    #cdef void fill_tsetarray(self, TSetArray *out, int column_index, int tree_length)
    cpdef int next(self)
    #cdef void fill_sets(self, void **set_pointers, int *types, int size)
    cdef int fill_sets(self, void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size)
    cdef int get_integer(self, int column_index)
    cpdef int get_first_tree(self)
    cpdef int get_next_tree(self)

    
cdef int TSET=1
cdef int TSETARRAY=2
