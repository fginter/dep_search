import sys
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree

import re
import lex as lex
import yacc as yacc

from expr import *

def query(conn,expr):
    BATCH=1000
    q=u"SELECT sentence.* from sentence"
    rset=conn.execute(q)
    while True:
        rows=rset.fetchmany(BATCH)
        if not rows:
            break
        for _,sent_pickle in rows:
            tree=pickle.loads(str(sent_pickle))
            if exec_search_2(tree,expr):
                yield tree


def exec_search(tree,expr):
    s=None
    for rest in expr.restrictions:
        if not rest.node.restrictions:
            import pdb; pdb.set_trace()
            if u">" in rest.operator:
                dtype=rest.operator[2:-1]
                if dtype not in tree.d_govs: return False
                if s is None:
                    s=tree.d_govs[dtype]
                else:
                    s&=tree.d_govs[dtype]
                    if not s: return False
            else:
                raise ValueError("I can't handle this!")
        else:
            raise ValueError("I can't handle this!")
    if s:
        return True
    else: return False


def exec_search_2(tree,expr):
    s=None
    for rest in expr.restrictions:
        if not rest.node.restrictions:
            if u">" in rest.operator:
                dtype=rest.operator[2:-1]
                #To support negation
                if not rest.negated and dtype not in tree.d_govs: return False
                if s is None:
                    if not rest.negated:
                        s=tree.d_govs[dtype]
                    else:
                        #What a terrible way to go!
                        all_tokens = set(range(1, len(tree.tokens)))
                        try:
                            s=all_tokens - tree.d_govs[dtype]
                        except KeyError:
                            s=all_tokens
                        #import pdb;pdb.set_trace()
                else:
                    if not rest.negated:
                        s&=tree.d_govs[dtype]
                    else:
                        all_tokens = set(range(1, len(tree.tokens)))
                        try:
                            s&=all_tokens - tree.d_govs[dtype]
                        except KeyError:
                            s&=all_tokens
                    if not s: return False
            else:
                raise ValueError("I can't handle this!")
        else:
            raise ValueError("I can't handle this!")
    if s:
        return True
    else: return False




if __name__==u"__main__":

    e_parser=yacc.yacc()
    expression=u"_ !>/nsubj/ _ >/dobj/ _ >/cop/ _ "

    node=e_parser.parse(expression)
    print "search tree:",node.to_unicode()

    conn=sqlite3.connect("/mnt/ssd/sdata/sdata2.db")
    out=codecs.getwriter("utf-8")(sys.stdout)

    for t in query(conn,node):
        t.to_conll(out)
        





