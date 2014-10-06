from query import Query
#import lex as lex
#import yacc as yacc
#import re
from expr import *
import sys

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


def process_node(node):

    orig_node = node
    #Give each node an id
    #And get appropriate dicts for these nodes
    node_id_dict, node_depth_dict, no_negs_above_dict = get_depth_and_id_dicts(node)
    #Make a reverse id dict
    reverse_node_id_dict = {v: k for k, v in node_id_dict.items()}

    #print '#', node_id_dict
    #print '#', node_depth_dict

    #Sort nodes into order
    order_of_execution = []
    levels = node_depth_dict.keys()
    levels.sort()
    levels.reverse()
    for level in levels:
        nodes_which_break_on_empty = []
        nodes_which_dont_break_on_empty = []        
        for node_id in node_depth_dict[level]:
            if no_negs_above_dict[node_id]:
                nodes_which_break_on_empty.append(node_id)
            else:
                nodes_which_dont_break_on_empty.append(node_id)
        order_of_execution.extend(nodes_which_break_on_empty)
        order_of_execution.extend(nodes_which_dont_break_on_empty)

    #Make pseudo objects
    pseudo_nodes = {}
    for node_id, node in node_id_dict.items():
        
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
                input_node_id = reverse_node_id_dict[input_node]
            else:
                input_node_id = None
            pseudo_depres_list.append(PseudoDepres(depres, input_node_id))
        pseudo_node = PseudoNode(node, pseudo_depres_list, node_depres, node_txt_restrictions, node_id)
        pseudo_nodes[node_id] = pseudo_node

    print orig_node.to_unicode()
    for node_id in order_of_execution:
        node = node_id_dict[node_id]
        pseudo_node = pseudo_nodes[node_id]
        if len(node.restrictions) < 1:
            continue
        print
        print '#Node ', node_id
        if no_negs_above_dict[node_id]:
            print '#Break execution if this node returns set()'
        else:
            print '#Do Not break execution if this node returns set()'
        #print 
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


    
def get_depth_and_id_dicts(node):

    node_id_dict, node_depth_dict, no_negs_above_dict = id_the_tree(node, '0', 0, True)

    proper_depth_dict = {}
    #print 'ndk', node_depth_dict.keys()
    for key in node_depth_dict.keys():
        value = node_depth_dict[key]
        #print 'vk', value, key
        if value not in proper_depth_dict.keys():
            proper_depth_dict[value] = []
        proper_depth_dict[value].append(key)

    return node_id_dict, proper_depth_dict, no_negs_above_dict

def id_the_tree(node, id, depth, no_negs_above):

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
        res_id_dict, res_depth_dict, res_no_negs_above_dict = id_the_tree(kid_node, id + '_' + str(i), depth+1, neg)
        node_id_dict.update(res_id_dict)   
        node_depth_dict.update(res_depth_dict)  
        no_negs_above_dict.update(res_no_negs_above_dict)

    return node_id_dict, node_depth_dict, no_negs_above_dict

def main():

    '''
    Exploring the node tree, trying to figure very naive order of execution.
    '''

    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    args = parser.parse_args()
    
    e_parser=yacc.yacc()
    for expression in args.expression:
        nodes = e_parser.parse(expression)
        print nodes.to_unicode()

    process_node(nodes)














main()
