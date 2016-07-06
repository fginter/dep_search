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

cdef class DB:

    def __cinit__(self):
        self.thisptr= new LMDB_Fetch()

    def open_db(self,unicode db_name):

        #print 'opening', db_name
        self.thisptr.open_env(db_name)
        self.thisptr.open_dbs()
        self.thisptr.start_transaction()

        '''
        db_name_u8=db_name.encode("utf-8") #Need to make a variable for this one, because .encode() produces only a temporary object
        sqlite3_open_v2(db_name_u8,&self.db,SQLITE_OPEN_READONLY,NULL)
        '''
        pass

    def close_db(self):
        pass#print >> sys.stderr,  "DB CLOSE:", sqlite3_close_v2(self.db)


    def set_set_map_pointers(self, sets, arrays, int rarest):

        cdef uint32_t *my_array = <uint32_t *>malloc(len(sets) * sizeof(uint32_t))
        for i, s in enumerate(sets):
            my_array[i] = s

        cdef uint32_t *my_array_m = <uint32_t *>malloc(len(arrays) * sizeof(uint32_t))
        for i, s in enumerate(arrays):
            my_array_m[i] = s

        #Iset_arr = (uint32_t * len(sets))(*sets)
        #arr_arr = (uint32_t * len(array))(*arrays)
        #cdef uint32_t * setp = <uint32_t *>set_arr
        self.thisptr.set_set_map_pointers(len(sets), len(arrays), my_array, my_array_m, rarest)

    cpdef int get_first_tree(self):
        ptr = self.thisptr.get_first_fitting_tree()
        if ptr != NULL:
            return (<int*>ptr)[0]
        else:
            return -1
    '''
    cpdef int get_next_tree(self):
        ptr = self.thisptr.get_next_fitting_tree()
        if ptr != NULL:
            return (<int*>ptr)[0]
        else:
            return -1
     
    cdef int get_first_tree(self):
        ptr = self.thisptr.get_first_fitting_tree()
        if ptr != NULL:
            return 0#(<Tree*>ptr)
        else:
            return 1#ptr
    '''

    cpdef int hextree_from_db(self, tree_id):
        self.thisptr.get_a_treehex(tree_id)
        return 1

    cpdef int get_next_tree(self):
        ptr = self.thisptr.get_next_fitting_tree()
        if ptr != NULL:
            return (<int*>ptr)[0]
        else:
            return -1

    #cpdef uint32_t* get_current_tree_id(self):
    #    tree_id = self.thisptr.get_current_tree_id()
    #    return tree_id

    def exec_query(self, int rarest):
        self.thisptr.set_search_cursor_key(rarest)

        #pass
        #Find the rarest id out of these
        #set_search_cursor_key(unsigned int flag)

        """Runs sqlite3_prepare, use .next() to iterate through the rows. Args is a list of *UNICODE* arguments to bind to the query
        cdef unicode a
        cdef int idx
        query_u8=query.encode("utf-8")
        cdef char* txt=query_u8
        result=sqlite3_prepare_v2(self.db,query_u8,len(query_u8),&self.stmt,NULL)
        if result!=SQLITE_OK:
            print sqlite3_errmsg(self.db)
            return False, result
        for idx,a in enumerate(args):
            a_u8=a.encode("utf-8")
            result=sqlite3_bind_text(self.stmt,idx+1,a_u8,len(a_u8),<void(*)(void*)>-1) #the last param is from SQLite headers
            if result!=SQLITE_OK:
                print sqlite3_errmsg(self.db)
                return False, result
        return True, 0
        """
        return 1
    cpdef int next(self):
        """
        cdef int result = sqlite3_step(self.stmt)
        if result==SQLITE_ROW:
            return 0
        elif result==SQLITE_DONE:
            sqlite3_finalize(self.stmt)
            return 1
        else:
            print >> sys.stderr, sqlite3_errmsg(self.db)            
            return result
        """
        return 1

    #cdef void fill_tset(self,TSet *out, int column_index, int tree_length):
    #    pass
        """
        cdef const void *data
        data_type=sqlite3_column_type(self.stmt,column_index)
        if data_type==SQLITE_BLOB:
            data=sqlite3_column_blob(self.stmt, column_index)
            out.deserialize(data)
        else:
            out.set_length(tree_length)
            out.erase()
        """
    #cdef void fill_tsetarray(self, TSetArray *out, int column_index, int tree_length):
    #    pass
        """
        cdef int blob_len
        cdef const void *data
        data_type=sqlite3_column_type(self.stmt,column_index)
        if data_type==SQLITE_BLOB:
            data=sqlite3_column_blob(self.stmt,column_index)
            blob_len=sqlite3_column_bytes(self.stmt, column_index);
            out.deserialize(data,blob_len)
        else:
            out.set_length(tree_length)
            out.erase()
        """
    #def fill_pytset(self, PyTSet s, int column_index, int tree_length):
    #    pass#self.fill_tset(s.thisptr, column_index, tree_length)

    #def fill_pytsetarray(self, PyTSetArray s, int column_index, int tree_length):
    #    pass#self.fill_tsetarray(s.thisptr, column_index, tree_length)

    cdef int get_integer(self, int column_index):
        return 1#sqlite3_column_int(self.stmt, column_index)

    cdef int fill_sets(self, void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size):
        tree  = self.thisptr.tree
        return tree.fill_sets(set_pointers, indices, types, optional, size)

    def get_tree_text(self):

        tree  = self.thisptr.tree
        tree_text = ''
        for i in range(tree.zipped_tree_text_length):
            tree_text += <char*>self.thisptr.tree.zipped_tree_text[i]
        return tree_text


    #Yeah, a weird place for this!
    cdef int print_sets(self, void **set_pointers, unsigned char *types, int size):
        tree  = self.thisptr.tree
        return tree.print_sets(set_pointers, types, size)

        """
        cdef int i
        cdef int col_index
        cdef int tree_length = sqlite3_column_int(self.stmt, 1)
        for i in range(size):
            col_index=i+2
            if types[i]==1: # TODO fix constant
                self.fill_tset(<TSet *>set_pointers[i],col_index,tree_length)
            elif types[i]==2:
                self.fill_tsetarray(<TSetArray *>set_pointers[i],col_index,tree_length)
            else:
                print "C",types[i]
                assert False
        """
            

