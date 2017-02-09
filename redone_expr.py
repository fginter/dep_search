# -*- coding: utf-8 -*-
import re
import logging
import lex as lex
import yacc as yacc


class ExpressionError(ValueError):

    pass


class BaseNode():
    node_id = ''
    level = 0
    negs_above = False
    neg = False
    deprel = False
    parent_node = None
    extra_comments = []
    #def __init__(self):
    #    self.extra_comments = []


class SetNode_Token(BaseNode):
    #Makes a single operation, and returns a single set
    def __init__(self, token_restriction):
        self.node_id = ''
        self.extra_comments = []
        self.token_restriction = token_restriction.rstrip('"').lstrip('"')
        if self.token_restriction.startswith('L=') and not token_restriction.startswith('"'):
            self.token_restriction = self.token_restriction[2:]
            self.proplabel = '@CGBASE'
        else:
            self.proplabel = ''

    def set_proplabel(self, label):
        if self.proplabel == '':
            self.proplabel = label

    def get_kid_nodes(self):
        return []

    def to_unicode(self):
        return u'SetNode(Token:' + self.proplabel + self.token_restriction + u')' + str(self.extra_comments) 


class SetNode_Eq(BaseNode):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''
        self.extra_comments = []

    def get_kid_nodes(self):
        return [self.setnode1, self.setnode2]

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' == ' + self.setnode2.to_unicode() + ')'



class SetNode_SubEq(BaseNode):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''
        self.extra_comments = []

    def get_kid_nodes(self):
        return [self.setnode1, self.setnode2]

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' -> ' + self.setnode2.to_unicode() + ')'


class SetNode_And(BaseNode):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''
        self.extra_comments = []

    def get_kid_nodes(self):
        return [self.setnode1, self.setnode2]

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' AND ' + self.setnode2.to_unicode() + ')'

class SetNode_Plus(BaseNode):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''
        self.extra_comments = []


    def get_kid_nodes(self):
        return [self.setnode1, self.setnode2]

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' PLUS ' + self.setnode2.to_unicode() + ')'


class SetNode_Or(BaseNode):

    def __init__(self, setnode1, setnode2):
        self.node_id = ''
        self.setnode1 = setnode1
        self.setnode2 = setnode2
        self.proplabel = ''
        self.extra_comments = []

    def get_kid_nodes(self):
        return [self.setnode1, self.setnode2]

    def to_unicode(self):
        return u'Node(' + self.setnode1.to_unicode() + ' OR ' + self.setnode2.to_unicode() + ')'

class SetNode_Dep(BaseNode):

    def __init__(self, setnode1, setnode2, deprel):
        self.node_id = ''
        self.index_node = setnode1
        self.deprels = [(deprel, setnode2)]
        self.proplabel = ''
        self.extra_comments = []

    def get_kid_nodes(self):
        to_return = [self.index_node,]
        for dr_tuple in self.deprels:
            to_return.append(dr_tuple[0])
            to_return.append(dr_tuple[1])
        return to_return

    def to_unicode(self):

        deprel_list = []
        for drt in self.deprels:
            deprel_list.append(drt[0].to_unicode() + ':' + drt[1].to_unicode())        

        return u'Node(index_node:' + self.index_node.to_unicode() + ' << ' + ','.join(deprel_list) +' >> )' + str(self.extra_comments)

class SetNode_Not(BaseNode):

    def __init__(self, setnode1):
        self.node_id = ''
        self.setnode1 = setnode1
        self.neg = True
        self.extra_comments = []

    def get_kid_nodes(self):
        return [self.setnode1,]

    def to_unicode(self):
        return u'Node(NOT ' + self.setnode1.to_unicode() +')'

class DeprelNode(BaseNode):
    #Makes a single operation, and returns a single set
    def __init__(self, dep_restriction):
        self.node_id = ''
        self.dep_restriction = dep_restriction
        self.deprel = True

    def get_kid_nodes(self):
        return []

    def to_unicode(self):
        return u'DeprelNode(' + self.dep_restriction + u')'

class DeprelNode_And(BaseNode):

    def __init__(self, dnode1, dnode2):
        self.node_id = ''
        self.dnode1 = dnode1
        self.dnode2 = dnode2
        self.deprel = True

    def get_kid_nodes(self):
        return [self.dnode1, self.dnode2]

    def to_unicode(self):
        return u'DeprelNode(' + self.dnode1.to_unicode() + ' AND ' + self.dnode2.to_unicode() + ')'

class DeprelNode_Or(BaseNode):

    def __init__(self, dnode1, dnode2):
        self.node_id = ''
        self.dnode1 = dnode1
        self.dnode2 = dnode2
        self.deprel = True

    def get_kid_nodes(self):
        return [self.dnode1, self.dnode2]

    def to_unicode(self):
        return u'DeprelNode(' + self.dnode1.to_unicode() + ' OR ' + self.dnode2.to_unicode() + ')'


class DeprelNode_Not(BaseNode):

    def __init__(self, dnode1):
        self.node_id = '' 
        self.dnode1 = dnode1
        self.neg = True
        self.deprel = True

    def get_kid_nodes(self):
        return [self.dnode1]

    def to_unicode(self):
        return u'DeprelNode(NOT ' + self.dnode1.to_unicode() +')'


#########################
### The expression parser bit starts here

#Lexer - tokens

tokens=('TEXT',    #/..../
        'WORD', #@...
        'DEPOP',     #</nsubj/
        'LPAR',      #(
        'RPAR',      #)
        'NEG',       #!
        'AND',       #&
        'OR',        #|
        'PLUS',
        'EQ',
        'SE',
        'ANYTOKEN',
        'ECOM',
        'XDOT',
        'BGN',
        'END')  #_

#Here's regular expressions for the tokens defined above
t_TEXT = ur'((?!(->|\+|&|\(|\)|\||==|<|>|"|\s)).)+'
t_DEPOP = ur'(<|>)([^="<>()&|\s]+)?'

def t_ECOM(t):
    ur'{[^}]+}'
    return t

def t_WORD(t):
    ur'"[^"]+"'
    return t

def t_LPAR(t):
    ur"\("
    return t

def t_RPAR(t):
     ur"\)"
     return t

def t_NEG(t):
    ur"\!"
    return t

def t_AND(t):
    ur"\&"
    return t

def t_OR(t):
    ur"\|"
    return t

def t_EQ(t):
    ur"=="
    return t

def t_SE(t):
    ur"->"
    return t

def t_PLUS(t):
    ur"\+"
    return t

def t_XDOT(t):
    ur"[.]{1}"
    return t

def t_BGN(t):
    ur"\^"
    return t

def t_END(t):
    ur"\$"
    return t


def t_ANYTOKEN(t):
     ur"_"
     return t
t_ignore=u" \t"

def t_error(t):


    raise ExpressionError(u"%s:::Unexpected character '%s'\nHERE: '%s'..."%(t, t.value[0],t.value[:5]))


#......and here's where starts the CFG describing the expressions
# the grammar rules are the comment strings of the functions

#Main 
precedence = (('left','PLUS'),('left','EQ'),('left','SE'),('left','DEPOP'),('left','OR'),('left','AND'),('left','NEG'), ('left', 'ECOM'), ('left','TEXT'), ('right', 'XDOT'), ('left', 'BGN'), ('left', 'END'))

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

def p_bgn(t):
    u'''setnode : BGN setnode'''
    t[0] = SetNode_Dep(t[2], SetNode_Token('_'), DeprelNode_Not(DeprelNode('<lin@L')))


def p_end(t):
    u'''setnode : setnode END'''
    t[0] = SetNode_Dep(t[1], SetNode_Token('_'), DeprelNode_Not(DeprelNode('<lin@R')))

def p_dot(t):
    u'''setnode : tokendef XDOT setnode'''
    t[0] = SetNode_Dep(t[1], t[3], DeprelNode('<lin@R'))

def p_ecomxpr(t):
    u'''setnode : setnode ECOM'''
    t[1].extra_comments.append(t[2][1:-1])
    t[0] = t[1]

def p_expr2(t):
    u'''setnode : setnode depres'''
    if isinstance(t[1], SetNode_Dep):
        t[1].deprels.append(t[2])
        t[0] = t[1]
    else:
        t[0] = SetNode_Dep(t[1], t[2][1], t[2][0])

def p_sn_depres_a(t):
    u'''depres : depnode tokendef'''
    t[0] = (t[1], t[2])

def p_exprp(t):
    u'''tokendef : LPAR setnode RPAR'''
    #          | ANYTOKEN'''
    if len(t)==4: #the upper rule
        t[0]=t[2] #...just return the embedded expression
    #elif len(t)==2:
    #    t[0]=SetNode_Token(t[1])


def p_exprp_d(t):
    u'''depdef : LPAR depnode RPAR
              | DEPOP'''
    if len(t)==4: #the upper rule
        t[0]=t[2] #...just return the embedded expression
    elif len(t)==2:
        t[0]=DeprelNode(t[1])

def p_exprp2(t):
    u'''setnode : tokendef'''
    #if isinstance(BaseNode):
    t[0]=t[1]  #if tokendef returns a Node(), this will also return a Node()
    #else:
    #    p_exprp3(t)    

def p_exprp5(t):
    u'''depnode : depdef'''
    t[0]=t[1]  #if tokendef returns a Node(), this will also return a Node()

def p_exprp3(t):
    u'''tokendef : WORD
                | TEXT
                | ANYTOKEN'''
    if len(t) == 2:
       if t[1].startswith('"') and t[1].endswith('"'):
           t[0] = SetNode_Token(t[1])
       elif t[1]=='_':
           t[0]=SetNode_Token(t[1])
       else:
           t[0] = SetNode_Token(t[1])
           t[0].set_proplabel('@CGTAG')


def p_dn_and(t):
    u'''depnode : depnode AND depnode'''
    if not isinstance(t[1], DeprelNode_Not) and not isinstance(t[3], DeprelNode_Not):
        t[0] = DeprelNode_And(t[1], t[3])
    else:
        raise ExpressionError(u"Negated depency restrictions are not allowed inside AND operators, maybe try to include negation outside the AND operator.")

def p_sn_and(t):
    u'''tokendef : tokendef AND tokendef'''
    t[0] = SetNode_And(t[1], t[3])

def p_sn_or(t):
    u'''tokendef : tokendef OR tokendef'''
    t[0] = SetNode_Or(t[1], t[3])

def p_sn_plus(t):
    u'''setnode : setnode PLUS setnode'''
    t[0] = SetNode_Plus(t[1], t[3])

def p_sn_eq(t):
    u'''setnode : setnode EQ setnode'''
    t[0] = SetNode_Eq(t[1], t[3])

def p_sn_seq(t):
    u'''setnode : setnode SE setnode'''
    t[0] = SetNode_SubEq(t[1], t[3])

def p_dn_or(t):
    u'''depnode : depnode OR depnode'''
    if not isinstance(t[1], DeprelNode_Not) and not isinstance(t[3], DeprelNode_Not):
        t[0] = DeprelNode_Or(t[1], t[3])
    else:
        raise ExpressionError(u"Negated depency restrictions are not allowed inside OR operators, maybe try to include negation outside the OR operator.")
 
def p_dn_not(t):
    u'''depdef : NEG depdef'''
    t[0] = DeprelNode_Not(t[2])

def p_sn_not(t):
    u'''tokendef : NEG tokendef'''
    t[0] = SetNode_Not(t[2])

lex.lex(reflags=re.UNICODE)
yacc.yacc(write_tables=0,debug=1,method='SLR')

 
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Expression parser')
    parser.add_argument('expression', nargs='+', help='Training file name, or nothing for training on stdin')
    args = parser.parse_args()
    e_parser=yacc.yacc(write_tables=0,debug=1,method='LALR')
    for expression in args.expression:

        import logging
        logging.basicConfig(filename='myapp.log', level=logging.INFO)
        log = logging.getLogger()
        ebin = e_parser.parse(expression.decode('utf8'), debug=0)
        print ebin.to_unicode()
