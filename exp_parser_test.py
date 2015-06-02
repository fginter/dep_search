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


    print
    print 'Testing the Matching Engine...'


    m = hashlib.md5()
    fails = []
    success = []

    db_file = '/mnt/ssd/sdata/pb4-ud-100M/trees_00100.db'
    inf = open('unit_test_query.data', 'rt').readlines()

    for i, line in enumerate(inf):

        query, db_file, ln_res, rhash = line.split('\t')
        #L=olla&!Person=3        /mnt/ssd/sdata/pb4-ud-100M/trees_00100.db       72133   hash        
        args = ['python', 'query.py', '-d', db_file, '-m', '0', query]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = p.communicate()
        #assert  err.split('\n')[-2].startswith('Total')
        hit_count = err.split('\n')[-2].split()[-1].strip()
        out = '\n'.join(out.split('\n')[1:])
        m.update(out)

        correct_ln = hit_count == ln_res
        did_something = err.split('\n')[-2].startswith('Total')
        correct_hash = rhash == m.hexdigest()
        if correct_ln and did_something and correct_hash:
            fails.append((query, correct_ln, did_something, correct_hash))
        else:
            success.append(query)
        #print hit_count
        #outf.write('\t'.join([ex[0].encode('utf8'),db_file, hit_count, m.digest()]) + '\n')

    print
    print len(success), '/', len(inf), 'successful!'

    for f in fails:
        print f[0]
        print f[1:]




main()
