import re

import lex as lex
import yacc as yacc



class ExpressionError(ValueError):

    pass


# one node (token, possibly restricted somehow)
class Node(object): 

    def __init__(self):
        self.restrictions=[] #Right now, just a list of dependency restrictions

    def add_dep_res(self,res):
        self.restrictions.append(res)

    def add_tok_res(self,res): #Adds a restriction on the token
        self.restrictions.append(res) #just a list for now, it will need to change of course

    def to_unicode(self):
        return u"Node(%s)"%(u",".join(r.to_unicode() if not isinstance(r,tuple) else u"=".join(c for c in r) for r in self.restrictions))

# one dependency restriction
class DepRes(object):
    
    def __init__(self,operator,node):
        self.negated=False #Has this restriction been negated?
        self.operator=operator #I guess we'll need to do more than just remember these :D
        self.node=node
        self.restrictions=[]


    def to_unicode(self):
        if self.negated:
            neg=u"!"
        else:
            neg=u""
        return neg+self.operator+u"  "+self.node.to_unicode()


#########################
### The expression parser bit starts here

#Lexer - tokens

tokens=('REGEX',    #/..../
        'PROPLABEL', #@...
        'DEPOP',     #</nsubj/
        'LPAR',      #(
        'RPAR',      #)
        'NEG',       #!
        'ANYTOKEN')  #_

#Here's regular expressions for the tokens defined above

t_REGEX=ur"/[^/]+/"
t_PROPLABEL=ur"@[A-Z]+"
t_DEPOP=ur"(<|>)(/[^/]+/)?"
t_LPAR=ur"\("
t_RPAR=ur"\)"
t_NEG=ur"!"
t_ANYTOKEN=ur"_"

t_ignore=u" \t"

def t_error(t):
    raise ExpressionError(u"Unexpected character '%s'\nHERE: '%s'..."%(t.value[0],t.value[:5]))


#......and here's where starts the CFG describing the expressions
# the grammar rules are the comment strings of the functions

#Main 
precedence = ( ('left','DEPOP'), )

def p_error(t):
    if t==None:
        raise ExpressionError(u"Syntax error at the end of the expression. Perhaps you forgot to specify a target token? Forgot to close parentheses?")
    else:
        raise ExpressionError(u"Syntax error at the token '%s'\nHERE: '%s'..."%(t.value,t.lexer.lexdata[t.lexpos:t.lexpos+5]))

#TOP  search -> expression
def p_top(t):
    u'''search : expr'''
    t[0]=t[1]   #t[0] is the result (left-hand side) and t[1] is the result of "expr"

# expression can be:

#  ( expression )
#  _
def p_exprp(t):
    u'''expr : LPAR expr RPAR
              | ANYTOKEN'''
    if len(t)==4: #the upper rule
        t[0]=t[2] #...just return the embedded expression
    elif len(t)==2:
        t[0]=Node() #hmm... - shouldn't I somehow fill this node?

# /token/
def p_exprp2(t):
    u'''expr : tokendef'''
    t[0]=t[1]  #if tokendef returns a Node(), this will also return a Node()


# expression dependency_restriction
# expression ! dependency_restriction
def p_expr2(t):
    u'''expr : expr depres
             | expr NEG depres'''
    t[0]=t[1] #The return value is the right-hand expression, but we add a restriction to it
    if len(t)==3: #upper rule
        t[0].add_dep_res(t[2]) #not negated
    elif len(t)==4: #lower rule
        t[3].negated=True 
        t[0].add_dep_res(t[3]) #negated

# dependency restriction is
# dep operator (>< etc) followed by another expression
def p_depres(t):
    u'''depres : DEPOP expr'''
    t[0]=DepRes(t[1],t[2]) #Make a restriction out of the operator and the right-hand expression


# token is ... we'll have to redo this, the current one assumes a horrible syntax

# one or more props, where a prop is ...err... a random name for a nonterminal. :)
def p_tokendef(t):
    u'''tokendef : prop
                 | prop tokendef'''
    if len(t)==2: #upper rule
        t[0]=Node()
        t[0].add_tok_res(t[1]) #aha, so this adds a restriction on the NODE (lemma, pos, etc)
    elif len(t)==3: #lowe rule
        t[0]=t[2] #tokendef already returns a node, to which we just add restrictions, let's redo this stuff
        t[0].add_tok_res(t[1])

# ...where a prop is a regular expression, or a labeled regular expression
#...christ, whatever this even was?!
def p_prop(t):
    u'''prop : REGEX
             | PROPLABEL REGEX'''
    if len(t)==2:
        t[0]=(u"TXT",unicode(t[1][1:-1].decode('utf-8'))) #strip the /../
    elif len(t)==3:
        t[0]=(unicode(t[1][1:].decode('utf-8')),unicode(t[2][1:-1].decode('utf-8'))) #strip the /../


lex.lex(reflags=re.UNICODE)
yacc.yacc(write_tables=0)

 
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    args = parser.parse_args()
    
    e_parser=yacc.yacc()
    for expression in args.expression:

        import logging
        logging.basicConfig(filename='myapp.log', level=logging.INFO)
        log = logging.getLogger()


        print e_parser.parse(expression, debug=log).to_unicode()
    
