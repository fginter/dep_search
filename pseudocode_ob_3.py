#import lex as lex
#import yacc as yacc
#import re
from redone_expr import *
import sys
import codecs
import json
#Taskilist:
#1. The order of the nodes(this time there is a possibility of three input nodes for a node!)
#And other stuffs

#2. SetManager
#3. CodeGenerator

class NodeInterpreter():

    def __init__(self, node, tag_list=[], val_dict={}):

        self.tag_list = tag_list
        self.val_dict = val_dict

        if len(self.tag_list) < 1:
            self.use_tag_list = False
        else:
            self.use_tag_list = True

        self.node = node
        self.array_count = 0
        self.set_count = 0

    def do_you_need_all_tokens(self):
        #XXX Needs Optimization
        if isinstance(self.node, SetNode_Token):
            if self.node.token_restriction == '_':
                self.set_count += 1
                return True, ['node_' + self.node.node_id + '_all_tokens_' + str(self.set_count)]
            else:
                return False, []
        else:
            return False, []

    def what_temp_sets_do_you_need(self):
        temp_sets = []
        if isinstance(self.node, SetNode_Dep):

            filtering_function_name = 'filter_' + self.node.node_id
            temp_set_name = filtering_function_name +'_temp_set'
            temp_set_name_2 = filtering_function_name +'_temp_set_2'
            temp_sets.append(temp_set_name)
            temp_sets.append(temp_set_name_2)

            #the amount of positive deprels
            positive_count = 0
            for deprel, input_set in self.node.deprels:
                if not isinstance(deprel, DeprelNode_Not):
                    positive_count += 1
            for i in range(0, positive_count):
                temp_sets.append(filtering_function_name + '_C' + str(i))

        return temp_sets



    def what_sets_do_you_need(self):
        db_orders = []
        if isinstance(self.node, SetNode_Token):
            #Tag, Lemma or Word
            db_orders = self.set_node_token_into_db_label()
            if db_orders == None: import pdb;pdb.set_trace()
        #Give these needed sets a name
        name_dict = {}
        for dbo in db_orders:
            self.set_count += 1
            name_dict[dbo] = 'node_' + self.node.node_id + '_set_' + str(self.set_count)
        return db_orders, name_dict

    def what_arrays_do_you_need(self):
        db_orders = []
        if isinstance(self.node, DeprelNode):
            db_orders = self.deprel_node_into_db_label()
        #Give these needed sets a name
        name_dict = {}
        for dbo in db_orders:
            self.array_count += 1
            name_dict[dbo] = 'node_' + self.node.node_id + '_array_' + str(self.array_count)


        return db_orders, name_dict

    def deprel_node_into_db_label(self):
        #XXX change after format change!
        #This guy will need optimization later on!
        return_list = []
        prechar = '!'
        if self.node.negs_above:
            prechar = ''

        #XXX change after format change!
        if self.node.dep_restriction.startswith('<!'):
            prechar = ''
            return_list.append(prechar + u'dep_a_anyrel')
        if self.node.dep_restriction.startswith('>!'):
            prechar = ''
            return_list.append(prechar + u'gov_a_anyrel')

        if self.node.dep_restriction.split('@')[0] == '<':
            return_list.append(prechar + u'dep_a_anyrel')
            return return_list
        if self.node.dep_restriction.split('@')[0] == '>':
            return_list.append(prechar + u'gov_a_anyrel')
            return return_list

        if self.node.dep_restriction.startswith('>'):
            return_list.append(prechar + u'gov_a_' + self.node.dep_restriction[1:].split('@')[0].lstrip('!'))
            return return_list

        if self.node.dep_restriction.startswith('<'):
            return_list.append(prechar + u'dep_a_' + self.node.dep_restriction[1:].split('@')[0].lstrip('!'))
            return return_list


    def set_node_token_into_db_label(self):
        #XXX change after format change!
        #Raise Error if faulty query!
        prechar = '!'
        if self.node.negs_above:
            prechar = ''
        if self.node.proplabel == '' and self.node.token_restriction != '_':
            return [prechar + 'token_s_' + self.node.token_restriction]
        if self.node.proplabel == '@CGTAG' and self.node.token_restriction != '_':
            if not self.use_tag_list or self.use_tag_list and self.node.token_restriction in self.tag_list + self.val_dict.keys():

                if self.node.token_restriction in self.val_dict.keys():
                    return [prechar + 'tag_s_' + self.val_dict[self.node.token_restriction]]
                else:
                    return [prechar + 'tag_s_' + self.node.token_restriction]
            else:
                return [prechar + 'token_s_' + self.node.token_restriction]

        if self.node.proplabel == '@CGBASE' and self.node.token_restriction != '_':
            return [prechar + 'lemma_s_' + self.node.token_restriction]
        if self.node.proplabel != '':
            raise Exception('Faulty Proplabel!', self.node.proplabel, self.node.token_restriction)
        if self.node.token_restriction == '_':
            return []

    def what_output_do_you_need(self):
        if (isinstance(self.node, SetNode_Token) and not self.node.token_restriction == '_') or isinstance(self.node, SetNode_Dep):        
            return True, 'node_' + self.node.node_id + '_out', 'set'
        elif isinstance(self.node, DeprelNode):
            return True, 'node_' + self.node.node_id + '_out', 'array'
        else:
            return False, None, None

class SetManager():

    def __init__(self, nodes, node_dict, tag_list=[], val_dict={}):
        self.node_needs = {}
        self.tag_list = tag_list
        self.val_dict = val_dict
        #Interrogate the nodes
        for key in node_dict.keys():
            node = node_dict[key]
            self.node_needs[key] = {}
            ni = NodeInterpreter(node, tag_list=self.tag_list, val_dict=self.val_dict)

            #0. Are you compulsory
            #1. What sets do you need from the db?
            self.node_needs[key]['db_sets'], self.node_needs[key]['db_sets_label'] = ni.what_sets_do_you_need()
            self.node_needs[key]['all_tokens'], self.node_needs[key]['all_tokens_label'] = ni.do_you_need_all_tokens()
            #2. What arrays do you need from the db?
            self.node_needs[key]['db_arrays'], self.node_needs[key]['db_arrays_label'] = ni.what_arrays_do_you_need()
            #3. What temporary sets do you need?
            self.node_needs[key]['temp_sets'] = ni.what_temp_sets_do_you_need()
            #4. What temporary arrays do you need?
            #5. Do you need an output set, what is your output set called?
            self.node_needs[key]['own_output'], self.node_needs[key]['own_output_set'], self.node_needs[key]['own_output_set_type'] = ni.what_output_do_you_need()

def generate_search_code(node, tag_list=[], val_dict={}):

    #1. Go through the nodes
    #...and while doing it:
    #   -gather the needed sets, and their status(compulsory or non-compulsory)
    #   -the order in which these nodes should be executed
    #   -id each and every node
    #   -for these nodes give the proper inputs(as nodes, and stuff from the db)
    #   -the needed temporary sets and such
    #   -the names of the sets gathered from the db

    #This will id all the nodes, give them levels and fill negs_above
    node_dict = process_nodes(node)

    #Visualize the nodes :3
    #visualize(node, node_dict)
    #Works

    #Now, the order of execution
    order_of_execution = get_order_of_execution(node, node_dict)
    #visualize_order(order_of_execution)

    #Get all the sets this thing needs...
    set_manager = SetManager(node, node_dict, tag_list=tag_list, val_dict=val_dict)
    #... and visualize!
    #visualize_sets(set_manager, node_dict)
    #Seems to work!


    #Now for the code generation itself
    lines = []
    for l in get_class_function(set_manager):
        lines.append(l)

    for l in get_cinit_function(set_manager):
        lines.append(l)

    for l in get_init_function(set_manager):
        lines.append(l)

    for l in generate_code(node, set_manager, node_dict, order_of_execution, tag_list=tag_list, val_dict=val_dict):
        #if not '#' in l: 
        lines.append(l)

    return lines

def get_cinit_function(set_manager, max_len=2048):


    #XXX
    temp_set_list = []
    temp_array_list = []
    output_set_list = []

    load_list_set = []
    load_list_array = []


    for key in set_manager.node_needs.keys():

        for ikey in set_manager.node_needs[key]['db_sets_label'].keys():
            load_list_set.append((ikey, set_manager.node_needs[key]['db_sets_label'][ikey]))
        for ikey in set_manager.node_needs[key]['db_arrays_label'].keys():
            load_list_array.append((ikey, set_manager.node_needs[key]['db_arrays_label'][ikey]))
        for ikey in set_manager.node_needs[key]['all_tokens_label']:
            temp_set_list.append(ikey)
        for ikey in set_manager.node_needs[key]['temp_sets']:
            temp_set_list.append(ikey)
        if set_manager.node_needs[key]['own_output']:
            if set_manager.node_needs[key]['own_output_set_type'] == 'set':
                temp_set_list.append(set_manager.node_needs[key]['own_output_set'])
            elif set_manager.node_needs[key]['own_output_set_type'] == 'array':
                temp_array_list.append(set_manager.node_needs[key]['own_output_set'])

    lines = []
    lines.append('    def __cinit__(self):')
    lines.append('        self.sets=<void**>malloc(' + str(len(load_list_set) + len(load_list_array)) + '*sizeof(void*))')
    lines.append('        self.set_types=<int*>malloc(' + str(len(load_list_set) + len(load_list_array)) + '*sizeof(int))')

    query_list = []

    lines.append(' '*8 + 'self.empty_set = new TSet(' + str(max_len) + ')')

    for ts in temp_set_list:
        if ts not in load_list_set:
            lines.append(' '*8 + 'self.' + ts + ' = new TSet(' + str(max_len) + ')')

    for ts in temp_array_list:
        if ts not in load_list_set:
            lines.append(' '*8 + 'self.' + ts +   '= new TSetArray(' + str(max_len) + ')')

    load_list = load_list_set + load_list_array

    for i, key in enumerate(load_list):
        if 'set' in key[1]:
            lines.append(' '*8 + 'self.set_types[' + str(i) + '] = 1')
            lines.append(' '*8 + 'self.' + key[1] + '= new TSet(' + str(max_len) + ')')
            lines.append(' '*8 + 'self.sets[' + str(i) + '] = ' + 'self.' + key[1])
            query_list.append(u'' + key[0])
        elif 'array' in key[1]:
            lines.append(' '*8 + 'self.set_types[' + str(i) + '] = 2')
            lines.append(' '*8 + 'self.' + key[1] + ' = new TSetArray(' + str(max_len) + ')')
            lines.append(' '*8 + 'self.sets[' + str(i) + '] = ' + 'self.' + key[1])
            query_list.append(u'' + key[0])

    lines.append(' '*8 + 'self.query_fields = ' + str(query_list))
    return lines


def get_init_function(set_manager):

    all_tokens_list = []
    output_set_and_array_list = []

    for key in set_manager.node_needs.keys():
        for ikey in set_manager.node_needs[key]['all_tokens_label']:
            all_tokens_list.append(ikey)

    temp_set_list = []
    output_set_list = []
    temp_array_list = []

    for key in set_manager.node_needs.keys():

        for ikey in set_manager.node_needs[key]['temp_sets']:
            temp_set_list.append(ikey)
        #if set_manager.node_needs[key]['own_output']:
        #    temp_set_list.append(set_manager.node_needs[key]['own_output_set'])
        if set_manager.node_needs[key]['own_output']:
            if set_manager.node_needs[key]['own_output_set_type'] == 'set':
                temp_set_list.append(set_manager.node_needs[key]['own_output_set'])
            elif set_manager.node_needs[key]['own_output_set_type'] == 'array':
                temp_array_list.append(set_manager.node_needs[key]['own_output_set'])


    sentence_count_str = get_sentence_count_str(set_manager)
    lines = []
    lines.append(' '*4 + 'cdef void initialize(self):')
    lines.append(' '*8 + 'self.empty_set.set_length(self.' + sentence_count_str + '.tree_length)')

    for key in all_tokens_list:
            lines.append(' '*8 + 'self.' + key + '.set_length(self.' + sentence_count_str + '.tree_length)')
            lines.append(' '*8 + 'self.' + key + '.fill_ones()')

    #All sets and arrays , not lifted from the db,should be given len
    #There are output_sets, temp_sets, output_arrays
    for key in temp_set_list:
            lines.append(' '*8 + 'self.' + key + '.set_length(self.' + sentence_count_str + '.tree_length)')
            lines.append(' '*8 + 'self.' + key + '.copy(self.empty_set)')
            #lines.append(' '*8 + 'self.' + key + '.complement()')

    for key in temp_array_list:
            lines.append(' '*8 + 'self.' + key + '.set_length(self.' + sentence_count_str + '.tree_length)')

    #Maybe I should add the copies here?
    #    else:
    #        if key not in self.load_list_dict.keys():
    #            #Get the name of the set and clone
    #            lines.append(' '*8 + key + '.copy(' + inv_list_dict[self.init_dict[key]] + ')')

    #XXX uncomment if needed
    #The extras as well
    #for ts in self.temp_set_list:
    #    lines.append(' '*8 + ts + '.set_length(' + stuff + '.tree_length)')
            #lines.append(' '*4 + key + '.fill_ones()')            
    #stuff = inv_list_dict[self.all_arrays[0]]
    #for ts in self.temp_array_list:
    #    lines.append(' '*8 + ts + '.set_length(' + stuff + '.tree_length)')
    #        #lines.append(' '*4 + key + '.fill_ones()')      
    #Reverse the load_list_dict

    if len(lines) < 2:
        lines.append(' '*8 + 'pass')  
    return lines

def get_class_function(set_manager):
    lines = []

    temp_set_list = []
    temp_array_list = []
    output_set_list = []

    load_list_set = []
    load_list_array = []

    for key in set_manager.node_needs.keys():

        for ikey in set_manager.node_needs[key]['db_sets_label'].keys():
            load_list_set.append((ikey, set_manager.node_needs[key]['db_sets_label'][ikey]))
        for ikey in set_manager.node_needs[key]['db_arrays_label'].keys():
            load_list_array.append((ikey, set_manager.node_needs[key]['db_arrays_label'][ikey]))
        for ikey in set_manager.node_needs[key]['all_tokens_label']:
            temp_set_list.append(ikey)
        for ikey in set_manager.node_needs[key]['temp_sets']:
            temp_set_list.append(ikey)
        if set_manager.node_needs[key]['own_output']:
            if set_manager.node_needs[key]['own_output_set_type'] == 'set':
                temp_set_list.append(set_manager.node_needs[key]['own_output_set'])
            elif set_manager.node_needs[key]['own_output_set_type'] == 'array':
                temp_array_list.append(set_manager.node_needs[key]['own_output_set'])


    lines.append('cdef class  GeneratedSearch(Search):')
    for key in load_list_set:
        lines.append(' ' * 4 + 'cdef TSet *' + key[1])

    for key in load_list_array:
        lines.append(' ' * 4 + 'cdef TSetArray *' + key[1])

    #Extra and temp
    for key in temp_set_list:
        lines.append(' ' * 4 + 'cdef TSet *' + key)
    
    for key in temp_array_list:
        lines.append(' ' * 4 + 'cdef TSetArray *' + key)

    lines.append(' ' * 4 + 'cdef TSet *empty_set')
    lines.append(' ' * 4 + 'cdef public object query_fields')

    return lines

def generate_code(nodes, set_manager, node_dict, order_of_execution, tag_list=[], val_dict={}):

    #Start building the match code, by going through the nodes in the order of ooe
    #A mysterious object will deal with the code_block creation

    #This will be practically for filtering functions
    extra_functions = []
    match_code_lines = []
    node_output_dict = {}

    for node in order_of_execution:
        match_block, node_extra_functions = generate_code_for_a_node(node, set_manager, node_dict, node_output_dict, tag_list=tag_list, val_dict=val_dict)

        match_code_lines.extend(match_block)
        extra_functions.extend(node_extra_functions)

    lines = []
    lines.append('    cdef TSet* exec_search(self):')
    for l in match_code_lines:
        lines.append(' '*8 + l)
    lines.append(' '*8 + 'return self.' + node_output_dict['0'])

    for f in extra_functions:
        for l in f:
            lines.append(' '*4 + l)

    return lines

def generate_code_for_a_node(node, set_manager, node_dict, node_output_dict, tag_list=[], val_dict={}):

    extra_functions = []
    match_lines = []

    match_lines.append('#' + node.node_id)
    match_lines.append('#' + node.to_unicode())
    node_ni = NodeInterpreter(node, tag_list=tag_list, val_dict=val_dict)
    #SetNode_Token
    if isinstance(node, SetNode_Token):
        #I'll find the name of the assigned set
        what_I_need_from_the_db = node_ni.set_node_token_into_db_label()
        if len(what_I_need_from_the_db) < 1:
            #Ah, this is all tokens kind of SetNode_Token
            #I'll just report it as my output
            output_set = set_manager.node_needs[node.node_id]['all_tokens_label'][0]
            match_lines.append('#Reporting ' + output_set + ' as output set')
            node_output_dict[node.node_id] = output_set
            return match_lines, extra_functions
        else:
            #Get the setname
            db_set = set_manager.node_needs[node.node_id]['db_sets_label'][what_I_need_from_the_db[0]]
            output_set_name = set_manager.node_needs[node.node_id]['own_output_set']
            match_lines.append('self.' + output_set_name + '.copy(self.' + db_set + ')')
            match_lines.append('#Reporting ' + output_set_name + ' as output set')
            node_output_dict[node.node_id] = output_set_name
            return match_lines, extra_functions

    elif isinstance(node, DeprelNode):

        #XXX hack!
        #XXX change after format change!
        negated = False
        if node.dep_restriction.startswith('<!'):
            negated=True
        if node.dep_restriction.startswith('>!'):
            negated=True
 
        output_set_name = set_manager.node_needs[node.node_id]['own_output_set']
        #I'll find the name of the assigned array
        what_I_need_from_the_db = node_ni.deprel_node_into_db_label()

        #Get the setname
        if not negated:
            db_set = set_manager.node_needs[node.node_id]['db_arrays_label'][what_I_need_from_the_db[0]]
            output_set_name = set_manager.node_needs[node.node_id]['own_output_set']
            match_lines.append('self.' + output_set_name + '.copy(self.' + db_set + ')')
            match_lines.append('#Reporting ' + output_set_name + ' as output array')
            node_output_dict[node.node_id] = output_set_name
        else:

            #XXX Kind of a hacky solution

            db_set_labels = []
            desires = []
            #So in this case I've got like
            for desire in what_I_need_from_the_db:
                db_set = set_manager.node_needs[node.node_id]['db_arrays_label'][desire]
                db_set_labels.append(db_set)
                desires.append(desire)

            #Since this is negated we separate an anyrel
            anyrel_set = None
            the_db_set = None
            for desire, label in zip(desires, db_set_labels):
                if 'anyrel' in desire:
                    anyrel_set = label
                else:
                    the_db_set = label


            #minus update
            match_lines.append('self.' + output_set_name + '.copy(self.' + anyrel_set + ')')
            match_lines.append('self.' + output_set_name + '.minus_update(self.' + the_db_set + ')')
            match_lines.append('#Reporting ' + output_set_name + ' as output array')
            node_output_dict[node.node_id] = output_set_name

        #XXX format change!
        #Left/Right update comes here and is done to the output_set
        if node.dep_restriction[-2:] == '@L':
            match_lines.append('self.' + output_set_name + '.filter_direction(True)')
        elif node.dep_restriction[-2:] == '@R':
            match_lines.append('self.' + output_set_name + '.filter_direction(False)')

        return match_lines, extra_functions
        
    elif isinstance(node, SetNode_And):

        #Get input nodes
        input_set_1 = node_output_dict[node.setnode1.node_id]
        input_set_2 = node_output_dict[node.setnode2.node_id]
        match_lines.append('self.' + input_set_1 + '.intersection_update(self.' + input_set_2 + ')')
        if not node.negs_above:
            match_lines.append('if self.' + input_set_1 + '.is_empty(): return self.' + input_set_1)
        match_lines.append('#Reporting ' + input_set_1 + ' as output set')
        node_output_dict[node.node_id] = input_set_1

    elif isinstance(node, DeprelNode_And):

        #Get input nodes
        input_array_1 = node_output_dict[node.dnode1.node_id]
        input_array_2 = node_output_dict[node.dnode2.node_id]
        match_lines.append('self.' + input_array_1 + '.intersection_update(self.' + input_array_2 + ')')
        match_lines.append('#Reporting ' + input_array_1 + ' as output array')
        node_output_dict[node.node_id] = input_array_1

    elif isinstance(node, SetNode_Or):

        #Get input nodes
        input_set_1 = node_output_dict[node.setnode1.node_id]
        input_set_2 = node_output_dict[node.setnode2.node_id]
        match_lines.append('self.' + input_set_1 + '.union_update(self.' + input_set_2 + ')')
        if not node.negs_above:
            match_lines.append('if self.' + input_set_1 + '.is_empty(): return self.' + input_set_1)
        match_lines.append('#Reporting ' + input_set_1 + ' as output set')
        node_output_dict[node.node_id] = input_set_1

    elif isinstance(node, DeprelNode_Or):

        #Get input nodes
        input_array_1 = node_output_dict[node.dnode1.node_id]
        input_array_2 = node_output_dict[node.dnode2.node_id]
        match_lines.append('self.' + input_array_1 + '.union_update(self.' + input_array_2 + ')')
        match_lines.append('#Reporting ' + input_array_1 + ' as output array')
        node_output_dict[node.node_id] = input_array_1


    elif isinstance(node, SetNode_Not):

        input_set = node_output_dict[node.setnode1.node_id]
        match_lines.append('self.' + input_set + '.complement()')
        match_lines.append('#Reporting ' + input_set + ' as output set')
        node_output_dict[node.node_id] = input_set

    elif isinstance(node, DeprelNode_Not):

        input_array = node_output_dict[node.dnode1.node_id]
        #Why? So that SetNode_Dep can have negative depres

        #XXX terrible hack!
        #the complement, if needed is done on Deprel
        #This should be used only as an input to SetNode_Dep

        #if not isinstance(node.parent_node, SetNode_Dep):
        #    match_lines.append('self.' + input_array + '.complement_update()')
        match_lines.append('#Reporting ' + input_array + ' as output set')
        node_output_dict[node.node_id] = input_array

    elif isinstance(node, SetNode_Dep):

        #0. Create the tables needed for the filtering function
        #   (mapping_array, input_set, negated)
        #   ....

        #[(deprel, setnode2), ...... ]
        #table_of_restrictions = []
        deprels = []
        input_sets = []
        negateds = []
        for deprel, input_set in node.deprels:
            negated = False
            if isinstance(deprel, DeprelNode_Not):
                negated = True
            #table_of_restrictions.append((deprel, input_set, negated))
            deprels.append('self.' + node_output_dict[deprel.node_id])
            input_sets.append('self.' + node_output_dict[input_set.node_id])
            negateds.append(negated)

        filtering_arguments = ['t',]
        for dr in deprels:
            filtering_arguments.append(dr)
        for iset in input_sets:
            filtering_arguments.append(iset)

        filtering_function_name = 'filter_' + node.node_id

        #1. Start building the Filtering function itself
        sentence_count_str = get_sentence_count_str(set_manager)
        filtering_function = generate_filtering(filtering_function_name, deprels, input_sets, negateds, sentence_count_str)
        extra_functions.append(filtering_function)


        #Index node
        index_node = node_output_dict[node.index_node.node_id]
        #output set
        output_set = set_manager.node_needs[node.node_id]['own_output_set']

        match_lines.append('for t in range(0, self.' + sentence_count_str + '.tree_length):')
        match_lines.append(' ' * 4 + 'if not self.' + index_node + '.has_item(t): continue')
        match_lines.append(' ' * 4 + 'if self.' + filtering_function_name + '(' + ','.join(filtering_arguments) + '): self.' + output_set + '.add_item(t)')
        match_lines.append('#Reporting ' + output_set + ' as output set')
        node_output_dict[node.node_id] = output_set

    return match_lines, extra_functions


def generate_filtering(filtering_function_name, deprels, input_sets, negateds, sentence_count_str):
    line = []
    compulsory_sets = []
    negated_sets = []
    for i, neg in enumerate(negateds):
        if neg:
            negated_sets.append(i)
        else:
            compulsory_sets.append(i)
    arguments = ['self', 'int t']
    for i, dr in enumerate(deprels):
        arguments.append('TSetArray *M' + str(i))
    for i, iset in enumerate(input_sets):
        arguments.append('TSet *S' + str(i))    

    line.append('cdef bool ' + filtering_function_name + '(' + ','.join(arguments) + '):')

    temp_set_name = 'self.' + filtering_function_name +'_temp_set'
    temp_set_name_2 = 'self.' + filtering_function_name +'_temp_set_2'

    #Temporary full set which, we intersect these
    #line.append(' '* 4 + filtering_function_name +'_temp_set.set_length(' + sentence_count_str + '.tree_length)')
    #I'll just copy the temp_set

    #line.append(' '*4 + 'for i in range(0, ' + str(len(negated_sets)) + '):')
    for ns in negated_sets:
        line.append(' '*4 + 'M' + str(ns) + '.get_set(t, ' + temp_set_name + ')')
        line.append(' '*4 + temp_set_name_2 + '.copy(' + temp_set_name + ')')
        line.append(' '*4 + temp_set_name_2 + '.intersection_update(S' + str(ns) + ')')
        line.append(' '*4 + 'if not ' + temp_set_name_2 + '.is_empty(): return False')

    for i, comp in enumerate(compulsory_sets):
        line.append(' '*4 + 'M' + str(comp) + '.get_set(t, ' + temp_set_name + ')')
        line.append(' '*4 + 'self.' + filtering_function_name + '_C' + str(i) + '.copy(' + temp_set_name + ')')
        line.append(' '*4 + 'self.' + filtering_function_name + '_C' + str(i) + '.intersection_update(S' + str(comp) + ')')
        line.append(' '*4 + 'if self.' + filtering_function_name + '_C' + str(i) + '.is_empty(): return False')

    #This doesnt ensure correctness
    '''
    if len(compulsory_sets) > 1:
        
        line.append(' '* 4 + temp_set_name + '.copy(self.' + filtering_function_name + '_C' + str(0) + ')')
        for i, cs in enumerate(compulsory_sets[1:]):
            line.append(' '* 4 + temp_set_name + '.intersection_update(self.' + filtering_function_name + '_C' + str(i+1) + ')')
        line.append(' '*4 + 'if ' + temp_set_name + '.is_empty(): return True')
   '''

    if len(compulsory_sets) > 1:
        
        line.append(' '* 4 + temp_set_name + '.copy(self.' + filtering_function_name + '_C' + str(0) + ')')
        for i, cs in enumerate(compulsory_sets[1:]):
            line.append(' '* 4 + temp_set_name + '.union_update(self.' + filtering_function_name + '_C' + str(i+1) + ')')

        line.append(' '*4 + 'len_temp_set = 0')
        line.append(' '*4 + 'for n in range(0, self.' + sentence_count_str + '.tree_length):')
        line.append(' '*8 + 'if ' + temp_set_name + '.has_item(n): len_temp_set += 1')
        line.append(' '*4 + 'if len_temp_set < ' + str(len(compulsory_sets)) + ': return False')

    forbidden_tokens = []
    for i, cs in enumerate(compulsory_sets):
        line.append(' ' * (4 + 4*i) + 'for t' + str(cs) + ' in range(0, self.' + sentence_count_str + '.tree_length):') 
        line.append(' ' * (8 + 4*i) + 'if not self.' + filtering_function_name + '_C' + str(i) + '.has_item(t' + str(cs) + '): continue')
        if len(forbidden_tokens) > 0:
            logic = 't' + str(cs) + '==' + str(forbidden_tokens[0])
            for ft in forbidden_tokens[1:]:
                logic += ' or ' + 't' + str(cs) + '==' + str(ft)
            line.append(' ' * (8 + 4*i) + 'if ' + logic + ': continue')
        forbidden_tokens.append('t' + str(cs))
    if len(compulsory_sets) > 0:
        line.append(' ' * (8 + 4*i) + 'return True')
        line.append(' ' * 4 + 'return False')
    else:
        line.append(' ' * 4 + 'return True')

    return line

def get_sentence_count_str(set_manager):
    #Search for some random set or array and return proper line
    compulsory = []
    non_compulsory = []

    for key in set_manager.node_needs.keys():
        for ikey in set_manager.node_needs[key]['db_sets_label'].keys():
            db_set = set_manager.node_needs[key]['db_sets_label'][ikey]
            if ikey.startswith('!'):
                compulsory.append(db_set)
                break
            else:
                non_compulsory.append(db_set)
        for ikey in set_manager.node_needs[key]['db_arrays_label'].keys():
            db_set = set_manager.node_needs[key]['db_arrays_label'][ikey]
            if ikey.startswith('!'):
                compulsory.append(db_set)
                break
            else:
                non_compulsory.append(db_set)

    if len(compulsory) > 0:
        return compulsory[0]
    if len(non_compulsory) < 1:
        raise Exception('Cannot get sentence length!')
    return non_compulsory[0]

def visualize_sets(set_manager, node_dict):

    print
    print 'Node Sets'

    for key in set_manager.node_needs.keys():

        print
        print node_dict[key].to_unicode()
        print 'Sets needed from the db:'
        for ikey in set_manager.node_needs[key]['db_sets_label'].keys():
            print ikey, set_manager.node_needs[key]['db_sets_label'][ikey]
        print 'Arrays needed from the db:'
        for ikey in set_manager.node_needs[key]['db_arrays_label'].keys():
            print ikey, set_manager.node_needs[key]['db_arrays_label'][ikey]
        print 'All_tokens needed:'
        for ikey in set_manager.node_needs[key]['all_tokens_label']:
            print ikey
        print 'Output_sets needed:'
        if set_manager.node_needs[key]['own_output']:
            print set_manager.node_needs[key]['own_output_set']

def visualize_order(order):

    print 'ORDER:'
    for node in order:
        print node.node_id

def get_order_of_execution(node, node_dict):

    order_of_exec = []
    #Get levels
    #Go through the levels, starting from the bottom
    #Do the compulsory ones first
    
    levels = set()
    lev_nodes = {}
    for key in node_dict.keys():
        node = node_dict[key]
        if node.level not in lev_nodes.keys():
            lev_nodes[node.level] = []
        lev_nodes[node.level].append(node)
        levels.add(node.level)

    levels = list(levels)
    levels.sort()
    levels.reverse()

    for lev in levels:
        compulsory_lev_nodes = []
        non_compulsory_lev_nodes = []
        for l_node in lev_nodes[lev]:
            if l_node.negs_above:
                non_compulsory_lev_nodes.append(l_node)
            else:
                compulsory_lev_nodes.append(l_node)

        order_of_exec.extend(compulsory_lev_nodes)
        order_of_exec.extend(non_compulsory_lev_nodes)

    return order_of_exec


def visualize(node, node_dict):


    #Hmmm...
    #The point is to see whether it worked!

    #Get levels
    #Print node info per level
    levels = set()
    lev_nodes = {}
    for key in node_dict.keys():
        node = node_dict[key]
        if node.level not in lev_nodes.keys():
            lev_nodes[node.level] = []
        lev_nodes[node.level].append(node)
        levels.add(node.level)

    levels = list(levels)
    levels.sort()

    for lev in levels:
        print 
        print 'Level:', lev
        print

        for node in lev_nodes[lev]:

            print node.to_unicode()
            print 'level', node.level
            print 'compulsory', not node.negs_above
            print 'node_id', node.node_id
            print


def process_nodes(node):

    node_dict = {}
    id_the_nodes(node, '0', 0, False, node_dict)
    return node_dict

def id_the_nodes(node, pid, lev, negs_above, node_dict):

    #Neg True if (this is a Not node or negs_above)
    negs = False
    if negs_above or node.neg:
        negs = True

    if isinstance(node, SetNode_Or) or isinstance(node, DeprelNode_Or):
        negs = True

    node.node_id = pid
    node.level = lev
    node.negs_above = negs
    node_dict[pid] = node

    if not isinstance(node, SetNode_Dep):

        kid_nodes = node.get_kid_nodes()
        for i, kid_node in enumerate(kid_nodes):
            kid_node.parent_node = node
            id_the_nodes(kid_node, pid + '_' + str(i), lev + 1, negs, node_dict)
    else:

        id_the_nodes(node.index_node, pid + '_i', lev + 1, negs, node_dict)
        node.index_node.parent_node = node

        #Check if the deprel is negative or not:
        for i, deprel_tuple in enumerate(node.deprels):
            #deprel_tuple[0] = deprel, deprel_tuple[1] = token_set

            deprel_tuple[0].parent_node = node
            deprel_tuple[1].parent_node = node

            if isinstance(deprel_tuple[0], DeprelNode_Not):
                id_the_nodes(deprel_tuple[1], pid + '_' + str(i) + '_0', lev + 1, True, node_dict)
                id_the_nodes(deprel_tuple[0], pid + '_' + str(i) + '_1', lev + 1, True, node_dict)
            else:
                id_the_nodes(deprel_tuple[1], pid + '_' + str(i) + '_0', lev + 1, negs, node_dict)
                id_the_nodes(deprel_tuple[0], pid + '_' + str(i) + '_1', lev + 1, negs, node_dict)

def write_cython_code(lines, output_file):

    out = codecs.open(output_file, 'wt', 'utf8')

    magic_lines = '''# distutils: language = c++
# distutils: include_dirs = setlib
# distutils: extra_objects = setlib/pytset.so
# distutils: sources = query_functions.cpp
include "search_common.pxi"\n'''

    out.write(magic_lines)

    for line in lines:
        out.write(line + '\n')

    out.close()

def main():
    '''
    Exploring the node tree, trying to figure very naive order of execution.
    With a naive attempt at code generation
    '''

    json_filename = 'symbols.json'
    json_lines = open(json_filename, 'rt').readline()
    json_dict = json.loads(json_lines)

    tag_list = []
    val_dict = {}

    for key in json_dict.keys():
        should_be_in_val_dict = True
        val_tuples = []
        for tpl in json_dict[key]:
            if tpl[0] == 'VAL':
                val_tuples.append(tpl)
            else:
                #If this is also tag or something else, then it shouldn't be interpreted as anything else
                should_be_in_val_dict = False
                if tpl[0] in ['TAG', 'CAT', 'CAT=VAL']:
                    tag_list.append(key)

        if len(val_tuples) > 0 and should_be_in_val_dict:
            #Find the maximum
            max_tuple = val_tuples[0]
            for vt in val_tuples[1:]:
                if vt[-1] > max_tuple[-1]:
                    max_tuple = vt
            val_dict[key] = max_tuple[1]

    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    parser.add_argument('output_file')
    args = parser.parse_args()

    e_parser=yacc.yacc()
    for expression in args.expression:
        nodes = e_parser.parse(expression)
        print nodes.to_unicode()

    code_lines = generate_search_code(nodes, tag_list=tag_list, val_dict=val_dict)
    #cdd = code(nodes)
    #lines = cdd.get_search_code()
    filename = str(args.output_file)
    write_cython_code(code_lines, filename + '.pyx')


def generate_and_write_search_code_from_expression(expression, filename, json_filename=''):

    try:
        json_f = open(json_filename, 'rt')
        json_line = json_f.readline()
        json_f.close()
        json_dict = json.loads(json_line)
    except:
        json_dict = {}

    tag_list = []
    val_dict = {}

    for key in json_dict.keys():
        should_be_in_val_dict = True
        val_tuples = []
        for tpl in json_dict[key]:
            if tpl[0] == 'VAL':
                val_tuples.append(tpl)
            else:
                #If this is also tag or something else, then it shouldn't be interpreted as anything else
                should_be_in_val_dict = False
                if tpl[0] in ['TAG', 'CAT', 'CAT=VAL']:
                    tag_list.append(key)

        if len(val_tuples) > 0 and should_be_in_val_dict:
            #Find the maximum
            max_tuple = val_tuples[0]
            for vt in val_tuples[1:]:
                if vt[-1] > max_tuple[-1]:
                    max_tuple = vt
            val_dict[key] = max_tuple[1]



    e_parser=yacc.yacc()
    nodes = e_parser.parse(expression)
    #print nodes.to_unicode()
    code_lines = generate_search_code(nodes, tag_list=tag_list, val_dict=val_dict)
    write_cython_code(code_lines, filename + '.pyx')

if __name__ == "__main__":
    main()
