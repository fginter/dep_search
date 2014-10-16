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
        self.text = str(self.expression)


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
    what_sets_are_needed = set()
    what_words_are_needed = set()

    for node_id in order_of_execution:

        node = node_id_dict[node_id]
        pseudo_node = pseudo_nodes[node_id]
        if len(node.restrictions) < 1:
            continue

        if False:

            print
            print '#Node ', node_id
            if no_negs_above_dict[node_id]:
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
    for node_id in order_of_execution:

        node = node_id_dict[node_id]
        pseudo_node = pseudo_nodes[node_id]
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

                        if no_negs_above_dict[node_id]:
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

                            if no_negs_above_dict[node_id]:
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
                    pair_block, needed = generate_pairing('f_set',None, op, dtype, False)
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

    the_block = []
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
    With a naive attempt at code generation
    '''

    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    args = parser.parse_args()
    
    e_parser=yacc.yacc()
    for expression in args.expression:
        nodes = e_parser.parse(expression)
        #print nodes.to_unicode()

    process_node(nodes)














main()
