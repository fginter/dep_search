#from query import Query
#import lex as lex
#import yacc as yacc
#import re
from expr import *
import sys


class node_code_block():

    def __init__(self, blocks, pseudo_node, node_id):

        self.node_id = node_id
        self.pseudo_node = pseudo_node
        self.operation_blocks = blocks
        self.end_block = []

class intersect_code_block():

    def __init__(self, set1, set2):

        self.set1 = set1
        self.set2 = set2

    def to_string(self):
        return 'Intersect' + str((self.set1, self.set2))

class pair_code_block():
    #(rest, set1, set2, operation, type, negated=False)
    def __init__(self, rest, set1, set2, operation, optype, negated=False):

        self.restriction = rest
        self.set1 = set1#''
        self.set2 = set2#''
        self.operation = operation#''
        self.needed_from_db = []
        self.negated = negated
        self.optype = optype

    def to_string(self):
        return 'Pair' + str((self.set1, self.set2, self.operation, self.optype, self.negated))


class retrieve_from_db_code_block():

    def __init__(self, needed):
        self.what_to_retrieve = needed

    def to_string(self):
        return 'Get_from_db' + str((self.what_to_retrieve))

class end_search_block():

    def __init__(self):
        self.code = '#ENDBLOCK'


class end_node_block():

    def __init__(self, node_id):
        self.node_id = node_id

    def to_string(self):
        return 'output_' + self.node_id + '=f_set'


class code():

    def __init__(self, original_node):

        self.original_node = original_node
        self.process_node(self.original_node)
        #Match Function
        self.match_code = self.get_match_function()
        #What is needed from the dictionary
        self.text_needs_comp, self.text_needs_vol, self.pair_needs_comp, self.pair_needs_vol = self.get_what_is_needed_from_db()

        print 'Done!'

    def print_pseudo_code(self):
        #Print what is needed from the db
        print 'What is needed from the db:'
        print '  compulsory text/tags:'
        for rest in self.text_needs_comp:
            print ' '*4 + str(rest)
        print '  non-compulsory text/tags:'
        for rest in self.text_needs_vol:
            print ' '*4 + str(rest)
        print '  compulsory deplists:'
        for rest in self.pair_needs_comp:
            print ' '*4 + str(rest)
        print '  non-compulsory deplists:'
        for rest in self.pair_needs_vol:
            print ' '*4 + str(rest)

        print
        print 'Match Function:'

        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            #Humm, It could've been more simple
            print '  #Node:' + node_id
            for i, block in enumerate(node.operation_blocks):
                print ' '*2 + 'set_' + node_id + ' = ' + block.to_string()
                if compulsory_node and i not in [0, len(node.operation_blocks)]:
                    print ' '*2 + 'if self.set_' + node_id + '.is_empty(): return self.set_' + node_id
        print ' '*2 + 'return set_' + node_id




    def get_search_code(self):


        #Stuff to collect
        #1. list of node_id sets and how theyre initialized
        #2. sets from the db
        #3. arrays from the db
        #4. all sets
        #5. all arrays
        #6. query fields

        node_sets_inits = []
        sets_from_the_db = []
        arrays_from_the_db = []
        all_sets = []
        all_arrays = set()
        query_fields = []

        intersection_sets = set()


        #print 'What is needed from the db:'
        #print '  compulsory text/tags:'
        #for rest in self.text_needs_comp:
        #    print ' '*4 + str(rest)
        #print '  non-compulsory text/tags:'
        #for rest in self.text_needs_vol:
        #    print ' '*4 + str(rest)
        #print '  compulsory deplists:'
        #for rest in self.pair_needs_comp:
        #    print ' '*4 + str(rest)
        #print '  non-compulsory deplists:'
        #for rest in self.pair_needs_vol:
        #    print ' '*4 + str(rest)
        #print
        #print '#Match Function:'

        match_function = []


        match_function.append( '    cdef TSet* exec_search(self):')
        #
        all_tokens = False

        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            #Humm, It could've been more simple
            match_function.append(' ' * 8 + '#Node:' + node_id)
            for i, block in enumerate(node.operation_blocks):
                #print ' '*2 + 'set_' + node_id + ' = ' + block.to_string()
                #Here we print the wanted operation
                #3 options;
                #    1) set introduction
                #    2) intersection update on the node set
                #    3) pairing update on the node set
                if isinstance(block, retrieve_from_db_code_block):
                    if block.what_to_retrieve != 'ALL TOKENS':
                        if type(block.what_to_retrieve) == tuple:
                            if block.what_to_retrieve[0] == '<':
                                #print ' ' * 8 + 'self.set_' + node_id + '=self.set_deps_' + str(block.what_to_retrieve[1])
                                node_sets_inits.append(('self.set_' + node_id, 'dep_s_' + str(block.what_to_retrieve[1])))
                                sets_from_the_db.append(('dep_s_' + str(block.what_to_retrieve[1]), compulsory_node))

                            else:
                                #print ' ' * 8 + 'self.set_' + node_id + '=self.set_govs_' + str(block.what_to_retrieve[1])
                                node_sets_inits.append(('self.set_' + node_id, 'gov_s_' + str(block.what_to_retrieve[1])))
                                sets_from_the_db.append(('gov_s_' + str(block.what_to_retrieve[1]), compulsory_node))
                        else:
                            #print ' ' * 8 + 'self.set_' + node_id + '=' + str(block.what_to_retrieve)
                            node_sets_inits.append(('self.set_' + node_id, str(block.what_to_retrieve)))
                            sets_from_the_db.append((str(block.what_to_retrieve), compulsory_node))
                    else:
                        #print ' ' * 8 + 'self.set_' + node_id + '.fill_ones()'
                        node_sets_inits.append(('self.set_' + node_id, 'fill_ones'))

                if isinstance(block, intersect_code_block):
                    #Which is the one that is not us

                    #import pdb;pdb.set_trace()
                    sets = set([block.set1, block.set2])
                    sets -= set(['self.set_' + node_id])
                    #sets = list(sets)
                    match_function.append(' ' * 8 + 'self.set_' + node_id + '.intersection_update(self.' + str(list(sets)[0]) + ')')
                    intersection_sets.add((str(list(sets)[0]), compulsory_node))
                    sets_from_the_db.append((str(list(sets)[0]), compulsory_node))

                if isinstance(block, pair_code_block):
                    pass
                    #The options here are:
                    #1. Deptype is defined
                    #2. Dep or Gov
                    #import pdb;pdb.set_trace()
                    if block.set2 is None:
                        #We need in this code an extra set which is always filled with ones!
                        #Lets call it self.all_tokens
                        block.set2='self.all_tokens'
                        if not all_tokens:
                            node_sets_inits.append(('self.all_tokens', 'fill_ones'))
                            all_tokens = True

                    if block.optype is None:
                        pass
                        #pairing(self.set0,self.set2,self.seta1,False)
                        #import pdb; pdb.set_trace()
                        #print 'block', block

                        #if block.set2 is None:
                        if block.operation == '<':
                            match_function.append( ' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.dep_a_anytype', str(block.negated)]) + ')')
                            all_arrays.add(('dep_a_anytype', not block.negated and compulsory_node))
                            
                        else:
                            match_function.append(' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.gov_a_anytype', str(block.negated)]) + ')')
                            all_arrays.add(('gov_a_anytype', not block.negated and compulsory_node))
                    else:
                        pass
                        if block.operation == '<':
                            match_function.append(' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.dep_a_'  + str(block.optype), str(block.negated)]) + ')')
                            all_arrays.add(('dep_a_'  + str(block.optype), not block.negated and compulsory_node))
                        else:
                            match_function.append(' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.gov_a_' + str(block.optype), str(block.negated)]) + ')')
                            all_arrays.add(('gov_a_' + str(block.optype), not block.negated and compulsory_node))                    


                if compulsory_node and i not in [0,1, len(node.operation_blocks)-1]:
                    match_function.append(' '*8 + 'if self.set_' + node_id + '.is_empty(): return self.set_' + node_id)
        match_function.append(' '*8 + 'return self.set_' + node_id)


        print
        #print '#Sets from the db'

        #import pdb;pdb.set_trace()

        #Initialize function

        #We need:
        #1.   At least one set from the db
        #1.5  init tree lengths
        #2.   Initialize the set_node_ids
        #2.5  init either fill_ones or db

        #get the first mentions
        t_inits_from_db = set()
        db_fetch_dict = {}

        #
        fill_ones = set()
        clone = set()
        cinit_load = set()

        for t in node_sets_inits:

            if t[1] == 'fill_ones':
                fill_ones.add(t)

            elif t[1] not in t_inits_from_db:
                db_fetch_dict[t[1]] = t[0]
                t_inits_from_db.add(t[1])
                cinit_load.add((t[0], t[1]))
            else:
                #print db_fetch_dict
                #import pdb;pdb.set_trace()
                clone.add((t[0], db_fetch_dict[t[1]]))


        #import pdb;pdb.set_trace()


        initialize_function = []


        initialize_function.append('''    cdef void initialize(self):
        """
        Called before every sentence to be processed. Must initialize sets which are not fetched from the DB. Be efficient here, whatever you do!
        """''')

        #For all node_id sets:
        #Does the set from the db have to be compulsory??
        initialize_function.append(' '*8 + 'pass')
#        for t in node_sets_inits:
#
#            print ' '*8 + t[0] + '.tree_length=' + sets_from_the_db[0][0] + '.tree_length'
#            print ' '*8 + t[0] + '.array_len=' + sets_from_the_db[0][0] + '.array_len'

        #clones and fill ones
        for t in clone:
            #initialize_function.append(' '*8 + t[0] + '.tree_length=' + sets_from_the_db[0][0] + '.tree_length')
            #initialize_function.append(' '*8 + t[0] + '.array_len=' + sets_from_the_db[0][0] + '.array_len')
            initialize_function.append(' '*8 + t[0] + '.copy(' + t[1] + ')')
        for t in fill_ones:
            if sets_from_the_db[0][0] in db_fetch_dict.keys():

                initialize_function.append(' '*8 + t[0] + '.tree_length=' + db_fetch_dict[sets_from_the_db[0][0]] + '.tree_length')
                initialize_function.append(' '*8 + t[0] + '.array_len=' + db_fetch_dict[sets_from_the_db[0][0]] + '.array_len')
            else:

                initialize_function.append(' '*8 + t[0] + '.tree_length=self.' + sets_from_the_db[0][0] + '.tree_length')
                initialize_function.append(' '*8 + t[0] + '.array_len=self.' + sets_from_the_db[0][0] + '.array_len')

            initialize_function.append(' ' * 8 + t[0] + '.fill_ones()')

        #__cinit__ function


        cinit_function = []
        class_block = []

        class_block.append('cdef class GeneratedSearch(Search):')

        #We need:
        #1.   query fields
        #2.   all sets and Arrays used
        #3.   sets and arrays from db

        #Count all db stuff
        #All db stuff is:
        #cinit_load + intersection_sets + all_arrays
        all_db_stuff_count = len(cinit_load) + len(intersection_sets) + len(all_arrays)

        cinit_function.append('''    def __cinit__(self):
        #This runs only once per search, creates the data structures, etc.
        self.sets=<void**>malloc(''' + str(all_db_stuff_count) + '''*sizeof(void*))
        self.set_types=<int*>malloc(''' + str(all_db_stuff_count) + '''*sizeof(int))''')

        #So I guess the first number is arrays and the second is the sets?
        #XXX:Figure out later

        #XXX: is query is seeded eith neg it doesnt work!

        #print ' ' * 8 + 'self.set_types[0],self.set_types[1]=2,1'

        #Init the sets used, both from db and node_id

        #All sets is node_id sets and sets_from_the db
        for t in node_sets_inits:
            cinit_function.append(' '*8 + t[0] + '=new TSet(312)')
            class_block.append(' '*4 + 'cdef TSet *' + t[0].split('.')[-1])

        for t in list(intersection_sets):
            cinit_function.append(' ' * 8 + 'self.' + t[0] + '=new TSet(312)')
            class_block.append(' '*4 + 'cdef TSet *' + t[0].split('.')[-1])

        #Init the arrays used

        #setify and compulsify arrays, haha
        all_arrays_set = set()
        compulsory_arrays = set()
        voluntary_arrays = set()

        for t in all_arrays:
            all_arrays_set.add(t[0])
            if t[1]:
                compulsory_arrays.add(t[0])
            else:
                voluntary_arrays.add(t[0])

        voluntary_arrays -= compulsory_arrays


        all_sets_set = set()
        compulsory_sets = set()
        voluntary_sets = set()

        for t in sets_from_the_db:
            all_sets_set.add(t[0])
            if t[1]:
                compulsory_sets.add(t[0])
            else:
                voluntary_sets.add(t[0])

        voluntary_sets -= compulsory_sets

        for array in list(all_arrays_set):
            cinit_function.append(' '*8 + 'self.' + array + '=new TSetArray(312)')

            class_block.append(' '*4 + 'cdef TSetArray *' + array)
        #Fill the self.sets and query fields
        #Youll need to regerate them from the restrictions
        class_block.append(' '*4 + 'cdef public object query_fields')
        #Query Fields
        #Oh, so all the stuff that is needed from the db
        #Start with sets and the arrays
        #sets
        sets_list = []
        q_fields = []
        set_types = []


        for cs in compulsory_sets:

            #The possibilities here
            #set_node_id
            #self. + cs
            if cs in db_fetch_dict.keys():
                sets_list.append(db_fetch_dict[cs])
            else:
                sets_list.append('self.' + cs)

            q_fields.append(u'!' + cs.split('.')[-1])
            set_types.append(1)
        for cs in voluntary_sets:
            if cs in db_fetch_dict.keys():
                sets_list.append(db_fetch_dict[cs])
            else:
                sets_list.append('self.' + cs)

            #if cs in db_fetch_dict.keys():
            #    sets_list.append(db_fetch_dict[cs])
            #else:
            #    sets_list.append('self.' + cs)

            q_fields.append(u'' + cs.split('.')[-1])
            set_types.append(1)
        for cs in compulsory_arrays:
            sets_list.append('self.' + cs)
            q_fields.append(u'!' + cs.split('.')[-1])
            set_types.append(2)
        for cs in voluntary_arrays:
            set_types.append(2)
            sets_list.append('self.' + cs)
            q_fields.append(u'' + cs)

        for i, cs in enumerate(sets_list):
            cinit_function.append(' '*8 + 'self.sets[' + str(i) + ']=' + cs)

        for i, cs in enumerate(set_types):
            cinit_function.append(' '*8 + 'self.set_types[' + str(i) + ']=' + str(cs))

        cinit_function.append(' '*8 + 'self.query_fields='+str(q_fields))



        print '\n'.join(class_block)
        print '\n'.join(match_function)
        print '\n'.join(initialize_function)
        print '\n'.join(cinit_function)

        return class_block + initialize_function + cinit_function + match_function



    def print_cython_match_function(self):


        #Stuff to collect
        #1. list of node_id sets and how theyre initialized
        #2. sets from the db
        #3. arrays from the db
        #4. all sets
        #5. all arrays
        #6. query fields

        node_sets_inits = []
        sets_from_the_db = []
        arrays_from_the_db = []
        all_sets = []
        all_arrays = set()
        query_fields = []


        #print 'What is needed from the db:'
        #print '  compulsory text/tags:'
        #for rest in self.text_needs_comp:
        #    print ' '*4 + str(rest)
        #print '  non-compulsory text/tags:'
        #for rest in self.text_needs_vol:
        #    print ' '*4 + str(rest)
        #print '  compulsory deplists:'
        #for rest in self.pair_needs_comp:
        #    print ' '*4 + str(rest)
        #print '  non-compulsory deplists:'
        #for rest in self.pair_needs_vol:
        #    print ' '*4 + str(rest)
        print
        print '#Match Function:'

        print '    cdef TSet* exec_search(self):'
        #

        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            #Humm, It could've been more simple
            print  ' ' * 8 + '#Node:' + node_id
            for i, block in enumerate(node.operation_blocks):
                #print ' '*2 + 'set_' + node_id + ' = ' + block.to_string()
                #Here we print the wanted operation
                #3 options;
                #    1) set introduction
                #    2) intersection update on the node set
                #    3) pairing update on the node set
                if isinstance(block, retrieve_from_db_code_block):
                    if block.what_to_retrieve != 'ALL TOKENS':
                        if type(block.what_to_retrieve) == tuple:
                            if block.what_to_retrieve[0] == '<':
                                #print ' ' * 8 + 'self.set_' + node_id + '=self.set_deps_' + str(block.what_to_retrieve[1])
                                node_sets_inits.append(('self.set_' + node_id, 'self.deps_s_' + str(block.what_to_retrieve[1])))
                                sets_from_the_db.append(('self.deps_s_' + str(block.what_to_retrieve[1]), compulsory_node))

                            else:
                                #print ' ' * 8 + 'self.set_' + node_id + '=self.set_govs_' + str(block.what_to_retrieve[1])
                                node_sets_inits.append(('self.set_' + node_id, 'self.govs_s_' + str(block.what_to_retrieve[1])))
                                sets_from_the_db.append(('self.govs_s_' + str(block.what_to_retrieve[1]), compulsory_node))
                        else:
                            #print ' ' * 8 + 'self.set_' + node_id + '=' + str(block.what_to_retrieve)
                            node_sets_inits.append(('self.set_' + node_id, str(block.what_to_retrieve)))
                            sets_from_the_db.append((str(block.what_to_retrieve), compulsory_node))
                    else:
                        #print ' ' * 8 + 'self.set_' + node_id + '.fill_ones()'
                        node_sets_inits.append(('self.set_' + node_id, 'fill_ones'))

                if isinstance(block, intersect_code_block):
                    #Which is the one that is not us

                    #import pdb;pdb.set_trace()
                    sets = set([block.set1, block.set2])
                    sets -= set(['self.set_' + node_id])
                    #sets = list(sets)
                    print ' ' * 8 + 'self.set_' + node_id + '.intersection_update(' + str(list(sets)[0]) + ')'

                if isinstance(block, pair_code_block):
                    pass
                    #The options here are:
                    #1. Deptype is defined
                    #2. Dep or Gov
                    #import pdb;pdb.set_trace()
                    if block.optype is None:
                        pass
                        #pairing(self.set0,self.set2,self.seta1,False)
                        #import pdb; pdb.set_trace()
                        #print 'block', block
                        if block.operation == '<':
                            print ' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.deps_a', str(block.negated)]) + ')'
                            all_arrays.add(('self.deps_a', not block.negated and compulsory_node))
                            
                        else:
                            print ' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.govs_a', str(block.negated)]) + ')'
                            all_arrays.add(('self.govs_a', not block.negated and compulsory_node))
                    else:
                        pass
                        if block.operation == '<':
                            print ' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.deps_a_'  + str(block.optype), str(block.negated)]) + ')'
                            all_arrays.add(('self.deps_a_'  + str(block.optype), not block.negated and compulsory_node))
                        else:
                            print ' '*8 + 'pairing(' + ','.join([str(block.set1), str(block.set2), 'self.govs_a_' + str(block.optype), str(block.negated)]) + ')'
                            all_arrays.add(('self.govs_a_' + str(block.optype), not block.negated and compulsory_node))                    


                if compulsory_node and i not in [0,1, len(node.operation_blocks)-1]:
                    print ' '*8 + 'if set_' + node_id + '.is_empty(): return set_' + node_id + str(i)
        print ' '*8 + 'return set_' + node_id


        print
        #print '#Sets from the db'

        #import pdb;pdb.set_trace()

        #Initialize function

        #We need:
        #1.   At least one set from the db
        #1.5  init tree lengths
        #2.   Initialize the set_node_ids
        #2.5  init either fill_ones or db

        import pdb;pdb.set_trace()



        print '''    cdef initialize(self):
        """
        Called before every sentence to be processed. Must initialize sets which are not fetched from the DB. Be efficient here, whatever you do!
        """'''

        #For all node_id sets:
        #Does the set from the db have to be compulsory??
        for t in node_sets_inits:
            print ' '*8 + t[0] + '.tree_length=' + sets_from_the_db[0][0] + '.tree_length'
            print ' '*8 + t[0] + '.array_len=' + sets_from_the_db[0][0] + '.array_len'

        for t in node_sets_inits:
            if t[1] != 'fill_ones':
                print ' ' * 8 + t[0] + '=' + t[1] 
            else:
                print ' ' * 8 + t[0] + '.fill_ones()' 


        #__cinit__ function

        #We need:
        #1.   query fields
        #2.   all sets and Arrays used
        #3.   sets and arrays from db


        print '''    def __cinit__(self):
        #This runs only once per search, creates the data structures, etc.
        self.sets=<void**>malloc(2*sizeof(void*))
        self.set_types=<int*>malloc(2*sizeof(int))'''

        #So I guess the first number is arrays and the second is the sets?
        #XXX:Figure out later

        #XXX: is query is seeded eith neg it doesnt work!

        #print ' ' * 8 + 'self.set_types[0],self.set_types[1]=2,1'

        #Init the sets used, both from db and node_id

        #All sets is node_id sets and sets_from_the db
        for t in node_sets_inits:
            print ' '*8 + t[0] + '=new TSet(312)'

        for t in sets_from_the_db:
            print ' ' * 8 + t[0] + '=new TSet(312)'

        #Init the arrays used

        #setify and compulsify arrays, haha
        all_arrays_set = set()
        compulsory_arrays = set()
        voluntary_arrays = set()

        for t in all_arrays:
            all_arrays_set.add(t[0])
            if t[1]:
                compulsory_arrays.add(t[0])
            else:
                voluntary_arrays.add(t[0])

        voluntary_arrays -= compulsory_arrays


        all_sets_set = set()
        compulsory_sets = set()
        voluntary_sets = set()

        for t in sets_from_the_db:
            all_sets_set.add(t[0])
            if t[1]:
                compulsory_sets.add(t[0])
            else:
                voluntary_sets.add(t[0])

        voluntary_sets -= compulsory_sets

        for array in list(all_arrays_set):
            print ' '*8 + array + '=new TSetArray(312)'        


        #Fill the self.sets and query fields
        #Youll need to regerate them from the restrictions

        #Query Fields
        #Oh, so all the stuff that is needed from the db
        #Start with sets and the arrays
        #sets
        sets_list = []
        q_fields = []
        set_types = []


        for cs in compulsory_sets:
            sets_list.append(cs)
            q_fields.append('!' + cs.split('.')[-1])
            set_types.append(1)
        for cs in voluntary_sets:
            sets_list.append(cs)
            q_fields.append(cs.split('.')[-1])
            set_types.append(1)
        for cs in compulsory_arrays:
            sets_list.append(cs)
            q_fields.append('!' + cs.split('.')[-1])
            set_types.append(2)
        for cs in voluntary_arrays:
            set_types.append(2)
            sets_list.append(cs.split('.')[-1])
            q_fields.append(cs)

        for i, cs in enumerate(sets_list):
            print ' '*8 + 'self.sets[' + str(i) + ']=' + cs

        for i, cs in enumerate(set_types):
            print ' '*8 + 'self.set_types[' + str(i) + ']=' + str(cs)

        print ' '*8 + 'self.query_fields='+str(q_fields)



    def get_what_is_needed_from_db(self):
        #Go through the nodes

        #In two categories:
        #1. The text requirements
        #2. What is needed for pairings
        text_needs = []
        pair_needs = []

        #Mark if the need is compulsory or not
        #If negs above, then it is not a compulsory need

        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            #Humm, It could've been more simple
            for block in node.operation_blocks:
               # import pdb;pdb.set_trace()
                if isinstance(block, pair_code_block):
                    #import pdb; pdb.set_trace()
                    #Dependency restriction
                    comp_res = not block.negated
                    if not comp_res or not compulsory_node:
                        if block.optype!=None:
                            pair_needs.append((block.optype ,False))
                        else:
                            pair_needs.append(('all_dep_gov', False))
                    else:
                        if block.optype!=None:
                            pair_needs.append((block.optype ,True))
                        else:
                            pair_needs.append(('all_dep_gov', True))

                if isinstance(block,intersect_code_block):
                    if 'set_' not in block.set1:
                        text_needs.append((block.set1, compulsory_node))
                    if 'set_' not in block.set2:
                        text_needs.append((block.set2, compulsory_node))
                if isinstance(block, retrieve_from_db_code_block):
                        if type(block.what_to_retrieve) == tuple:
                            pair_needs.append((block.what_to_retrieve, compulsory_node))
                        else:
                            text_needs.append((block.what_to_retrieve, compulsory_node))
        #Make sets
        text_needs_comp = set()
        text_needs_vol = set()
        pair_needs_comp = set()
        pair_needs_vol = set()
        for pair_need in pair_needs:
            if pair_need[1]:
                pair_needs_comp.add(pair_need[0])
            else:
                pair_needs_vol.add(pair_need[0])

        for txt_need in text_needs:
            if txt_need[1]:
                text_needs_comp.add(txt_need[0])
            else:
                text_needs_vol.add(txt_need[0])

        #Remove unnecessary
        pair_needs_vol -= pair_needs_comp
        text_needs_vol -= text_needs_comp
        return text_needs_comp, text_needs_vol, pair_needs_comp, pair_needs_vol


    def get_code(self):

        #match Function
        match_code = self.get_match_function()
        #init_function
        #init_function = self.get_init_function(db_list)

        output = ['class CustomSearch\n',]
        output.extend(init_function)
        output.extend(match_function)

        return output

    def get_match_function(self):

        node_codes = []

        #Start going through the nodes in order
        for node_id in self.order_of_execution:
            node = self.node_id_dict[node_id]
            pseudo_node = self.pseudo_nodes[node_id]

            if len(node.restrictions) < 1:
                continue
            node_codes.append(self.get_node_code(node_id))

        return node_codes
        #import pdb;pdb.set_trace()
        #the_code = []
        #for nc in node_codes:
        #    the_code.extend(nc)
        #return the_code

    def get_match_endgame(self):

        return  ['return XXX',]

    def get_node_code(self, node_id):

        #So Start collecting the node code blocks into this list
        operation_blocks = []

        #Here we are!
        break_exec_on_empty_set = self.no_negs_above_dict[node_id]

        #Grab the sets which need to be paired with each other
        sets_to_pair = []
        negated_sets_to_pair = []
        needed_from_the_dict = set()

        #Go through text restrictions
        #These will be intersected
        txt_what_sets_are_needed, txt_sets_to_intersect, needed_words = self.get_text_restrictions(node_id)

        #print txt_what_sets_are_needed, txt_sets_to_intersect, needed_words
        #import pdb;pdb.set_trace()


        #Go through deprels without input
        #These will be paired
        pos_dni_sets_to_pair, neg_dni_sets_to_pair = self.get_dep_wo_input_restrictions(node_id)

        #Go through deprels with input
        #These will be paired
        pos_di_sets_to_pair, neg_di_sets_to_pair = self.get_dep_w_input_restrictions(node_id)

        #Find a good starting point
        #Check through positive deprel without input and text_res
        the_first_set = ''
        the_first_set_found = False

        #print '#' * 50
        #print '# node:' + node_id
        #print '#' * 50
        #print '# ' + str(txt_sets_to_intersect)
        #print '#' * 50
        #print '# pos_dni: ' + str(pos_dni_sets_to_pair) + ', neg_dni: ' + str(neg_dni_sets_to_pair)
        #print '#' * 50
        #print '# pos_di: ' + str(pos_di_sets_to_pair) + ', neg_di: ' + str(neg_di_sets_to_pair)
        #print '#' * 50

        first_code_block = []

        #If node has text restrictions it's a good starting point
        if len(txt_sets_to_intersect) > 0:
            first_code_block = self.get_text_restrictions_intersect_code(txt_sets_to_intersect)
            the_first_set_found = True
            ####
            operation_blocks.append(retrieve_from_db_code_block(txt_sets_to_intersect[0]))

        elif len(pos_dni_sets_to_pair) > 0:
            code, needed = self.get_dep_set(pos_dni_sets_to_pair[0])
            #needed_from_the_dict |= needed
            first_code_block = code
            ####
            operation_blocks.append(retrieve_from_db_code_block(pos_dni_sets_to_pair[0]))


            pos_dni_sets_to_pair = pos_dni_sets_to_pair[1:]
            the_first_set_found = True
        else:
            #XXX:Do this!
            needed = 'deps??'
            first_code_block = ['fset=all_tokens',]
            the_first_set_found = True
            ####
            operation_blocks.append(retrieve_from_db_code_block('ALL TOKENS'))


        #print '# ' + str(first_code_block)
        #print '#' * 50
        #print
        #Works quite nicely up to this point

        for txtr in txt_sets_to_intersect[1:]:
            operation_blocks.append(intersect_code_block('self.set_' + node_id, txtr))

        #Ok, I've got the first set and all I need to get this thing done!
        pair_code_blocks = []

        #Do pairings for deprels with input
        for di in pos_di_sets_to_pair:

            #print di
            operation_blocks.append(pair_code_block(di, 'self.set_' + node_id, di[2], di[0], di[1]))

        #Do pairings for deprels without input
        for di in pos_dni_sets_to_pair:
            #(rest, set1, set2, operation, type, negated=False)
            operation_blocks.append(pair_code_block(di, 'self.set_' + node_id, None, di[0], di[1]))

        #Do pairings for ned deprels with input
        for di in neg_di_sets_to_pair:
            #(rest, set1, set2, operation, type, negated=False)
            operation_blocks.append(pair_code_block(di, 'self.set_' + node_id, di[2], di[0], di[1], negated=True))

        #Do pairings for neg deprels without input
        for di in neg_dni_sets_to_pair:
            #(rest, set1, set2, operation, type, negated=False)
            operation_blocks.append(pair_code_block(di, 'self.set_' + node_id, None, di[0], di[1], negated=True))

        #print '#' * 50
        #for op in operation_blocks:
        #    print op.to_string()
        #    if break_exec_on_empty_set:
        #        print 'if empty(set_' + node_id + '): return set_' + node_id 
        #print '#' * 50
        #print 
        pseudo_node = self.pseudo_nodes[node_id]
        return node_code_block(operation_blocks, pseudo_node ,node_id)

        #return operation_blocks

        #end_game = ['#Check assignment', 'output_' + node_id + '=fset']
        ####
        #operation_blocks.append(end_node_block(node_id))

        
        #print first_code_block
        #print pair_code_blocks
        #print end_game
        #return operation_blocks

        #import pdb; pdb.set_trace()




        #The endgame; to check wether this form is possible
        #To be done!


    def get_pair_block(self, di, negated=False):
        needed = set()
        code_block = []   

        if len(di) > 2:
            code_block, needed = self.generate_pairing('f_set',None, di[0], di[1], negated)
        else:
            code_block, needed = self.generate_pairing('f_set',di[2], di[0], di[1], negated)

        return needed, code_block


    def get_dep_set(self, dset):

        needed = set()
        code = []
        #(op, dtype)
        if dset[0] == '<':
            code.append('fset=t.d_deps[u"' + dset[1] + '"]')
            needed.add('d_deps_' + dset[1])

        if dset[0] == '>':
            code.append('fset=t.d_govs[u"' + dset[1] + '"]')
            needed.add('d_govs_' + dset[1])

        return code, needed


    def get_text_restrictions_intersect_code(self, txt_sets_to_intersect):

        code = []
        code.append('f_set=' + txt_sets_to_intersect[0])
        for txtres in txt_sets_to_intersect[1:]:
            code.append('f_set&=' + txtres)
        return code


    def get_dep_w_input_restrictions(self, node_id):

        pos_di_sets_to_pair = []
        neg_di_sets_to_pair = []

        pseudo_node = self.pseudo_nodes[node_id]
        #2. Go through the depres without input
        for dp in pseudo_node.depres_with_input:
            #print dp.depres.operator
            op = dp.depres.operator[0]
            dtype = dp.depres.operator[2:-1]
            #print op, dtype

            if not dp.depres.negated:
                #Not negated
                #Pair f_set with this
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                #print op, dtype
                pos_di_sets_to_pair.append((op, dtype, 'self.set_' + dp.input_node))

            else:
                #Negated
                #Pair and subtract the result from the f_set
                #No need to pair when negating!
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                neg_di_sets_to_pair.append((op, dtype, 'self.set_' + dp.input_node))

        return pos_di_sets_to_pair, neg_di_sets_to_pair


    def get_dep_wo_input_restrictions(self, node_id):

        pos_dni_sets_to_pair = []
        neg_dni_sets_to_pair = []

        pseudo_node = self.pseudo_nodes[node_id]
        #2. Go through the depres without input
        for dp in pseudo_node.depres_with_empty_node:
            #print dp.depres.operator
            op = dp.depres.operator[0]
            dtype = dp.depres.operator[2:-1]
            #print op, dtype

            if not dp.depres.negated:
                #Not negated
                #Pair f_set with this
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                #print op, dtype
                pos_dni_sets_to_pair.append((op, dtype))

            else:
                #Negated
                #Pair and subtract the result from the f_set
                #No need to pair when negating!
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                neg_dni_sets_to_pair.append((op, dtype))

        return pos_dni_sets_to_pair, neg_dni_sets_to_pair



    def get_text_restrictions(self, node_id):

        needed_words = set()
        what_sets_are_needed = set()
        #needed_tags = set()
        txt_sets_to_pair = []

        pseudo_node = self.pseudo_nodes[node_id]

        for txt_res in pseudo_node.txt_res:
            #print len(code_block)
            if txt_res[0] in [u'CGTAG', u'TXT', u'CGBASE'] and txt_res[1] != u'_':

                if txt_res[0] == u'TXT':
                    txt_sets_to_pair.append('token_s_' + txt_res[1])
                    if self.no_negs_above_dict[node_id]:
                        needed_words.add(txt_res[1])

                elif txt_res[0] == u'CGTAG':

                    if '+' not in txt_res[1]:

                        txt_sets_to_pair.append('tag_s_' + txt_res[1])

                        if self.no_negs_above_dict[node_id]:
                            what_sets_are_needed.add('!tags_' + txt_res[1])
                        else:
                            what_sets_are_needed.add('tags_' + txt_res[1])

                    else:
                        tags = txt_res[1].split('+')
                        for tag in tags:
                            txt_sets_to_pair.append('tag_s_' + tag)
                            if self.no_negs_above_dict[node_id]:
                                what_sets_are_needed.add('!tags_' + tag)
                            else:
                                what_sets_are_needed.add('tags_' + tag)

                elif txt_res[0] == u'CGBASE':

                    if '+' not in txt_res[1]:

                        txt_sets_to_pair.append('lemma_s_' + txt_res[1])

                        if self.no_negs_above_dict[node_id]:
                            what_sets_are_needed.add('!lemma_' + txt_res[1])
                        else:
                            what_sets_are_needed.add('lemma_' + txt_res[1])




        return what_sets_are_needed, txt_sets_to_pair, needed_words


    def generate_pairing(self, set1,set2,op,dtype=None,negated=False):

        the_block = ['#Pair(' + str((set1,set2,op,dtype,negated)), ]
        needed = set()

        if dtype:
            the_block.append('d_type = "' + dtype + '"')
        the_block.append('set_1 = ' + set1)
        if set2:
            the_block.append('set_2 = ' + set2)

        if dtype and op==u">":
            the_block.append('needed_dict=t.type_deps.get(dtype,{})')
            if not negated:
                needed.add('!deps_' + dtype)
            else:
                needed.add('deps_' + dtype)
        elif dtype and op==u"<":
            the_block.append('needed_dict=t.type_govs.get(dtype,{})')
            if not negated:
                needed.add('!govs_' + dtype)
            else:
                needed.add('govs_' + dtype)
        elif op==u">":
            the_block.append('needed_dict=t.deps')
            needed.add('deps')
        elif op==u"<":
            the_block.append('needed_dict=t.govs')
            needed.add('govs')

        the_block.append('result=set()')
        the_block.append('for i in set1:')
        if set2:
            the_block.append('\tif set2&needed_dict.get(i,set()):')
            the_block.append('\t\tresult.add(i)')
        else:
            the_block.append('\tif needed_dict.get(i,set()):')
            the_block.append('\t\tresult.add(i)')

        return the_block, needed




    def process_node(self, node):

        orig_node = node
        #Give each node an id
        #And get appropriate dicts for these nodes
        self.node_id_dict, self.node_depth_dict, self.no_negs_above_dict = self.get_depth_and_id_dicts(node)
        #Make a reverse id dict
        self.reverse_node_id_dict = {v: k for k, v in self.node_id_dict.items()}

        #print '#', self.node_id_dict
        #print '#', self.node_depth_dict

        #Sort nodes into order
        self.order_of_execution = []
        levels = self.node_depth_dict.keys()
        levels.sort()
        levels.reverse()
        for level in levels:
            self.nodes_which_break_on_empty = []
            self.nodes_which_dont_break_on_empty = []        
            for node_id in self.node_depth_dict[level]:
                if self.no_negs_above_dict[node_id]:
                    self.nodes_which_break_on_empty.append(node_id)
                else:
                    self.nodes_which_dont_break_on_empty.append(node_id)
            self.order_of_execution.extend(self.nodes_which_break_on_empty)
            self.order_of_execution.extend(self.nodes_which_dont_break_on_empty)

        #Make pseudo objects
        self.pseudo_nodes = {}
        for node_id, node in self.node_id_dict.items():
            
            #Go through restrictions of this node
            node_txt_restrictions = []
            node_depres = []

            restrictions = node.restrictions
            for rest in restrictions:
                if type(rest) != DepRes:
                    node_txt_restrictions.append(rest)
                else:
                    node_depres.append(rest)

            #Make Pseudo DepRels
            pseudo_depres_list = []
            for depres in node_depres:
                #Does this have an input node, which is not empty?
                input_node = depres.node
                if len(input_node.restrictions) > 0:
                    input_node_id = self.reverse_node_id_dict[input_node]
                else:
                    input_node_id = None
                pseudo_depres_list.append(PseudoDepres(depres, input_node_id))
            pseudo_node = PseudoNode(node, pseudo_depres_list, node_depres, node_txt_restrictions, node_id)
            self.pseudo_nodes[node_id] = pseudo_node


    def get_depth_and_id_dicts(self, node):

        node_id_dict, node_depth_dict, no_negs_above_dict = self.id_the_tree(node, '0', 0, True)

        proper_depth_dict = {}
        #print 'ndk', self.node_depth_dict.keys()
        for key in node_depth_dict.keys():
            value = node_depth_dict[key]
            #print 'vk', value, key
            if value not in proper_depth_dict.keys():
                proper_depth_dict[value] = []
            proper_depth_dict[value].append(key)

        return node_id_dict, proper_depth_dict, no_negs_above_dict

    def id_the_tree(self, node, id, depth, no_negs_above):

        no_negs_above_dict = {}
        node_id_dict = {}
        node_depth_dict = {}
        node_id_dict[id] = node
        node_depth_dict[id] = depth
        no_negs_above_dict[id] = no_negs_above
        kid_nodes = []
        negated = []
        for dr in node.restrictions:
            if type(dr) == DepRes:
                kid_nodes.append(dr.node)
                negated.append(dr.negated)

        for i, kid_node in enumerate(kid_nodes):

            if no_negs_above and not negated[i]:
                neg = True
            else:
                neg = False
            res_id_dict, res_depth_dict, res_no_negs_above_dict = self.id_the_tree(kid_node, id + '_' + str(i), depth+1, neg)
            node_id_dict.update(res_id_dict)   
            node_depth_dict.update(res_depth_dict)  
            no_negs_above_dict.update(res_no_negs_above_dict)

        return node_id_dict, node_depth_dict, no_negs_above_dict









class PseudoNode():

    def __init__(self, node, pseudo_depres, depres, txt_res, id, should_break_if_empty=False):

        self.id = id
        self.node = node
        self.pseudo_depres = pseudo_depres
        self.depres = depres
        self.txt_res = txt_res
        self.should_break_if_empty = should_break_if_empty

        self.depres_with_empty_node = []
        self.depres_with_input = []
        for pd in pseudo_depres:
            if pd.input_node == None:
                self.depres_with_empty_node.append(pd)
            else:
                self.depres_with_input.append(pd)

class PseudoDepres():

    def __init__(self,depres,input_node):

        self.input_node = input_node
        self.depres = depres
        self.expression = depres.operator
        self.text = str(self.expression)


def process_node(node):

    orig_node = node
    #Give each node an id
    #And get appropriate dicts for these nodes
    self.node_id_dict, self.node_depth_dict, self.no_negs_above_dict = get_depth_and_id_dicts(node)
    #Make a reverse id dict
    self.reverse_node_id_dict = {v: k for k, v in self.node_id_dict.items()}

    #print '#', self.node_id_dict
    #print '#', self.node_depth_dict

    #Sort nodes into order
    self.order_of_execution = []
    levels = self.node_depth_dict.keys()
    levels.sort()
    levels.reverse()
    for level in levels:
        self.nodes_which_break_on_empty = []
        self.nodes_which_dont_break_on_empty = []        
        for node_id in self.node_depth_dict[level]:
            if self.no_negs_above_dict[node_id]:
                self.nodes_which_break_on_empty.append(node_id)
            else:
                self.nodes_which_dont_break_on_empty.append(node_id)
        self.order_of_execution.extend(self.nodes_which_break_on_empty)
        self.order_of_execution.extend(self.nodes_which_dont_break_on_empty)

    #Make pseudo objects
    self.pseudo_nodes = {}
    for node_id, node in self.node_id_dict.items():
        
        #Go through restrictions of this node
        node_txt_restrictions = []
        node_depres = []

        restrictions = node.restrictions
        for rest in restrictions:
            if type(rest) != DepRes:
                node_txt_restrictions.append(rest)
            else:
                node_depres.append(rest)

        #Make Pseudo DepRels
        pseudo_depres_list = []
        for depres in node_depres:
            #Does this have an input node, which is not empty?
            input_node = depres.node
            if len(input_node.restrictions) > 0:
                input_node_id = self.reverse_node_id_dict[input_node]
            else:
                input_node_id = None
            pseudo_depres_list.append(PseudoDepres(depres, input_node_id))
        pseudo_node = PseudoNode(node, pseudo_depres_list, node_depres, node_txt_restrictions, node_id)
        self.pseudo_nodes[node_id] = pseudo_node

    print orig_node.to_unicode()
    what_sets_are_needed = set()
    what_words_are_needed = set()

    for node_id in self.order_of_execution:

        node = self.node_id_dict[node_id]
        pseudo_node = self.pseudo_nodes[node_id]
        if len(node.restrictions) < 1:
            continue

        if False:

            print
            print '#Node ', node_id
            if self.no_negs_above_dict[node_id]:
                print '#Break execution if this node returns set()'
            else:
                print '#Do Not break execution if this node returns set()'
            print 

            print '\t#Text Restrictions:'
            for txt_res in pseudo_node.txt_res:
                print '\t#\t' + str(txt_res)
            #print
            print '\t#DepRes without input:'
            for dp in pseudo_node.depres_with_empty_node:
                print '\t#\t%s,%s' % (dp.depres.operator, not dp.depres.negated)
            #print
            print '\t#DepRes with input:'
            for dp in pseudo_node.depres_with_input:
                print '\t#\t%s, node_output_%s,%s'% (dp.depres.operator, dp.input_node,not dp.depres.negated)
            print '\t#Returns: node_output_%s' % node_id

	    #    0. init and maintain a list of all restrictions
	        #unique id and possible token set

	        #Restrictions without input

	    #	1. get sets for tag or word, lemma etc restrictions
	    #	2. get sets for depres without input
	    #	    pair for every set
	    #	3. get sets for depres with input
	    #	    pair for every set
		    #Maybe first ensure connection here?
		    #Or, maybe not?
		    #More details here

	        #Restrictions with input

	    #	4. For every res with input:
	    #	       get input set and pair with orig_set, with appropriate restriction
	    #	       save the sets
		           #Details!

	    #	5. Check assignment
	    #	    save sets

        #Which_sets are needed:

    #A codeblock for each node
    #A list of the sets which it needs

    #Afterwards:
    #   -generate header, with the sets

    #   -remove conflicting sets(later)
    #   -

    what_sets_are_needed = set()
    what_words_are_needed = set()

    cb = []
    for node_id in self.order_of_execution:

        node = self.node_id_dict[node_id]
        pseudo_node = self.pseudo_nodes[node_id]
        if len(node.restrictions) < 1:
            continue
        code_block = []
        first_set_found = False

        #1. Go through the textual limits
        for txt_res in pseudo_node.txt_res:
            #print len(code_block)
            if txt_res[0] in [u'CGTAG', u'TXT'] and txt_res[1] != u'_':

                if txt_res[0] == u'TXT':
                    if len(code_block) == 0:
                        code_block.append('f_set = t.dict_tokens[u"' + txt_res[1] + '"]')

                    else:
                        code_block.append('f_set &= t.dict_tokens[u"' + txt_res[1] + '"]')
                    what_words_are_needed.add(txt_res[1])

                elif txt_res[0] == u'CGTAG':

                    if '+' not in txt_res[1]:

                        if len(code_block) == 0:
                            code_block.append('f_set = t.tags[u"' + txt_res[1] + '"]')
                        else:
                            code_block.append('f_set &= t.tags[u"' + txt_res[1] + '"]')

                        if self.no_negs_above_dict[node_id]:
                            what_sets_are_needed.add('!tags_' + txt_res[1])
                        else:
                            what_sets_are_needed.add('tags_' + txt_res[1])

                    else:
                        tags = txt_res[1].split('+')
                        for tag in tags:
                            if len(code_block) == 0:
                                code_block.append('f_set = t.tags[u"' + tag + '"]')
                            else:
                                code_block.append('f_set &= t.tags[u"' + tag + '"]')

                            if self.no_negs_above_dict[node_id]:
                                what_sets_are_needed.add('!tags_' + tag)
                            else:
                                what_sets_are_needed.add('tags_' + tag)

        #2. Go through the depres without input
        for dp in pseudo_node.depres_with_empty_node:
            #print dp.depres.operator
            op = dp.depres.operator[0]
            dtype = dp.depres.operator[2:-1]
            #print op, dtype

            if len(code_block) > 0:
                if not dp.depres.negated:
                    #Not negated
                    #Pair f_set with this
                    op = dp.depres.operator[0]
                    dtype = dp.depres.operator[2:-1]
                    if len(dtype) < 1:
                        dtype = None
                    #print op, dtype
                    pair_block, needed = self.generate_pairing('f_set',None, op, dtype, False)
                    code_block.extend(pair_block)
                    what_sets_are_needed |= needed
                    code_block.append('f_set = result')

                else:
                    #Negated
                    #Pair and subtract the result from the f_set
                    #No need to pair when negating!
                    op = dp.depres.operator[0]
                    dtype = dp.depres.operator[2:-1]
                    if len(dtype) < 1:
                        dtype = None
                    #print op, dtype
                    #pair_block, needed = generate_pairing('f_set',None, op, dtype, True)
                    #code_block.extend(pair_block)
                    #what_sets_are_needed |= needed
                    if dtype:
                        if op == u'>':
                            code_block.append('f_set -= t.d_govs[u"' + dtype + '"]')
                            what_sets_are_needed.add('d_govs_' + dtype)
                        else:
                            code_block.append('f_set -= t.d_deps[u"' + dtype + '"]')                        
                            what_sets_are_needed.add('d_deps_' + dtype)
            else:
                if not dp.depres.negated:
                    #Not negated
                    #This will not stay it is wrong!
                    #Only a placeholder!!
                    code_block.append('f_set = set(range(0, len(t.tokens)))')
                    op = dp.depres.operator[0]
                    dtype = dp.depres.operator[2:-1]
                    if len(dtype) < 1:
                        dtype = None
                    pair_block, needed = generate_pairing('f_set',None, op, dtype, True)
                    code_block.extend(pair_block)
                    what_sets_are_needed |= needed
                    code_block.append('f_set = result')

                else:
                    #Negated
                    #FFS: f_set = set(all_tokens)
                    #Very suspect, check later!
                    code_block.append('f_set = set(range(0, len(t.tokens)))')
                    op = dp.depres.operator[0]
                    dtype = dp.depres.operator[2:-1]
                    if len(dtype) < 1:
                        dtype = None
                    #print op, dtype
                    #pair_block, needed = generate_pairing('f_set',None, op, dtype, True)
                    #code_block.extend(pair_block)
                    #what_sets_are_needed |= needed
                    if dtype:
                        if op == u'>':
                            code_block.append('f_set -= t.d_govs[u"' + dtype + '"]')
                            what_sets_are_needed.add('d_govs_' + dtype)
                        else:
                            code_block.append('f_set -= t.d_deps[u"' + dtype + '"]')                        
                            what_sets_are_needed.add('d_deps_' + dtype)
                    else:
                        #Negated whatever errrr
                        #I'm not going to do this, not now
                        pass

        #Really?
        if len(code_block) < 1:
            code_block.append('f_set = set(range(0, len(t.tokens)))')

        for dp in pseudo_node.depres_with_input:

            if not dp.depres.negated:
                #Not negated
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                #print op, dtype
                pair_block, needed = generate_pairing('f_set', 'output_' + dp.input_node, op, dtype, False)
                code_block.extend(pair_block)
                what_sets_are_needed |= needed
                code_block.append('f_set = result')

            else:
                #Negated
                #Not negated
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                #print op, dtype
                pair_block, needed = generate_pairing('f_set', 'output_' + dp.input_node, op, dtype, False)
                code_block.extend(pair_block)
                what_sets_are_needed |= needed
                code_block.append('f_set -= result')           

        code_block.append('##Check that everything works(?,?,?)')
        code_block.append('output_' + node_id + ' = f_set')

        print '\n'.join(code_block)
        cb.extend(code_block)
        #import pdb;pdb.set_trace()

    print 'return output_0'
    print what_sets_are_needed
    print what_words_are_needed

    generate_the_search_file(cb, what_sets_are_needed, what_words_are_needed)


def generate_the_search_file(code_blocks, what_sets_are_needed, what_words_are_needed):

    print 'class SearchC(Query):'
    print '\tdef __init__(self):'
    print '\t\tQuery.__init__(self)'
    print '\t\tself.words=' + str(what_words_are_needed)
    print '\t\tself.query_fields=' + str(list(what_sets_are_needed))
    print
    print '\tdef match(self,t):'
    for line in code_blocks:
        print '\t\t' + line
    print '\t\treturn output_0'


    def __init__(self):
        Query.__init__(self)
    



        #3. Go through the depres with input
        #4. Nothing found, How would this be possible?
        


def generate_pairing(set1,set2,op,dtype=None,negated=False):

    the_block = ['#Pair(' + str((set1,set2,op,dtype,negated)), ]
    needed = set()

    if dtype:
        the_block.append('d_type = "' + dtype + '"')
    the_block.append('set_1 = ' + set1)
    if set2:
        the_block.append('set_2 = ' + set2)

    if dtype and op==u">":
        the_block.append('needed_dict=t.type_deps.get(dtype,{})')
        if not negated:
            needed.add('!deps_' + dtype)
        else:
            needed.add('deps_' + dtype)
    elif dtype and op==u"<":
        the_block.append('needed_dict=t.type_govs.get(dtype,{})')
        if not negated:
            needed.add('!govs_' + dtype)
        else:
            needed.add('govs_' + dtype)
    elif op==u">":
        the_block.append('needed_dict=t.deps')
        needed.add('deps')
    elif op==u"<":
        the_block.append('needed_dict=t.govs')
        needed.add('govs')

    the_block.append('result=set()')
    the_block.append('for i in set1:')
    if set2:
        the_block.append('\tif set2&needed_dict.get(i,set()):')
        the_block.append('\t\tresult.add(i)')
    else:
        the_block.append('\tif needed_dict.get(i,set()):')
        the_block.append('\t\tresult.add(i)')

    return the_block, needed


    
def get_depth_and_id_dicts(node):

    self.node_id_dict, self.node_depth_dict, self.no_negs_above_dict = id_the_tree(node, '0', 0, True)

    proper_depth_dict = {}
    #print 'ndk', self.node_depth_dict.keys()
    for key in self.node_depth_dict.keys():
        value = self.node_depth_dict[key]
        #print 'vk', value, key
        if value not in proper_depth_dict.keys():
            proper_depth_dict[value] = []
        proper_depth_dict[value].append(key)

    return self.node_id_dict, proper_depth_dict, self.no_negs_above_dict

def id_the_tree(node, id, depth, no_negs_above):

    self.no_negs_above_dict = {}
    self.node_id_dict = {}
    self.node_depth_dict = {}
    self.node_id_dict[id] = node
    self.node_depth_dict[id] = depth
    self.no_negs_above_dict[id] = no_negs_above
    kid_nodes = []
    negated = []
    for dr in node.restrictions:
        if type(dr) == DepRes:
            kid_nodes.append(dr.node)
            negated.append(dr.negated)

    for i, kid_node in enumerate(kid_nodes):

        if no_negs_above and not negated[i]:
            neg = True
        else:
            neg = False
        res_id_dict, res_depth_dict, res_self.no_negs_above_dict = id_the_tree(kid_node, id + '_' + str(i), depth+1, neg)
        self.node_id_dict.update(res_id_dict)   
        self.node_depth_dict.update(res_depth_dict)  
        self.no_negs_above_dict.update(res_self.no_negs_above_dict)

    return self.node_id_dict, self.node_depth_dict, self.no_negs_above_dict

def main():

    '''
    Exploring the node tree, trying to figure very naive order of execution.
    With a naive attempt at code generation
    '''

    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    parser.add_argument('output_file')
    args = parser.parse_args()
    
    e_parser=yacc.yacc()
    for expression in args.expression:
        nodes = e_parser.parse(expression)
        print nodes.to_unicode()

    cdd = code(nodes)
    lines = cdd.get_search_code()
    filename = str(args.output_file)
    write_cython_code(lines, filename + '.pyx')

def write_cython_code(lines, output_file):

    out = open(output_file, 'wt')

    magic_lines = '''# distutils: language = c++
# distutils: include_dirs = setlib
# distutils: extra_objects = setlib/pytset.so
# distutils: sources = query_functions.cpp
include "search_common.pxi"\n'''

    out.write(magic_lines)

    for line in lines:
        out.write(line + '\n')

    out.close()









main()
