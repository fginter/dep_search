import six
assert six.PY3, "Please run me with Python3"

import ply.lex as lex
import ply.yacc as yacc
import readline
import urllib.parse

class Node:

    def __init__(self,dtype,children):
        self.dtype=dtype
        self.children=children

    def dsearch_ex(self):
        global macros
        #Now I guess I pick one of my STRING children to be the root or what?
        possible_roots=[c for c in self.children if isinstance(c,str)]
        assert possible_roots
        for r in possible_roots:
            bits=["(",macros.get(r,'"'+r+'"')] #Bits of the expression
            for c in self.children:
                if c==r:
                    continue
                if isinstance(c,str):
                    bits.extend(['>',macros.get(c,'"'+c+'"')])
                elif isinstance(c,Node):
                    if c.dtype=="dep" or c.dtype=="_":
                        bits.append(' > ')
                    else:
                        bits.append(' >'+c.dtype)
                    bits.extend(c.dsearch_ex())
                else:
                    assert False, repr(c)
            bits.append(")")
            return bits#I guess I should then generate the others too?

### ---------- lexer -------------

# List of token names.   This is always required
tokens = ('LBRAC','RBRAC','STRING')

def t_LBRAC(t):
    r'\['
    return t

def t_RBRAC(t):
    r'\]'
    return t

def t_STRING(t):
    r'[^\s\[\]]+'
    return t

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()

###  --------- grammar -----------

def p_expressions(p):
    '''expressions : expression
                   | expression expressions
    '''
    if len(p)==2:
        p[0]=[p[1]]
    elif len(p)==3:
        p[0]=[p[1]]+p[2]
    else:
        assert False

def p_expr(p):
    '''expression : tree
                  | STRING
    '''
    p[0]=p[1]

def p_tree(p):
    'tree : LBRAC STRING expressions RBRAC'
    p[0]=Node(p[2],p[3])

def p_error(p):
    print("Syntax error in input!")

parser = yacc.yacc()

def get_query_url(q):
    url="http://bionlp-www.utu.fi/dep_search/query"
    url+="?"+urllib.parse.urlencode({"search":q,"db":"RU160M","case_sensitive":"False","hits_per_page":"50"})
    return url

### ---------- run this ------------

# * NP-Nom = NOUN Case=Nom
# * XP = any phrasal category = NOUN, ADJ, ADV, PRON, VERB
# * PRON-Dat = PRON Case=Dat
# * NOUN-Nom = NOUN Case=Nom
# * VP = VERB
# * AP = ADJ
# * VP-Inf = VERB VerbForm=Inf
# * Imper = Mood=Imp
# * dep = any dependency label

macros_def="""
NP-Nom : (NOUN&Nom)
XP : (NOUN|ADJ|ADV|PRON|VERB)
PRON-Dat : (PRON&Dat)
NOUN-Nom : (NOUN&Nom)
VP : VERB
AP : ADJ
VP-Inf : (VERB&Inf)
Imper : (Mood=Imp)
_ : _
"""

macros={} #macro -> replacement
for repl in macros_def.strip().split("\n"):
    src,trg=repl.split(" : ",1)
    macros[src]=trg

# [root [nmod [case без] [nummod пяти] минут] NP-Nom]
    
while True:
   try:
       s = input('test > ')
   except EOFError:
       break
   if not s:
       continue
   node = parser.parse(s)
   qry=" ".join(node[0].dsearch_ex())
   print(qry)
   print(get_query_url(qry))
   
   
   
