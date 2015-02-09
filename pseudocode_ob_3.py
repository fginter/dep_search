#import lex as lex
#import yacc as yacc
#import re
from expr_tree import *
import sys


#Taskilist:
#1. The order of the nodes(this time there is a possibility of three input nodes for a node!)
#And other stuffs

#2. SetManager
#3. CodeGenerator

class NodeInterpreter():

    def __init__(self, node):
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
        prechar = '!'
        if self.node.negs_above:
            prechar = ''
        if self.node.dep_restriction.split('@')[0] == '<':
            return [prechar + u'gov_a_anyrel']
        if self.node.dep_restriction.split('@')[0] == '>':
            return [prechar + u'dep_a_anyrel']

        if self.node.dep_restriction.startswith('>'):
            return [prechar + u'dep_a_' + self.node.dep_restriction[2:-1].split('@')[0]]
        if self.node.dep_restriction.startswith('<'):
            return [prechar + u'gov_a_' + self.node.dep_restriction[2:-1].split('@')[0]]


    def set_node_token_into_db_label(self):
        #XXX change after format change!
        #Raise Error if faulty query!
        prechar = '!'
        if self.node.negs_above:
            prechar = ''
        if self.node.proplabel == '' and self.node.token_restriction != '_':
            return [prechar + 'token_s_' + self.node.token_restriction[1:-1]]
        if self.node.proplabel == '@CGTAG' and self.node.token_restriction != '_':
            return [prechar + 'tag_s_' + self.node.token_restriction[1:-1]]
        if self.node.proplabel == '@CGBASE' and self.node.token_restriction != '_':
            return [prechar + 'lemma_s_' + self.node.token_restriction[1:-1]]
        if self.node.proplabel != '':
            raise Exception('Faulty Proplabel!', self.node.proplabel, self.node.token_restriction)
        if self.node.token_restriction == '_':
            return []


    def what_output_do_you_need(self):

        if isinstance(self.node, SetNode_Token) or isinstance(self.node, DeprelNode) or isinstance(self.node, SetNode_Dep):        
            return True, 'node_' + self.node.node_id + '_out'
        else:
            return False, None

class SetManager():

    def __init__(self, nodes, node_dict):
        self.node_needs = {}
        #Interrogate the nodes
        for key in node_dict.keys():
            node = node_dict[key]
            self.node_needs[key] = {}
            ni = NodeInterpreter(node)

            #0. Are you compulsory
            #1. What sets do you need from the db?
            self.node_needs[key]['db_sets'], self.node_needs[key]['db_sets_label'] = ni.what_sets_do_you_need()
            self.node_needs[key]['all_tokens'], self.node_needs[key]['all_tokens_label'] = ni.do_you_need_all_tokens()
            #2. What arrays do you need from the db?
            self.node_needs[key]['db_arrays'], self.node_needs[key]['db_arrays_label'] = ni.what_arrays_do_you_need()
            #3. What temporary sets do you need?
            #4. What temporary arrays do you need?
            #5. Do you need an output set, what is your output set called?
            self.node_needs[key]['own_output'], self.node_needs[key]['own_output_set'] = ni.what_output_do_you_need()


def generate_search_code(node):


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
    visualize(node, node_dict)
    #Works

    #Now, the order of execution
    order_of_execution = get_order_of_execution(node, node_dict)
    visualize_order(order_of_execution)

    #Get all the sets this thing needs...
    set_manager = SetManager(node, node_dict)
    #... and visualize!
    visualize_sets(set_manager, node_dict)
    #Seems to work!


    #Now for the code generation itself
    generate_code(node, set_manager, node_dict, order_of_execution)

    import pdb;pdb.set_trace()


def generate_code(nodes, set_manager, node_dict, order_of_execution):

    #Start building the match code, by going through the nodes in the order of ooe
    #A mysterious object will deal with the code_block creation

    #This will be practically for filtering functions
    extra_functions = []
    match_code_lines = []
    node_output_dict = {}

    for node_id in order_of_execution:
        node = node_dict[node_id]
        match_block, extra_functions = generate_code_for_a_node(node, set_manager, node_dict, node_output_dict)


def generate_code_for_a_node(node, set_manager, node_dict, node_output_dict)

    extra_functions = []
    match_lines = []

    match_lines.append('#' + node.node_id)
    match_lines.append('#' + str(type(node)))

    node_ni = Node_Interpreter(node)

    #SetNode_Token
    if isinstance(node, SetNode_Token):
        #I'll find the name of the assigned set
        what_I_need_from_the_db = node_ni.set_node_token_into_db_label()
        if len(what_I_need_from_the_db) < 1:
            #Ah, this is all tokens kind of SetNode_Token
            #I'll just report it as my output
            output_set = set_manager.node_needs[node.node_id]['all_tokens_label'][0]
            match_lines.append('#Reporting ' + output_set + ' as output set')
            node_ouput_dict[node.node_id] = output_set
        else:
            #Get the setname
            db_set = set_manager.node_needs[key]['db_sets_label'][what_I_need_from_the_db[0]]
            output_set_name = 
            match_lines.append('#Reporting ' + output_set + ' as output set')
            node_ouput_dict[node.node_id] = output_set
        #I'll copy it
        #I'll report my output

            






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
            id_the_nodes(kid_node, pid + '_' + str(i), lev + 1, negs, node_dict)
    else:
        #Check if the deprel is negative or not:
        for i, deprel_tuple in enumerate(node.deprels):
            #deprel_tuple[0] = deprel, deprel_tuple[1] = token_set
            if isinstance(deprel_tuple[0], DeprelNode_Not):
                id_the_nodes(deprel_tuple[1], pid + '_' + str(i) + '_0', lev + 1, True, node_dict)
                id_the_nodes(deprel_tuple[0], pid + '_' + str(i) + '_1', lev + 1, True, node_dict)
            else:
                id_the_nodes(deprel_tuple[1], pid + '_' + str(i) + '_0', lev + 1, negs, node_dict)
                id_the_nodes(deprel_tuple[0], pid + '_' + str(i) + '_1', lev + 1, negs, node_dict)

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

    print nodes.to_unicode()

    generate_search_code(nodes)
    #cdd = code(nodes)
    #lines = cdd.get_search_code()
    #filename = str(args.output_file)
    #write_cython_code(lines, filename + '.pyx')

if __name__ == "__main__":
    main()
