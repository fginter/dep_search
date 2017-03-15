from redone_expr import *
import subprocess
import hashlib
import codecs

def main():

    inf = open('unit_test.data','rt')
    data = []
    for l in inf:
        data.append(l.split('\t'))


    print 'Testing the Expression Parser...'
    print
    e_parser=yacc.yacc()
    success = 0
    fail = []
    for i, ex in enumerate(data):
        #print ex[0]
        nodes = e_parser.parse(ex[0].decode('utf8'))
        res = nodes.to_unicode()
        if res == ex[1].strip().decode('utf8'):
            success +=1
        else:
            fail.append((ex[1], res.strip()))

    print success, '/', len(data), 'Tests Passed!'
    print
    print len(fail), 'failed!'
    for f in fail:
        print '-'*10
        print f[0]
        print f[1]
        print '-'*10

main()
