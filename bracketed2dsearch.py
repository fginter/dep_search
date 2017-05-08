import six
assert six.PY3, "Please run me with Python3"

import ply.lex as lex
import ply.yacc as yacc
import readline
import urllib.parse
import requests
import sys

class Node:

    def __init__(self,dtype,children):
        self.dtype=dtype
        self.children=children

    def dsearch_ex_lin(self):
        #cases like [dep xxx xxx xxx xxx]
        assert sum(1 for c in self.children if isinstance(c,str))==len(self.children)
        exprs=[]
        for root_idx,root in enumerate(self.children):
            expr=['"'+root+'"']
            for other_idx,other in enumerate(self.children):
                if other_idx<root_idx:
                    expr.append('>lin@L "{}"'.format(other))
                elif other_idx>root_idx:
                    expr.append('>lin@R "{}"'.format(other))
            exprs.append("("+(" ".join(expr))+")")
        return "("+(" | ".join(exprs))+")"
                
    def dsearch_ex(self):
        global macros
        #Now I guess I pick one of my STRING children to be the root or what?
        possible_roots=[c for c in self.children if isinstance(c,str)]
        if len(possible_roots)==len(self.children) and len(self.children)>1:
            return self.dsearch_ex_lin()
        elif len(possible_roots)>1:
            raise ValueError("Unsupported")
        assert len(possible_roots)==1
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
                    bits.append(c.dsearch_ex())
                else:
                    assert False, repr(c)
            bits.append(")")
            return " ".join(bits)#I guess I should then generate the others too?

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

def download(qry,maxnum,fname):
    data={"search":qry,"db":"RU160M","case":"False","retmax":maxnum}
    result=requests.get("http://epsilon-it.utu.fi/dep_search_webapi",params=data)
    print(result.url)
    with open(fname,"w") as f:
        print(result.text,file=f)
        

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
NP-Dat : (NOUN&Dat)
XP : (NOUN|ADJ|ADV|PRON|VERB)
PRON-Dat : (PRON&Dat)
NOUN-Nom : (NOUN&Nom)
VP : VERB
AP : ADJ
VP-Inf : (VERB&Inf)
VP-Imper : (VERB&Mood=Imp)
V-Past : (VERB&Past)
Imper : (Mood=Imp)
Cl : (VERB >nsubj _)
_ : _
"""

macros={} #macro -> replacement
for repl in macros_def.strip().split("\n"):
    src,trg=repl.split(" : ",1)
    macros[src]=trg


expressions={} #filename -> list of expressions
for line in sys.stdin:
    line=line.strip()
    if not line:
        continue
    if line.startswith("["):
        #an expression
        expression_list.append(line)
    else: #construction name
        line=line.replace(" ","_")
        expression_list=[]
        expressions[line]=expression_list

for fname,expression_list in sorted(expressions.items()):
    for expression in expression_list:
        print("Parsing expression", expression, file=sys.stderr, flush=True)
        node = parser.parse(expression)
        qry=node[0].dsearch_ex()
        print(qry)
        download(qry,5,"dl/"+fname+".conllu")
        
   
   
   
