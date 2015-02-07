import re

import lex as lex
import yacc as yacc



class ExpressionError(ValueError):

    pass

class SetNode_Token(object):
    #Makes a single operation, and returns a single set
    def __init__(self, token_restriction):
        self.node_id = ''
        self.token_restriction = token_restriction
        self.proplabel = ''
    def to_unicode(self):
        return u'SetNode(Token:' + self.proplabel + self.token_restriction + u')' 


class SetNode_And(object):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' AND ' + self.setnode2.to_unicode() + ')'

class SetNode_Or(object):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' OR ' + self.setnode2.to_unicode() + ')'

class SetNode_Dep(object):

    def __init__(self, setnode1, setnode2, deprel):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.deprel = deprel
        self.proplabel = ''

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' - ' + self.deprel.to_unicode() +' - '+ self.setnode2.to_unicode() + ')'

class SetNode_Not(object):

    def __init__(self, setnode1):
        self.node_id = ''
        self.setnode1 = setnode1
    def to_unicode(self):
        return u'Node(NOT ' + self.setnode1.to_unicode() +')'

class DeprelNode(object):
    #Makes a single operation, and returns a single set
    def __init__(self, dep_restriction):
        self.node_id = ''
        self.dep_restriction = dep_restriction
    def to_unicode(self):
        return u'DeprelNode(' + self.dep_restriction + u')'

class DeprelNode_And(object):

    def __init__(self, dnode1, dnode2):
        self.node_id = ''
        self.dnode1 = dnode1
        self.dnode2 = dnode2
    def to_unicode(self):
        return u'DeprelNode(' + self.dnode1.to_unicode() + ' AND ' + self.dnode2.to_unicode() + ')'

class DeprelNode_Or(object):

    def __init__(self, dnode1, dnode2):
        self.node_id = ''
        self.dnode1 = dnode1
        self.dnode2 = dnode2
    def to_unicode(self):
        return u'DeprelNode(' + self.dnode1.to_unicode() + ' OR ' + self.dnode2.to_unicode() + ')'


class DeprelNode_Not(object):

    def __init__(self, dnode1):
        self.node_id = '' 
        self.dnode1 = dnode1
    def to_unicode(self):
        return u'DeprelNode(NOT ' + self.dnode1.to_unicode() +')'

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


#one token restriction
class TokenRes(object):

    def __init__(self,content):
        self.negated=False #Has this restriction been negated?
        self.content=content 
        self.restrictions=[]

    def to_unicode(self):
        if self.negated:
            neg=u"!"
        else:
            neg=u""
        return u'TokenRes:' + neg+self.content+u"  "+str(self.restrictions)




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
        'AND',       #&
        'OR',        #|
        'ANYTOKEN')  #_

#Here's regular expressions for the tokens defined above

t_REGEX=ur"/[^/]+/"
t_PROPLABEL=ur"@[A-Z]+"
t_DEPOP=ur"(<|>)(/[^/]+/)?"
t_LPAR=ur"\("
t_RPAR=ur"\)"
t_NEG=ur"\!"
t_AND=ur"\&"
t_OR=ur"\|"
t_ANYTOKEN=ur"_"

t_ignore=u" \t"

def t_error(t):
    raise ExpressionError(u"Unexpected character '%s'\nHERE: '%s'..."%(t.value[0],t.value[:5]))


#......and here's where starts the CFG describing the expressions
# the grammar rules are the comment strings of the functions

#Main 
precedence = ( ('left','DEPOP'),('left','OR'),('left','AND'))

def p_error(t):
    if t==None:
        raise ExpressionError(u"Syntax error at the end of the expression. Perhaps you forgot to specify a target token? Forgot to close parentheses?")
    else:
        raise ExpressionError(u"Syntax error at the token '%s'\nHERE: '%s'..."%(t.value,t.lexer.lexdata[t.lexpos:t.lexpos+5]))

#TOP  search -> expression
def p_top(t):
    u'''search : setnode'''
    t[0]=t[1]   #t[0] is the result (left-hand side) and t[1] is the result of "expr"

# expression can be:

#  ( expression )
#  _
def p_exprp(t):
    u'''setnode : LPAR setnode RPAR
              | ANYTOKEN'''
    if len(t)==4: #the upper rule
        t[0]=t[2] #...just return the embedded expression
    elif len(t)==2:
        t[0]=SetNode_Token(t[1]) #hmm... - shouldn't I somehow fill this node?

def p_exprpd(t):
    u'''depnode : LPAR depnode RPAR
              | DEPOP'''
    if len(t)==4: #the upper rule
        t[0]=t[2] #...just return the embedded expression
    elif len(t)==2:
        t[0]=DeprelNode(t[1]) #hmm... - shouldn't I somehow fill this node?

def p_dn_and(t):
    u'''depnode : depnode AND depnode'''
    t[0] = DeprelNode_And(t[1], t[3])

def p_sn_and(t):
    u'''setnode : setnode AND setnode'''
    t[0] = SetNode_And(t[1], t[3])

def p_dn_or(t):
    u'''depnode : depnode OR depnode'''
    t[0] = DeprelNode_Or(t[1], t[3])

def p_sn_or(t):
    u'''setnode : setnode OR setnode'''
    t[0] = SetNode_Or(t[1], t[3])

def p_dn_not(t):
    u'''depnode : NEG depnode'''
    t[0] = DeprelNode_Not(t[2])
def p_sn_not(t):
    u'''setnode : NEG setnode'''
    t[0] = SetNode_Not(t[2])

def p_sn_depres(t):
    u'''setnode : setnode depnode setnode'''
    t[0] = SetNode_Dep(t[1], t[3], t[2])

def p_n_sn(t):
    u'''setnode : REGEX
                | PROPLABEL REGEX'''
    if len(t) == 2:
        t[0] = SetNode_Token(t[1])
    elif len(t) == 3:
        t[0] = SetNode_Token(t[2])
        t[0].proplabel = t[1]


lex.lex(reflags=re.UNICODE)
yacc.yacc(write_tables=0)

 
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    args = parser.parse_args()
    
    e_parser=yacc.yacc()
    for expression in args.expression:
        print e_parser.parse(expression).to_unicode()
    
