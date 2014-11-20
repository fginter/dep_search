# distutils: language = c++
# distutils: include_dirs = setlib
# distutils: sources = setlib/tset.cpp query_functions.cpp

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

    cdef cppclass TSetArray:
        int tree_length
        int array_len
        TSetArray(int length) except +
        void intersection_update(TSetArray *other)
        void union_update(TSetArray *other)
        void erase()
        void get_set(int index, TSet *result)
        void deserialize(const void *data, int size)
        void print_array()
        void erase()
        void set_length(int tree_length)

cdef extern from "query_functions.h":
    void pairing(TSet *index_set, TSet *other_set, TSetArray *mapping, bool negated)

cdef class Search:  # base class for all searches
    cdef void **sets  #Pointers to stuff coming from the DB: array 1 and set 2 (we don't need 0)
    cdef int *set_types

    cdef TSet* exec_search(self):
        pass

    cdef initialize(self):
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
                
cdef class  SimpleSearch(Search):
    """
    V <aux V
    0   1  2 <--- set number for variable names below
    """

    cdef TSet *set0 #declare the sets needed in the query
    cdef TSetArray *seta1
    cdef TSet *set2
    cdef public object query_fields

    def __cinit__(self):
        #This runs only once per search, creates the data structures, etc.
        self.sets=<void**>malloc(3*sizeof(void*))
        self.set_types=<int*>malloc(3*sizeof(int))
        self.set_types[0],self.set_types[1],self.set_types[2]=1,2,1 #Types of stuff we grab from the DB, so we'll be grabbing 1 and 2, i.e. array and set
        self.set0,self.seta1,self.set2=new TSet(312), new TSetArray(312), new TSet(312) ## all sets needed in the query must be created 
        self.sets[0]=self.set0
        self.sets[1]=self.seta1 #...feed the pointers into the sets[] array so the DB can fill them with data for us
        self.sets[2]=self.set2 #...
        self.query_fields=[u"!tag_s_POS_Num",u"!dep_a_num",u"!tag_s_POS_N"] #we want the sentence to have an aux and a V (these fields must come in the order in which sets[] and set_types[] come)

    cdef initialize(self):
        """Called before every sentence to be processed, but after data has
        been fetched from the DB. Must initialize sets which are not
        fetched from the DB. Be efficient here, whatever you do!

        """
        #We don't have tree_ and arrat_lengths, so we can grab them
        #from some of the sets we got from the DB
        #self.set0.tree_length=self.set2.tree_length
        #self.set0.array_len=self.set2.array_len
        #self.set0.fill_ones()
        #set1 and set2 we get from the DB, so no need to mess with them
        pass

    cdef TSet* exec_search(self):
        """
        This runs the actual query. I.e. initialize() has been called for us and all sets are filled with valid data.
        """
        #self.set0.print_set()
        #self.seta1.print_array()
        #self.set2.print_set()
        pairing(self.set0,self.set2,self.seta1,False) #Filter set0 by set2 through the seta1 mapping
        #print "Filtered"
        #self.set0.print_set()
        #print "^^"
        #print
        return self.set0 #...and that's where we have the result

cdef class  ParSearch(Search):

    cdef TSet *noun_set #declare the sets needed in the query
    cdef TSet *par_set
    cdef TSet *all_tokens
    cdef TSet *all_tokens2
    cdef TSet *all_tokens3
    cdef TSetArray *num_mapping
    cdef TSetArray *obj_mapping
    cdef TSetArray *subj_mapping
    cdef TSetArray *xcomp_mapping
    cdef TSetArray *iccomp_mapping

    cdef public object query_fields

    def __cinit__(self):
        #This runs only once per search, creates the data structures, etc.
        self.sets=<void**>malloc(7*sizeof(void*))
        self.set_types=<int*>malloc(7*sizeof(int))
        self.set_types[0],self.set_types[1],self.set_types[2],self.set_types[3],self.set_types[4],self.set_types[5],self.set_types[6]=1,1,2,2,2,2,2 #Types of stuff we grab from the DB, so we'll be grabbing 1 and 2, i.e. array and set


        self.noun_set,self.par_set,self.all_tokens,self.all_tokens2,self.all_tokens3=new TSet(312), new TSet(312), new TSet(312), new TSet(312), new TSet(312) ## all sets needed in the query must be created 
        self.num_mapping, self.obj_mapping, self.subj_mapping, self.xcomp_mapping, self.iccomp_mapping = new TSetArray(312), new TSetArray(312), new TSetArray(312), new TSetArray(312), new TSetArray(312)

        self.sets[0]=self.noun_set
        self.sets[1]=self.par_set #...feed the pointers into the sets[] array so the DB can fill them with data for us
        self.sets[2]=self.num_mapping #...
        self.sets[3]=self.obj_mapping
        self.sets[4]=self.subj_mapping
        self.sets[5]=self.xcomp_mapping
        self.sets[6]=self.iccomp_mapping
        self.query_fields=[u"!tag_s_POS_N",u"!tag_s_CASE_Par",u"gov_a_num",u"!gov_a_dobj",u"!gov_a_nsubj",u"dep_a_xcomp",u"dep_a_iccomp"] #we want the sentence to have an aux and a V (these fields must come in the order in which sets[] and set_types[] come)

    cdef initialize(self):
        """Called before every sentence to be processed, but after data has
        been fetched from the DB. Must initialize sets which are not
        fetched from the DB. Be efficient here, whatever you do!

        """
        #We don't have tree_ and arrat_lengths, so we can grab them
        #from some of the sets we got from the DB
        self.all_tokens.set_length(self.noun_set.tree_length)
        self.all_tokens.fill_ones()
        self.all_tokens2.set_length(self.noun_set.tree_length)
        self.all_tokens2.fill_ones()
        self.all_tokens3.set_length(self.noun_set.tree_length)
        self.all_tokens3.fill_ones()

    cdef TSet* exec_search(self):
        """
        This runs the actual query. I.e. initialize() has been called for us and all sets are filled with valid data.
        """
        
        #print "num array:"
        #self.num_mapping.print_array()
        #print "xcomp array:"
        #self.xcomp_mapping.print_array()
        #print "iccomp array:"
        #self.iccomp_mapping.print_array()

        # 1) calc N+Par set (subj token)
        self.noun_set.intersection_update(self.par_set)

        # 2) calculate !Par+num and do minus wrt. subj token
        self.all_tokens.minus_update(self.par_set)
        pairing(self.noun_set,self.all_tokens,self.num_mapping,True)

        # 3) calc obj token
        pairing(self.all_tokens2,self.par_set,self.obj_mapping,False)
        
        # 3) some kind of mapping between subj token head and obj token head
        pairing(self.all_tokens2,self.noun_set,self.subj_mapping,False)

        # 4) minus xcomp and iccomp
        pairing(self.all_tokens2,self.all_tokens3,self.xcomp_mapping,True)
        pairing(self.all_tokens2,self.all_tokens3,self.iccomp_mapping,True)

        return self.all_tokens2 #...and that's where we have the result

