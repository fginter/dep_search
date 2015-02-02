#from query import Query
#import lex as lex
#import yacc as yacc
#import re
from expr import *
import sys


class SetManager():

    def __init__(self, match_code, no_negs_above_dict):

        self.match_code = match_code
        self.no_negs_above_dict = no_negs_above_dict
        self.process_all()

    def process_all(self):


        #Get all of the used sets and arrays
        #And whether theyre complsory or not

        self.all_arrays = []
        self.all_sets = []

        compulsory_sets = []
        voluntary_sets = []
        compulsory_arrays = []
        voluntary_arrays = []
        get_from_db_blocks = {}

        extra_list = []


        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            pass#print node_id
            for i, block in enumerate(node.operation_blocks):
                #Get used sets and arrays

                used_arrays, used_sets, non_compulsory_sets, non_compulsory_arrays, extras = block.get_needed()
                extra_list.extend(extras)

                self.all_sets.extend(used_sets)
                self.all_arrays.extend(used_arrays)

                self.all_sets.extend(non_compulsory_sets)
                self.all_arrays.extend(non_compulsory_arrays)

                if block.negated or not compulsory_node:
                    voluntary_sets.extend(used_sets)
                    voluntary_arrays.extend(used_arrays)

                    voluntary_sets.extend(non_compulsory_sets)
                    voluntary_arrays.extend(non_compulsory_arrays)

                else:
                    compulsory_sets.extend(used_sets)
                    compulsory_arrays.extend(used_arrays)

                    voluntary_sets.extend(non_compulsory_sets)
                    voluntary_arrays.extend(non_compulsory_arrays)

                if isinstance(block, retrieve_from_db_code_block):
                    get_from_db_blocks[node_id] = block

                if isinstance(block, text_restriction_code_block):
                    if block.init:
                        get_from_db_blocks[node_id] = block


        self.init_dict = {}
        for key in get_from_db_blocks.keys():
            block = get_from_db_blocks[key]
            self.init_dict['self.set_' + key] = block.get_init_set()

        #If the said key is multiple times in the
        #db list, it is cloned
        #fill ones are of course fill
        #db

        self.db_set_node_dict = {}
        self.fill_set_node_list = []
        self.clone_set_node_list = []
        self.rev_db_set_node_dict = {}
        self.load_list_dict = {}
        #The practical step here is to get those sets which are only used to ground sets
        for key in self.init_dict.keys():

            #Fill one
            if self.init_dict[key] == 'ALL TOKENS':
                self.fill_set_node_list.append(key)
            #Clone
            elif self.all_sets.count(self.init_dict[key]) > 1:
                self.clone_set_node_list.append(key)
            else:
                self.db_set_node_dict[key] = self.init_dict[key]
                self.rev_db_set_node_dict[self.init_dict[key]] = key
                if self.init_dict[key] in compulsory_sets:
                    self.load_list_dict[key] = '!' + self.init_dict[key]
                else:
                    self.load_list_dict[key] = self.init_dict[key]

        #Ok, the sets which are used for init are now found!
        #What next
        #1) So, I guess creating the load lists
        #Create a list of sets which are not taken
        free_set_list = []
        for d_set in list(set(self.all_sets)):
            if d_set not in self.db_set_node_dict.values():
                free_set_list.append(d_set)

        self.help_set_dict = {}
        #Make the dict
        for i, d_set in enumerate(free_set_list):
            self.help_set_dict['self.set_h_' + str(i)] = d_set
            if d_set in compulsory_sets:
                self.load_list_dict['self.set_h' + str(i)] = '!' + d_set
            else:
                self.load_list_dict['self.set_h' + str(i)] = d_set


        for i, d_arr in enumerate(self.all_arrays):
            self.help_set_dict['self.array_h_' + str(i)] = d_arr
            if d_arr in compulsory_arrays:
                self.load_list_dict['self.array_h' + str(i)] = '!' + d_arr
            else:
                self.load_list_dict['self.array_h' + str(i)] = d_arr

        #2) After that the clone list
 
        #self.clone_dict = {}
        #for cl_s in self.clone_set_node_list:

            #node_id is the key
            #import pdb;pdb.set_trace()
            #d_set = self.db_set_node_dict[key]
            #self.clone_dict[cl_s] = self.help_set_dict[d_set]

        #3) Extra set dict
        # -- If all_tokens is requested grant it!
        # -- for temp set create one
        self.temp_set_list = []
        self.temp_array_list = []

        for e in extra_list:
        #for e in extras:
            if e == 'ALL TOKENS':
                self.init_dict['self.set_all_tokens'] = 'ALL TOKENS'
            if e == 'temp_set':
                self.temp_set_list.append('self.temp_set' + str(len(self.temp_set_list)))
            if e == 'temp_array':
                self.temp_array_list.append('self.temp_array' + str(len(self.temp_array_list)))

        self.usable_temp_array_list = self.temp_array_list[:]

        #A nice list for cinit function
        #import pdb;pdb.set_trace()

        self.inv_list_dict = {}
        for key in self.load_list_dict.keys():
            v = self.load_list_dict[key]
            if v.startswith('!'):
                v = v[1:]
            self.inv_list_dict[v] = key


    def get_cinit_function(self):

        #This is the most complex one!
        lines = []
        lines.append('    def __cinit__(self):')
        #set_types
        #sets
        lines.append('        self.sets=<void**>malloc(' + str(len(self.load_list_dict)) + '*sizeof(void*))')
        lines.append('        self.set_types=<int*>malloc(' + str(len(self.load_list_dict)) + '*sizeof(int))')

        query_list = []

        for key in self.init_dict:
            if key not in self.load_list_dict.keys():
                lines.append(' '*8 + key + '= new TSet(2048)')

        #The extras as well
        for ts in self.temp_set_list:
            if key not in self.load_list_dict.keys():
                lines.append(' '*8 + ts + '= new TSet(2048)')

        for ts in self.temp_array_list:
            if key not in self.load_list_dict.keys():
                lines.append(' '*8 + ts + '= new TSetArray(2048)')

        for i, key in enumerate(self.load_list_dict.keys()):
            if 'set' in key:
                lines.append(' '*8 + 'self.set_types[' + str(i) + ']=1')
                lines.append(' '*8 + key + '= new TSet(2048)')
                lines.append(' '*8 + 'self.sets[' + str(i) + ']=' + key)
                query_list.append(u'' + self.load_list_dict[key])
            elif 'array' in key:
                lines.append(' '*8 + 'self.set_types[' + str(i) + ']=2')
                lines.append(' '*8 + key + '= new TSetArray(2048)')
                lines.append(' '*8 + 'self.sets[' + str(i) + ']=' + key)
                query_list.append(u'' + self.load_list_dict[key])

        lines.append(' '*8 + 'self.query_fields=' + str(query_list))
        return lines


    def get_init_function(self):
        lines = []
        lines.append(' '*4 + 'cdef void initialize(self):')
        
        #Select something from the db


        #Reverse the list
        inv_list_dict = {}
        for key in self.load_list_dict.keys():
            v = self.load_list_dict[key]
            if v.startswith('!'):
                v = v[1:]
            inv_list_dict[v] = key


        stuff = inv_list_dict[self.all_sets[0]]

        for key in self.init_dict:
            if self.init_dict[key] == 'ALL TOKENS':
                lines.append(' '*8 + key + '.set_length(' + stuff + '.tree_length)')
                lines.append(' '*8 + key + '.fill_ones()')
            else:
                if key not in self.load_list_dict.keys():
                    #Get the name of the set and clone
                    lines.append(' '*8 + key + '.copy(' + inv_list_dict[self.init_dict[key]] + ')')

        #The extras as well
        for ts in self.temp_set_list:
            lines.append(' '*8 + ts + '.set_length(' + stuff + '.tree_length)')
                #lines.append(' '*4 + key + '.fill_ones()')            

        #stuff = inv_list_dict[self.all_arrays[0]]

        for ts in self.temp_array_list:
            lines.append(' '*8 + ts + '.set_length(' + stuff + '.tree_length)')
                #lines.append(' '*4 + key + '.fill_ones()')      
        #Reverse the load_list_dict
        if len(lines) < 2:
            lines.append(' '*8 + 'pass')  
        return lines

    def get_temp_set(self):
        pass

    def get_temp_array(self):
        to_return = self.usable_temp_array_list[0]
        self.usable_temp_array_list.remove(self.usable_temp_array_list[0])
        return to_return

    def get_class_function(self):
        lines = []
        #Init really everything!
        lines.append('cdef class  GeneratedSearch(Search):')
        #STRIP 'self.' away!

        for key in self.init_dict:
            if self.init_dict[key] == 'ALL TOKENS':
                lines.append(' ' * 4 + 'cdef TSet *' + key[5:])
        #Loaded
        for key in self.load_list_dict:
            if 'array' in key:
                lines.append(' ' * 4 + 'cdef TSetArray *' + key[5:])
            else:
                lines.append(' ' * 4 + 'cdef TSet *' + key[5:])
        #Extra and temp
        for key in self.temp_set_list:
            lines.append(' ' * 4 + 'cdef TSet *' + key[5:])
        
        for key in self.temp_array_list:
            lines.append(' ' * 4 + 'cdef TSetArray *' + key[5:])
        lines.append(' ' * 4 + 'cdef public object query_fields')

        return lines
        #Then I should have all I need!
        #Ok, we've got the stuff that is used by the code
        #Figure out which set_XXX is which
        #Those which are not used as only node init deserve their own set
        #Those used as only node init need only node_set name
        #Those which are needed as both are assigned as clone thing
        #Fill ones
        #The end

class text_restriction_code_block():

    def __init__(self, pseudo_node, node_id, init=True):

        self.pseudo_node = pseudo_node
        self.node_id = node_id
        self.init = init
        self.process()
        self.negated = False

    def get_init_set(self):
        return self.init_set

    def get_code(self, set_manager):

        the_code = []
        #Set is initialized, just stack the updates
        
        for t_i in self.to_intersect:
            if t_i[1]=='+':
                the_set = t_i[0]
                the_code.append(' ' * 8 + 'self.set_' + str(self.node_id) + '.intersection_update(' + set_manager.inv_list_dict[t_i[0]] + ')')

            if t_i[1]=='!':
                the_set = t_i[0]
                the_code.append(' ' * 8 + 'self.set_' + str(self.node_id) + '.minus_update(' + set_manager.inv_list_dict[t_i[0]] + ')')
            if t_i[1]=='|':
                the_set = t_i[0]
                the_code.append(' ' * 8 + 'self.set_' + str(self.node_id) + '.union_update(' + set_manager.inv_list_dict[t_i[0]] + ')')

        return the_code


    def process(self):

        the_tags = []
        to_intersect = []

        for txt_res in self.pseudo_node.txt_res:
            if txt_res[0] in [u'CGTAG', u'TXT', u'CGBASE'] and txt_res[1] != u'_':
                if txt_res[0] == u'CGTAG':
                    tags = self.parse_tags(txt_res[1])
                    #txt_res[1].replace('!','+').replace()
                    for tag in tags:
                        if tag.startswith('!'):
                            to_intersect.append((u'tag_s_' + tag[1:], '!'))
                        elif tag.startswith('+'):
                            to_intersect.append((u'tag_s_' + tag[1:], '+'))
                        elif tag.startswith('|'):
                            to_intersect.append((u'tag_s_' + tag[1:], '|'))
                        else:
                            to_intersect.append((u'tag_s_' + tag, '+'))

                if txt_res[0] == u'TXT':
                    tags = self.parse_tags(txt_res[1])
                    for tag in tags:
                        if tag.startswith('!'):
                            to_intersect.append((u'token_s_' + tag[1:], '!'))
                        elif tag.startswith('+'):
                            to_intersect.append((u'token_s_' + tag[1:], '+'))
                        elif tag.startswith('|'):
                            to_intersect.append((u'token_s_' + tag[1:], '|'))
                        else:
                            to_intersect.append((u'token_s_' + tag, '+'))

                if txt_res[0] == u'CGBASE':
                    tags = self.parse_tags(txt_res[1])
                    for tag in tags:
                        if tag.startswith('!'):
                            to_intersect.append((u'lemma_s_' + tag[1:], '!'))
                        elif tag.startswith('+'):
                            to_intersect.append((u'lemma_s_' + tag[1:], '+'))
                        elif tag.startswith('|'):
                            to_intersect.append((u'lemma_s_' + tag[1:], '|'))
                        else:
                            to_intersect.append((u'lemma_s_' + tag, '+'))
            else:
                pass
                raise Exception('Wrong Tag!')        




        init_set = ''
        
        if self.init:

            #Find one which is not negated
            for t_i in to_intersect:
                if t_i[1] in ['|', '+']:
                    init_set = t_i[0]
                    to_intersect.remove(t_i)
                    break

            if init_set == '':
                init_set = 'ALL TOKENS'

        self.to_intersect = to_intersect
        self.init_set = init_set

    def parse_tags(self, input):

        if '+' not in input and '|' not in input and '!' not in input:
            return  [input]

        ###
        ###
        tags = []
        curr_tag = ''
        for char in input:
            if char in ['+', '!', '|']:
                #New tag
                if curr_tag != '':
                    tags.append(curr_tag)
                curr_tag = ''
            curr_tag += char

        tags.append(curr_tag)

        return tags

    def get_needed(self):

        needed_c_sets = []
        needed_v_sets = []

        for txt_res in self.pseudo_node.txt_res:
            if txt_res[0] in [u'CGTAG', u'TXT', u'CGBASE'] and txt_res[1] != u'_':
                if txt_res[0] == u'CGTAG':
                    tags = self.parse_tags(txt_res[1])
                    #txt_res[1].replace('!','+').replace()
                    for tag in tags:

                        if '|' not in txt_res[1]:

                            if tag.startswith('!'):
                                needed_v_sets.append(u'tag_s_' + tag[1:])
                            elif tag.startswith('+'):
                                needed_c_sets.append(u'tag_s_' + tag[1:])
                            elif tag.startswith('|'):
                                needed_c_sets.append(u'tag_s_' + tag[1:])
                            else:
                                needed_c_sets.append(u'tag_s_' + tag)

                        else:

                            if tag.startswith('!'):
                                needed_v_sets.append(u'tag_s_' + tag[1:])
                            elif tag.startswith('+'):
                                needed_v_sets.append(u'tag_s_' + tag[1:])
                            elif tag.startswith('|'):
                                needed_v_sets.append(u'tag_s_' + tag[1:])
                            else:
                                needed_v_sets.append(u'tag_s_' + tag)

                if txt_res[0] == u'TXT':
                    tags = self.parse_tags(txt_res[1])

                    for tag in tags:

                        if '|' not in txt_res[1]:

                            if tag.startswith('!'):
                                needed_v_sets.append(u'token_s_' + tag[1:])
                            elif tag.startswith('+'):
                                needed_c_sets.append(u'token_s_' + tag[1:])
                            elif tag.startswith('|'):
                                needed_c_sets.append(u'token_s_' + tag[1:])
                            else:
                                needed_c_sets.append(u'token_s_' + tag)
                        else:

                            if tag.startswith('!'):
                                needed_v_sets.append(u'token_s_' + tag[1:])
                            elif tag.startswith('+'):
                                needed_v_sets.append(u'token_s_' + tag[1:])
                            elif tag.startswith('|'):
                                needed_v_sets.append(u'token_s_' + tag[1:])
                            else:
                                needed_v_sets.append(u'token_s_' + tag)


                if txt_res[0] == u'CGBASE':
                    tags = self.parse_tags(txt_res[1])
                    for tag in tags:

                        if '|' not in txt_res[1]:

                            if tag.startswith('!'):
                                needed_v_sets.append(u'lemma_s_' + tag[1:])
                            elif tag.startswith('+'):
                                needed_c_sets.append(u'lemma_s_' + tag[1:])
                            elif tag.startswith('|'):
                                needed_c_sets.append(u'lemma_s_' + tag[1:])
                            else:
                                needed_c_sets.append(u'lemma_s_' + tag)
                        else:
                            if tag.startswith('!'):
                                needed_v_sets.append(u'lemma_s_' + tag[1:])
                            elif tag.startswith('+'):
                                needed_v_sets.append(u'lemma_s_' + tag[1:])
                            elif tag.startswith('|'):
                                needed_v_sets.append(u'lemma_s_' + tag[1:])
                            else:
                                needed_v_sets.append(u'lemma_s_' + tag)


            else:
                pass
                raise Exception('Wrong Tag!', '')
                #Raise Error!
                #needed_sets.append('impossible')

        #Return used_arrays, used_sets, non_compusory_sets, non_compulsory_arrays

        return [], needed_c_sets, needed_v_sets, [], []


class node_code_block():

    def __init__(self, blocks, pseudo_node, node_id):

        self.node_id = node_id
        self.pseudo_node = pseudo_node
        self.operation_blocks = blocks
        self.end_block = []

class intersect_code_block():

    def __init__(self, set1, set2):

        self.negated = False
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


    def get_code(self, set_manager):

        match_function = []
        temp_set = 'ebin'
        optypes = []
        if self.optype is not None and '|' in self.optype:
            optypes = self.optype.split('|')
            temp_set = set_manager.get_temp_array()
            op = ''
            if self.operation == '<':
                op = 'dep'
            else:
                op = 'gov'

            match_function.append(' '*8 + temp_set + '.copy(' + set_manager.inv_list_dict[op + '_a_' + optypes[0]] + ')')
            for ot in optypes[1:]:
                match_function.append(' '*8 + temp_set + '.union_update(' + set_manager.inv_list_dict[op + '_a_' + ot] + ')')
        else:
            optypes = [self.optype]

        #Get a temp set
        if self.set2 is None:
            self.set2 = 'self.set_all_tokens'

        if self.optype is None:
            pass
            #pairing(self.set0,self.set2,self.seta1,False)
            #import pdb; pdb.set_trace()
            pass#print 'block', block

            #if self.set2 is None:
            if self.operation == '<':
                match_function.append( ' '*8 + 'pairing(' + ','.join([str(self.set1), str(self.set2), set_manager.inv_list_dict['dep_a_anyrel'], str(self.negated)]) + ')')
                
            else:
                match_function.append(' '*8 + 'pairing(' + ','.join([str(self.set1), str(self.set2), set_manager.inv_list_dict['gov_a_anyrel'], str(self.negated)]) + ')')
        else:
            if '|' in self.optype:

                if self.operation == '<':
                    match_function.append(' '*8 + 'pairing(' + ','.join([str(self.set1), str(self.set2), temp_set, str(self.negated)]) + ')')
                else:
                    match_function.append(' '*8 + 'pairing(' + ','.join([str(self.set1), str(self.set2), temp_set, str(self.negated)]) + ')')

            else:

                if self.operation == '<':
                    match_function.append(' '*8 + 'pairing(' + ','.join([str(self.set1), str(self.set2), set_manager.inv_list_dict['dep_a_'  + str(self.optype)], str(self.negated)]) + ')')
                else:
                    match_function.append(' '*8 + 'pairing(' + ','.join([str(self.set1), str(self.set2), set_manager.inv_list_dict['gov_a_' + str(self.optype)], str(self.negated)]) + ')')

        return match_function



    def get_needed(self):

        vol_sets = []
        comp_sets = []

        vol_arrays = []
        comp_arrays = []

        self.extras = []

        #Get the needed sets

        if self.set2 is None:
            self.extras.append('ALL TOKENS')

        optypes = []
        if self.optype is not None and '|' in self.optype:
            optypes = self.optype.split('|')
        else:
            optypes = [self.optype]
        
        if self.optype is None:

            if self.operation == '<':

                if self.negated:

                    if self.set2 is not None and 'set_' not in self.set2:
                        vol_sets.append(self.set2)
                    vol_arrays.append('dep_a_anyrel')

                else:

                    if self.set2 is not None and 'set_' not in self.set2:
                        comp_sets.append(self.set2)
                    comp_arrays.append('dep_a_anyrel')

            else:

                if self.negated:

                    if self.set2 is not None and 'set_' not in self.set2:
                        vol_sets.append(self.set2)
                    vol_arrays.append('gov_a_anyrel')

                else:

                    if self.set2 is not None and 'set_' not in self.set2:
                        comp_sets.append(self.set2)
                    comp_arrays.append('gov_a_anyrel')
        else:

            if self.operation == '<':

                if self.negated:

                    if self.set2 is not None and 'set_' not in self.set2:
                        vol_sets.append(self.set2)
                    for ot in optypes:
                        vol_arrays.append('dep_a_' + ot)

                else:

                    if self.set2 is not None and 'set_' not in self.set2:
                        comp_sets.append(self.set2)
                    for ot in optypes:
                        comp_arrays.append('dep_a_' + ot)

            else:

                if self.negated:

                    if self.set2 is not None and 'set_' not in self.set2:
                        vol_sets.append(self.set2)
                    for ot in optypes:
                        vol_arrays.append('gov_a_' + ot)

                else:

                    if self.set2 is not None and 'set_' not in self.set2:
                        comp_sets.append(self.set2)
                    for ot in optypes:
                        comp_arrays.append('gov_a_' + ot)

        if len(optypes) > 1:
            self.extras.append('temp_array')

        if self.optype is not None and '|' not in self.optype:
            return comp_arrays, comp_sets, vol_sets, vol_arrays, self.extras
        else:
            return [], [], comp_sets + vol_sets, comp_arrays + vol_arrays, self.extras            

        #Return used_arrays, used_sets, non_compusory_sets, non_compulsory_arrays


    def to_string(self):
        return 'Pair' + str((self.set1, self.set2, self.operation, self.optype, self.negated))


class retrieve_from_db_code_block():

    def __init__(self, needed):
        self.what_to_retrieve = needed
        self.negated = False

    def get_code(self, set_manager):
        return []     

    def get_needed(self):
        if self.get_init_set() != 'ALL TOKENS':
            return [], [self.get_init_set()], [], [], []
        else:
            return [], [], [], [], []

    def get_init_set(self):
        if self.what_to_retrieve != 'ALL TOKENS':
            if self.what_to_retrieve[0] == '<':
                if self.what_to_retrieve[1] is None:
                    return 'dep_s_anyrel'
                return 'dep_s_' + self.what_to_retrieve[1]
            elif self.what_to_retrieve[0] == '>':
                if self.what_to_retrieve[1] is None:
                    return 'gov_s_anyrel'
                return 'gov_s_' + self.what_to_retrieve[1]

        else:
                return 'ALL TOKENS'
        #Return used_arrays, used_sets, non_compusory_sets, non_compulsory_arrays

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

        pass#print 'Done!'


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



    def print_pseudo_code(self):
        pass#print what is needed from the db
        pass#print 'What is needed from the db:'
        pass#print '  compulsory text/tags:'
        for rest in self.text_needs_comp:
            pass#print ' '*4 + str(rest)
        pass#print '  non-compulsory text/tags:'
        for rest in self.text_needs_vol:
            pass#print ' '*4 + str(rest)
        pass#print '  compulsory deplists:'
        for rest in self.pair_needs_comp:
            pass#print ' '*4 + str(rest)
        pass#print '  non-compulsory deplists:'
        for rest in self.pair_needs_vol:
            pass#print ' '*4 + str(rest)

        print
        pass#print 'Match Function:'

        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            #Humm, It could've been more simple
            pass#print '  #Node:' + node_id
            for i, block in enumerate(node.operation_blocks):
                pass#print ' '*2 + 'set_' + node_id + ' = ' + block.to_string()
                if compulsory_node and i not in [0, len(node.operation_blocks)]:
                    pass#print ' '*2 + 'if self.set_' + node_id + '.is_empty(): return self.set_' + node_id
        pass#print ' '*2 + 'return set_' + node_id


    def get_search_code(self):

        #Figure out the sets and arrays needed
        set_manager = SetManager(self.match_code, self.no_negs_above_dict)
        the_code = []

        the_code.extend(set_manager.get_class_function())
        the_code.extend(set_manager.get_cinit_function())
        the_code.extend(set_manager.get_init_function())


        the_code.append('    cdef TSet* exec_search(self):')
        for node in self.match_code:
            node_id = node.node_id
            compulsory_node = self.no_negs_above_dict[node_id]
            for i, block in enumerate(node.operation_blocks):

                #For this block get needed sets and arrays
                #Figure out whether it is the set starting point set or just some other
                #Name appropriately and push to the dict
                the_code.extend(block.get_code(set_manager))
                if compulsory_node and i not in [0,1, len(node.operation_blocks)-1]:
                    the_code.append(' '*8 + 'if self.set_' + node_id + '.is_empty(): return self.set_' + node_id)


        the_code.extend([' '*8 + 'return self.set_' + node_id])

        return the_code
        

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


    def get_node_code(self, node_id):

        pseudo_node = self.pseudo_nodes[node_id]
        #So Start collecting the node code blocks into this list
        operation_blocks = []

        #Here we are!
        break_exec_on_empty_set = self.no_negs_above_dict[node_id]

        #Grab the sets which need to be paired with each other
        sets_to_pair = []
        negated_sets_to_pair = []
        needed_from_the_dict = set()
        #Go through text restrictions
        txt_what_sets_are_needed, txt_sets_to_intersect, needed_words = self.get_text_restrictions(node_id)
        #txt_sets = self.get_text_restrictions_2(node_id)
        #Go through deprels without input
        #These will be paired
        pos_dni_sets_to_pair, neg_dni_sets_to_pair = self.get_dep_wo_input_restrictions(node_id)
        #Go through deprels with input
        #These will be paired
        pos_di_sets_to_pair, neg_di_sets_to_pair = self.get_dep_w_input_restrictions(node_id)
        #Find a good starting point
        #Check through positive deprel without input and text_res
        first_code_block = []
        #If node has text restrictions it's a good starting point
        if len(txt_sets_to_intersect) > 0:
            operation_blocks.append(text_restriction_code_block(pseudo_node, node_id, init=True))

        elif len(pos_dni_sets_to_pair) > 0:
            operation_blocks.append(retrieve_from_db_code_block(pos_dni_sets_to_pair[0]))
            pos_dni_sets_to_pair = pos_dni_sets_to_pair[1:]
            the_first_set_found = True
        else:
            operation_blocks.append(retrieve_from_db_code_block('ALL TOKENS'))

        #Ok, I've got the first set and all I need to get this thing done!
        pair_code_blocks = []

        #Do pairings for deprels with input
        for di in pos_di_sets_to_pair:
            pass#print di
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


        return node_code_block(operation_blocks, pseudo_node ,node_id)


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
            pass#print dp.depres.operator
            op = dp.depres.operator[0]
            dtype = dp.depres.operator[2:-1]
            pass#print op, dtype

            if not dp.depres.negated:
                #Not negated
                #Pair f_set with this
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                pass#print op, dtype
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
            pass#print dp.depres.operator
            op = dp.depres.operator[0]
            dtype = dp.depres.operator[2:-1]
            pass#print op, dtype

            if not dp.depres.negated:
                #Not negated
                #Pair f_set with this
                op = dp.depres.operator[0]
                dtype = dp.depres.operator[2:-1]
                if len(dtype) < 1:
                    dtype = None
                pass#print op, dtype
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
            pass#print len(code_block)
            if txt_res[0] in [u'CGTAG', u'TXT', u'CGBASE'] and txt_res[1] != u'_':

                if txt_res[0] == u'TXT':
                    txt_sets_to_pair.append('token_s_' + txt_res[1])
                    if self.no_negs_above_dict[node_id]:
                        needed_words.add(txt_res[1])

                elif txt_res[0] == u'CGTAG':


                    txt_sets_to_pair.append('tag_s_' + txt_res[1])

                    if self.no_negs_above_dict[node_id]:
                        what_sets_are_needed.add('!tags_' + txt_res[1])
                    else:
                        what_sets_are_needed.add('tags_' + txt_res[1])

                elif txt_res[0] == u'CGBASE':

                    txt_sets_to_pair.append('lemma_s_' + txt_res[1])

                    if self.no_negs_above_dict[node_id]:
                        what_sets_are_needed.add('!lemma_' + txt_res[1])
                    else:
                        what_sets_are_needed.add('lemma_' + txt_res[1])
            else:
                raise Exception('Wrong Tag:' + txt_res[0])
        return what_sets_are_needed, txt_sets_to_pair, needed_words


    def process_node(self, node):

        orig_node = node
        #Give each node an id
        #And get appropriate dicts for these nodes
        self.node_id_dict, self.node_depth_dict, self.no_negs_above_dict = self.get_depth_and_id_dicts(node)
        #Make a reverse id dict
        self.reverse_node_id_dict = {v: k for k, v in self.node_id_dict.items()}

        pass#print '#', self.node_id_dict
        pass#print '#', self.node_depth_dict

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
        pass#print 'ndk', self.node_depth_dict.keys()
        for key in node_depth_dict.keys():
            value = node_depth_dict[key]
            pass#print 'vk', value, key
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

    pass#print '#', self.node_id_dict
    pass#print '#', self.node_depth_dict

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

    pass#print orig_node.to_unicode()
    what_sets_are_needed = set()
    what_words_are_needed = set()

    for node_id in self.order_of_execution:

        node = self.node_id_dict[node_id]
        pseudo_node = self.pseudo_nodes[node_id]
        if len(node.restrictions) < 1:
            continue

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
            pass#print len(code_block)
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
            pass#print dp.depres.operator
            op = dp.depres.operator[0]
            dtype = dp.depres.operator[2:-1]
            pass#print op, dtype

            if len(code_block) > 0:
                if not dp.depres.negated:
                    #Not negated
                    #Pair f_set with this
                    op = dp.depres.operator[0]
                    dtype = dp.depres.operator[2:-1]
                    if len(dtype) < 1:
                        dtype = None
                    pass#print op, dtype
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
                    pass#print op, dtype
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
                    pass#print op, dtype
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
                pass#print op, dtype
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
                pass#print op, dtype
                pair_block, needed = generate_pairing('f_set', 'output_' + dp.input_node, op, dtype, False)
                code_block.extend(pair_block)
                what_sets_are_needed |= needed
                code_block.append('f_set -= result')           

        code_block.append('##Check that everything works(?,?,?)')
        code_block.append('output_' + node_id + ' = f_set')

        pass#print '\n'.join(code_block)
        cb.extend(code_block)
        #import pdb;pdb.set_trace()

    pass#print 'return output_0'
    pass#print what_sets_are_needed
    pass#print what_words_are_needed

    generate_the_search_file(cb, what_sets_are_needed, what_words_are_needed)

def get_depth_and_id_dicts(node):

    self.node_id_dict, self.node_depth_dict, self.no_negs_above_dict = id_the_tree(node, '0', 0, True)

    proper_depth_dict = {}
    pass#print 'ndk', self.node_depth_dict.keys()
    for key in self.node_depth_dict.keys():
        value = self.node_depth_dict[key]
        pass#print 'vk', value, key
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
        pass#print nodes.to_unicode()

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


def generate_and_write_search_code_from_expression(expression, output_file):
    e_parser=yacc.yacc()
    nodes = e_parser.parse(expression)
    cdd = code(nodes)
    lines = cdd.get_search_code()
    write_cython_code(lines, output_file + '.pyx')

def generate_and_write_search_code_from_node_tree(node, output_file):

    cd = code(node)
    lines = cd.get_search_code()
    write_cython_code(lines, output_file)



if __name__ == "__main__":
    main()
