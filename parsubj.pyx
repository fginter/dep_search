# distutils: language = c++
# distutils: include_dirs = setlib
# distutils: extra_objects = setlib/pytset.so
# distutils: sources = query_functions.cpp
include "search_common.pxi"

cdef class  GeneratedSearch(Search):

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


        self.noun_set,self.par_set,self.all_tokens,self.all_tokens2,self.all_tokens3=new TSet(2048), new TSet(2048), new TSet(2048), new TSet(2048), new TSet(2048) ## all sets needed in the query must be created 
        self.num_mapping, self.obj_mapping, self.subj_mapping, self.xcomp_mapping, self.iccomp_mapping = new TSetArray(2048), new TSetArray(2048), new TSetArray(2048), new TSetArray(2048), new TSetArray(2048)

        self.sets[0]=self.noun_set
        self.sets[1]=self.par_set #...feed the pointers into the sets[] array so the DB can fill them with data for us
        self.sets[2]=self.num_mapping #...
        self.sets[3]=self.obj_mapping
        self.sets[4]=self.subj_mapping
        self.sets[5]=self.xcomp_mapping
        self.sets[6]=self.iccomp_mapping
        self.query_fields=[u"!tag_s_POS_N",u"!tag_s_CASE_Par",u"gov_a_num",u"!gov_a_dobj",u"!gov_a_nsubj",u"dep_a_xcomp",u"dep_a_iccomp"] #we want the sentence to have an aux and a V (these fields must come in the order in which sets[] and set_types[] come)

    cdef void initialize(self):
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

