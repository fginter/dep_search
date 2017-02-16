from redone_expr import *
import sys
import codecs
import json
import sys

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
            #if db_orders == None: import pdb;pdb.set_trace()
        name_dict = {}
        for dbo in db_orders:
            self.set_count += 1
            name_dict[dbo] = 'node_' + self.node.node_id + '_set_' + str(self.set_count)
        return db_orders, name_dict

    def what_arrays_do_you_need(self):
        db_orders = []
        if isinstance(self.node, DeprelNode):
            db_orders = self.deprel_node_into_db_label()
        name_dict = {}
        for dbo in db_orders:
            self.array_count += 1
            if not dbo in name_dict:
                name_dict[dbo] = ['node_' + self.node.node_id + '_array_' + str(self.array_count)]
            else:
                name_dict[dbo].append('node_' + self.node.node_id + '_array_' + str(self.array_count))
        return db_orders, name_dict

    def deprel_node_into_db_label(self):
        return_list = []
        prechar = '!'
        if self.node.negs_above:
            prechar = ''
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

            dtype = self.node.dep_restriction[1:].split('@')[0].lstrip('!')
            
            if len(dtype) < 1:
                dtype = 'anyrel'

            if dtype.startswith('lin'):
                return_list.append(prechar + u'no_db_' + dtype)
            else:
                return_list.append(prechar + u'gov_a_' + dtype)

            return return_list

        if self.node.dep_restriction.startswith('<'):

            dtype = self.node.dep_restriction[1:].split('@')[0].lstrip('!')
            if len(dtype) < 1:
                dtype = 'anyrel'

            if dtype.startswith('lin'):
                return_list.append(prechar + u'no_db_' + dtype)
            else:
                return_list.append(prechar + u'dep_a_' + dtype)

            return return_list


    def set_node_token_into_db_label(self):
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
        set_and_array_labels = []

        for key in node_dict.keys():
            node = node_dict[key]
            self.node_needs[key] = {}
            ni = NodeInterpreter(node, tag_list=self.tag_list, val_dict=self.val_dict)
            self.node_needs[key]['db_sets'], self.node_needs[key]['db_sets_label'] = ni.what_sets_do_you_need()
            self.node_needs[key]['all_tokens'], self.node_needs[key]['all_tokens_label'] = ni.do_you_need_all_tokens()
            #2. What arrays do you need from the db?
            self.node_needs[key]['db_arrays'], self.node_needs[key]['db_arrays_label'] = ni.what_arrays_do_you_need()
            #3. What temporary sets do you need?
            self.node_needs[key]['temp_sets'] = ni.what_temp_sets_do_you_need()
            #4. What temporary arrays do you need?
            #5. Do you need an output set, what is your output set called?
            self.node_needs[key]['own_output'], self.node_needs[key]['own_output_set'], self.node_needs[key]['own_output_set_type'] = ni.what_output_do_you_need()

            #set_and_array_labels.extend(self.node_needs[key]['db_sets_label'])
            #set_and_array_labels.extend(self.node_needs[key]['db_arrays_label'])
            for label in self.node_needs[key]['db_sets_label']:
                if 'no_db' not in label:
                    set_and_array_labels.append(label)

            for label in self.node_needs[key]['db_arrays_label']:
                if 'no_db' not in label:
                    set_and_array_labels.append(label)

        #print 'set_and_array_labels', set_and_array_labels
        #If nothing was found add a virtual node 'extra' just to add something into the db_query
        if len(set_and_array_labels) < 1:
            self.node_needs['extra'] = {'temp_sets': [], 'all_tokens': False, 'all_tokens_label': [], 'db_arrays_label': {u'!dep_a_anyrel': ['extra_array']}, 'db_sets': [], 'db_arrays': [u'!dep_a_anyrel'], 'db_sets_label': {}, 'own_output_set': '', 'own_output_set_type': '', 'own_output': False}


def generate_search_code(node, tag_list=[], val_dict={}):

    node_dict = process_nodes(node)
    order_of_execution = get_order_of_execution(node, node_dict)
    set_manager = SetManager(node, node_dict, tag_list=tag_list, val_dict=val_dict)
    lines = []
    for l in get_class_function(set_manager):
        lines.append(l)

    for l in get_cinit_function(set_manager):
        lines.append(l)

    for l in get_init_function(set_manager):
        lines.append(l)

    for l in generate_code(node, set_manager, node_dict, order_of_execution, tag_list=tag_list, val_dict=val_dict):
        lines.append(l)

    return lines

def get_cinit_function(set_manager, max_len=2048):

    temp_set_list = []
    temp_array_list = []
    output_set_list = []
    load_list_set = []
    load_list_array = []

    for key in set_manager.node_needs.keys():

        for ikey in set_manager.node_needs[key]['db_sets_label'].keys():
            load_list_set.append((ikey, set_manager.node_needs[key]['db_sets_label'][ikey]))
        for ikey in set_manager.node_needs[key]['db_arrays_label'].keys():

            for v in set_manager.node_needs[key]['db_arrays_label'][ikey]:
                if not ikey.strip('!').startswith('no_db_'):
                    load_list_array.append((ikey, v))
                else:
                    temp_array_list.append(v)

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

    for key in temp_array_list:
            lines.append(' '*8 + 'self.' + key + '.set_length(self.' + sentence_count_str + '.tree_length)')

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
            for label in set_manager.node_needs[key]['db_arrays_label'][ikey]:
                load_list_array.append((ikey, label))
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

def handle_root_extra_comments(node, set_manager):

    output_lines = []
    #Parse the comments
    for com in node.extra_comments:
       if com.startswith('max_tree_len='):
           tree_len = int(com.split('=')[-1])
           sentence_count_str = get_sentence_count_str(set_manager)
           output_lines.append('if ' + 'self.' + sentence_count_str + '.tree_length >= ' + str(tree_len) + ': return self.empty_set')

       if com.startswith('min_tree_len='):
           tree_len = int(com.split('=')[-1])
           sentence_count_str = get_sentence_count_str(set_manager)
           output_lines.append('if ' + 'self.' + sentence_count_str + '.tree_length <= ' + str(tree_len) + ': return self.empty_set')

    return output_lines


def generate_code(nodes, set_manager, node_dict, order_of_execution, tag_list=[], val_dict={}):

    extra_functions = []
    match_code_lines = []
    node_output_dict = {}

    #The root node should have its extra comments inspected
    if len(order_of_execution[-1].extra_comments) > 0:
        #
        for l in handle_root_extra_comments(order_of_execution[-1], set_manager):
            match_code_lines.append(l)

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
            db_set = set_manager.node_needs[node.node_id]['db_arrays_label'][what_I_need_from_the_db[0]][0]
            #o_name_db_set = db_set = set_manager.node_needs[node.node_id]['db_arrays_label'][what_I_need_from_the_db[0]][0]
            output_set_name = set_manager.node_needs[node.node_id]['own_output_set']
            match_lines.append('self.' + output_set_name + '.copy(self.' + db_set + ')')

            #We need linear order set
            if what_I_need_from_the_db[0].strip('!').startswith('no_db_lin'):

                the_int = 1
                the_beg = 1
                #TODO: reduce hackiness of this contraption!
                try:
                    the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0])
                    the_beg = 1
                except:
                    #pass
                    #the_int = 1
                    try:
                        if ';' in what_I_need_from_the_db[0]:

                            the_int_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[1]
                            the_beg_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[0]

                            if len(the_int_str) < 1:
                                #Get sentence_ln
                                sentence_count_str = get_sentence_count_str(set_manager)
                                the_int = 'self.' + sentence_count_str + '.tree_length'
                            else:
                                the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[1])

                            the_beg = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[0])


                        elif ':' in what_I_need_from_the_db[0]:

                            the_int_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[1]
                            the_beg_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[0]

                            if len(the_int_str) < 1:
                                #Get sentence_ln
                                sentence_count_str = get_sentence_count_str(set_manager)
                                the_int = 'self.' + sentence_count_str + '.tree_length'
                            else:
                                the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[1])

                            the_beg = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[0])
                    except:
                        pass

                match_lines.append('self.' + output_set_name + '.make_lin_2(' + str(the_int) + ', ' + str(the_beg) + ')')

            if node.dep_restriction[-2:] == '@L':
                match_lines.append('self.' + output_set_name + '.filter_direction(True)')
            elif node.dep_restriction[-2:] == '@R':
                match_lines.append('self.' + output_set_name + '.filter_direction(False)')

            match_lines.append('#Reporting ' + output_set_name + ' as output array')
            node_output_dict[node.node_id] = output_set_name
        else:

            #This deprel is negated!
            anyrel_for_negation = ''
            db_array_for_use = ''

            desires = []
            db_set_labels = []

            for desire in set(what_I_need_from_the_db):
                db_sets = set_manager.node_needs[node.node_id]['db_arrays_label'][desire]
                for dbs in db_sets:
                    db_set_labels.append(dbs)
                    desires.append(desire)

            for d, l in zip(desires, db_set_labels):
                if 'anyrel' in d and len(anyrel_for_negation) < 1:
                    anyrel_for_negation = l
                else:
                    db_array_for_use = l

            db_set = db_array_for_use
            output_set_name = set_manager.node_needs[node.node_id]['own_output_set']
            match_lines.append('self.' + output_set_name + '.copy(self.' + anyrel_for_negation + ')')

            match_lines.append('#' + str(what_I_need_from_the_db))


            '''
            if what_I_need_from_the_db[1].strip('!').startswith('no_db_lin'):

                the_int = 1
                #TODO: reduce hackiness of this contraption!
                try:
                    the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0])
                except:
                    the_int = 1
            '''
            #We need linear order set
            if what_I_need_from_the_db[0].strip('!').startswith('no_db_lin'):

                the_int = 2
                the_beg = 1
                #TODO: reduce hackiness of this contraption!
                try:
                    the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0])
                    the_beg = 1
                except:
                    #pass
                    #the_int = 1
                    try:

                        if ';' in what_I_need_from_the_db[0]:

                            the_int_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[1]
                            the_beg_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[0]

                            if len(the_int_str) < 1:
                                #Get sentence_ln
                                sentence_count_str = get_sentence_count_str(set_manager)
                                the_int = 'self.' + sentence_count_str + '.tree_length'
                            else:
                                the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[1])

                            the_beg = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(';')[0])


                        elif ':' in what_I_need_from_the_db[0]:

                            the_int_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[1]
                            the_beg_str = what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[0]

                            if len(the_int_str) < 1:
                                #Get sentence_ln
                                sentence_count_str = get_sentence_count_str(set_manager)
                                the_int = 'self.' + sentence_count_str + '.tree_length'
                            else:
                                the_int = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[1])

                            the_beg = int(what_I_need_from_the_db[0].strip('!').split('_')[3].split('@')[0].split(':')[0])

                    except:
                        pass

                match_lines.append('self.' + output_set_name + '.make_lin_2(' + str(the_int) + ', ' + str(the_beg) + ')')

                #sentence_count_str = get_sentence_count_str(set_manager)
                #match_lines.append('self.' + db_set + '.set_length(self.' + sentence_count_str + '.tree_length)')
                #match_lines.append('self.' + output_set_name + '.set_length(self.' + sentence_count_str + '.tree_length)')

                #match_lines.append('self.' + db_set + '.make_lin(' + str(the_int) + ')')
                #match_lines.append('self.' + output_set_name + '.make_lin(self.' + output_set_name + '.tree_length)')

            if node.dep_restriction[-2:] == '@L':
                match_lines.append('self.' + db_set + '.filter_direction(True)')
            elif node.dep_restriction[-2:] == '@R':
                match_lines.append('self.' + db_set + '.filter_direction(False)')

            match_lines.append('self.' + output_set_name + '.minus_update(self.' + db_set + ')')

            match_lines.append('#Reporting ' + output_set_name + ' as output array')
            node_output_dict[node.node_id] = output_set_name

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


    elif isinstance(node, SetNode_Eq):

        #Get input nodes
        input_set_1 = node_output_dict[node.setnode1.node_id]
        input_set_2 = node_output_dict[node.setnode2.node_id]

        sentence_count_str = get_sentence_count_str(set_manager)
        match_lines.append('for t in range(0, self.' + sentence_count_str + '.tree_length):')
        match_lines.append(' ' * 4 + 'if not self.' + input_set_1 + '.has_item(t) and self.' + input_set_2 + '.has_item(t):')
        match_lines.append(' '*8 + 'self.'+ input_set_1 + '.copy(self.empty_set)')
        match_lines.append(' '*8 + 'break')

        match_lines.append(' ' * 4 + 'if self.' + input_set_1 + '.has_item(t) and not self.' + input_set_2 + '.has_item(t):')
        match_lines.append(' '*8 + 'self.'+ input_set_1 + '.copy(self.empty_set)')
        match_lines.append(' '*8 + 'break')

        if not node.negs_above:
            match_lines.append('if self.' + input_set_1 + '.is_empty(): return self.' + input_set_1)
        match_lines.append('#Reporting ' + input_set_1 + ' as output set')
        node_output_dict[node.node_id] = input_set_1


    elif isinstance(node, SetNode_SubEq):

        #Get input nodes
        input_set_1 = node_output_dict[node.setnode1.node_id]
        input_set_2 = node_output_dict[node.setnode2.node_id]

        #An intersection update for the set no 2.
        match_lines.append('self.' + input_set_2 + '.intersection_update(self.' + input_set_1  + ')')

        sentence_count_str = get_sentence_count_str(set_manager)
        match_lines.append('for t in range(0, self.' + sentence_count_str + '.tree_length):')
        match_lines.append(' ' * 4 + 'if not self.' + input_set_1 + '.has_item(t) and self.' + input_set_2 + '.has_item(t):')
        match_lines.append(' '*8 + 'self.'+ input_set_1 + '.copy(self.empty_set)')
        match_lines.append(' '*8 + 'break')

        match_lines.append(' ' * 4 + 'if self.' + input_set_1 + '.has_item(t) and not self.' + input_set_2 + '.has_item(t):')
        match_lines.append(' '*8 + 'self.'+ input_set_1 + '.copy(self.empty_set)')
        match_lines.append(' '*8 + 'break')

        if not node.negs_above:
            match_lines.append('if self.' + input_set_1 + '.is_empty(): return self.' + input_set_1)
        match_lines.append('#Reporting ' + input_set_1 + ' as output set')
        node_output_dict[node.node_id] = input_set_1


    elif isinstance(node, SetNode_Plus):

        #Get input nodes
        input_set_1 = node_output_dict[node.setnode1.node_id]
        input_set_2 = node_output_dict[node.setnode2.node_id]

        match_lines.append('if not self.' + input_set_1 + '.is_empty() and not self.' + input_set_2 + '.is_empty():')
        match_lines.append(' '*4 + 'self.' + input_set_1 + '.union_update(self.' + input_set_2 + ')')
        match_lines.append('else:')
        match_lines.append(' '*4 + 'self.' + input_set_1 + '.copy(self.empty_set)')

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
        match_lines.append('#Reporting ' + input_array + ' as output set')
        node_output_dict[node.node_id] = input_array

    elif isinstance(node, SetNode_Dep):

        deprels = []
        input_sets = []
        negateds = []
        for deprel, input_set in node.deprels:
            negated = False
            if isinstance(deprel, DeprelNode_Not):
                negated = True
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

        index_node = node_output_dict[node.index_node.node_id]
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
    compulsory = []
    non_compulsory = []

    for key in set_manager.node_needs.keys():
        for ikey in set_manager.node_needs[key]['db_sets_label'].keys():

            if 'no_db' in ikey:
                continue

            db_set = set_manager.node_needs[key]['db_sets_label'][ikey]
            if ikey.startswith('!') and 'no_db' not in ikey:
                compulsory.append(db_set)
                break
            else:
                non_compulsory.append(db_set)
        for ikey in set_manager.node_needs[key]['db_arrays_label'].keys():

            if 'no_db' in ikey:
                continue

            db_set = set_manager.node_needs[key]['db_arrays_label'][ikey][0]
            if ikey.startswith('!') and 'no_db' not in ikey:
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

def write_cython_code(lines, out):

    magic_lines_linux = '''# distutils: language = c++
# distutils: include_dirs = setlib
# distutils: extra_objects = setlib/pytset.so
# distutils: sources = query_functions.cpp
include "search_common.pxi"\n'''

    magic_lines_other = '''# distutils: language = c++
# distutils: include_dirs = setlib
# distutils: sources = query_functions.cpp setlib/pytset.cpp
include "search_common.pxi"\n'''

    if 'linux' in sys.platform:
        out.write(magic_lines_linux)
    else:
        out.write(magic_lines_other)

    for line in lines:
        out.write(line.encode('utf8') + '\n')

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
        nodes = e_parser.parse(expression.decode('utf8'))
        print nodes.to_unicode()

    code_lines = generate_search_code(nodes, tag_list=tag_list, val_dict=val_dict)
    #cdd = code(nodes)
    #lines = cdd.get_search_code()
    filename = str(args.output_file)
    write_cython_code(code_lines, open(filename + '.pyx', 'wt'))


def generate_and_write_search_code_from_expression(expression, f, json_filename=''):

    import sys
    print >> sys.stderr, expression

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

    nodes = e_parser.parse(expression.decode('utf8'))
    #print nodes.to_unicode()
    code_lines = generate_search_code(nodes, tag_list=tag_list, val_dict=val_dict)
    write_cython_code(code_lines, f)

if __name__ == "__main__":
    main()
