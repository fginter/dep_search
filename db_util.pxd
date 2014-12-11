from libcpp cimport bool

#...import stuff from this header file
cdef extern from "sqlite3.h":
    int sqlite3_bind_parameter_count(sqlite3_stmt*)
    int sqlite3_open_v2(const char *filename, sqlite3 **ppDb, int flags, const char *zvfs) 
    int sqlite3_close_v2(sqlite3*)
    int sqlite3_finalize(sqlite3_stmt *pStmt)
    int sqlite3_prepare_v2(sqlite3 *db, const char *zSql, int nByte, sqlite3_stmt **ppStmt, const char **pzTail)
    int sqlite3_step(sqlite3_stmt*)
    const void * sqlite3_column_blob(sqlite3_stmt*, int)
    int sqlite3_column_type(sqlite3_stmt*, int iCol)
    int sqlite3_column_bytes(sqlite3_stmt*, int iCol)
    int sqlite3_bind_text(sqlite3_stmt*,int iCol,const char* val,int len, void(*)(void*))
    int sqlite3_column_int(sqlite3_stmt*, int iCol)
    const char * sqlite3_errmsg(sqlite3 *)
    struct sqlite3: #Defines the type. We never touch it directly, so an empty struct is apparently enough
        pass     
    struct sqlite3_stmt:
        pass
    int SQLITE_OK
    int SQLITE_DONE
    int SQLITE_ROW
    int SQLITE_OPEN_READONLY
    int SQLITE_NULL
    int SQLITE_BLOB
    

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

cdef class DB:
    cdef sqlite3 *db #Pointer to the open DB
    cdef sqlite3_stmt *stmt # Pointer to a prepared statement
    cdef void fill_tset(self, TSet *out, int column_index, int tree_length)
    cdef void fill_tsetarray(self, TSetArray *out, int column_index, int tree_length)
    cpdef int next(self)
    cdef void fill_sets(self, void **set_pointers, int *types, int size)
    cdef int get_integer(self, int column_index)
    
cdef int TSET=1
cdef int TSETARRAY=2
