#!/usr/bin/env python

import time
import sys
import os

THISDIR=os.path.dirname(os.path.abspath(__file__))
os.chdir(THISDIR)

import subprocess
import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
from tree import Tree
import re
import zlib
import importlib
import argparse
import db_util
import glob
import tempfile
import sys
from collections import defaultdict

field_re=re.compile(ur"^(!?)(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
query_folder = './queries/'

#XXX: Very very temporary hack!
extras_dict = {}

def map_set_id(args, db, qobj):

    #XXX: figure out a way to check if this and that is in the db. 

    just_all_set_ids = []
    optional = []
    types = []

    c_args_s = []
    s_args_s = []
    c_args_m = []
    s_args_m = []

    solr_args = []

    or_groups = defaultdict(list)

    for arg in args:
        compulsory = False
        it_is_set = True
        or_group_id = None

        if arg.startswith('!'):
            compulsory = True    
            narg = arg[1:]
        else:
            narg = arg

        if narg.startswith('org_'):
            or_group_id = int(narg.split('_')[1])
            narg = narg[6:]

        #print >> sys.stderr, "narg:", narg
        optional.append(not compulsory)

        oarg = 0

        if narg.startswith('dep_a'):
            if db.has_id(u'd_' + narg[6:]):
                oarg = db.get_id_for(u'd_' + narg[6:])
            it_is_set = False

        if narg.startswith('gov_a'):
            if db.has_id(u'g_' + narg[6:]):
                oarg = db.get_id_for(u'g_' + narg[6:])
            it_is_set = False

        if narg.startswith('lemma_s'):
            if db.has_id(u'l_' + narg[8:]):
                oarg = db.get_id_for(u'l_' + narg[8:])
            it_is_set = True
        if narg.startswith('token_s'):
            if db.has_id(u'f_' + narg[8:]):
                oarg = db.get_id_for(u'f_' + narg[8:])
            it_is_set = True

        #Here! Add so that if not found as tag, try tokens
        if narg.startswith('tag_s'):
            it_is_set = True
            if db.has_id(u'' + narg[6:]):
            #if narg[6:] in set_dict.keys():
                oarg = db.get_id_for(u'' + narg[6:])
                solr_args.append(arg)
                if or_group_id != None:
                    or_groups[or_group_id].append(arg[6:])
            else:
                if db.has_id(u'p_' + narg[6:]):
                #if 'p_' + narg[6:] in set_dict.keys():
                    oarg = db.get_id_for(u'p_' + narg[6:])
                    solr_args.append(arg)
                    if or_group_id != None:
                        or_groups[or_group_id].append(arg[6:])

                else:
                    try:
                        if compulsory:
                            solr_args.append('!token_s_' + narg[6:])
                        else:
                            solr_args.append('token_s_' + narg[6:])
                            if or_group_id != None:
                                or_groups[or_group_id].append('token_s_' + narg[6:])

                        if db.has_id(u'f_' + narg[6:]):
                            #oarg = db.get_id_for(u'f_' + narg[6:])
                            oarg = db.get_id_for(u'f_' + narg[6:])

                    except:
                        pass#import pdb;pdb.set_trace()
        else:
            if not arg.startswith('org_'):
                solr_args.append(arg)
            else:
                solr_args.append(arg[6:])
                if or_group_id != None:
                    or_groups[or_group_id].append(arg[6:])


        types.append(not it_is_set)

        #print compulsory
        #print it_is_set
        just_all_set_ids.append(oarg)
        if compulsory:
            if it_is_set:
                c_args_s.append(oarg)
            else:
                c_args_m.append(oarg)
        else:
            if it_is_set:
                s_args_s.append(oarg)
            else:
                s_args_m.append(oarg)


    for item in qobj.org_has_all:
        #
        or_groups[item].append('dep_a_anyrel')


    together = c_args_s + c_args_m

    counts = []# [set_count[x] for x in together]
    min_c = 0#min(counts)
    rarest = 0#together[0]#counts.index(min_c)]
    #print >> sys.stderr, 'optional:', optional
    #print >> sys.stderr, 'types:', types
    solr_or_groups = []


    return rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args, or_groups



def query(query_fields):

    #print >> sys.stderr, 'query fields:', query_fields
    """
    query_fields: A list of strings describing the data to fetch
          Each string names a set to retrieve

          (gov|dep)_(a|s)_deptype
          - gov -> retrieve a from-governor-to-dependent mapping/set
          - dep -> retrieve a from-dependent-to-governor mapping/set
          - a -> retrieve a mapping (i.e. used as the third argument of the pairing() function
          - s -> retrieve a set (i.e. the set of governors or dependents of given type)
          - deptype -> deptype or u"anytype"
          prefixed with "!" means that only non-empty sets are of interest

          tag_s_TAG  -> retrieve the token set for a given tag
          prefixed with "!" means that only non-empty sets are of interest

          token_s_WORD -> retrieve the token set for a given token
          lemma_s_WORD -> retrieve the token set for a given lemma
          prefixed with "!" means that only non-empty sets are of interest
    """

    joins=[(u"FROM graph",[])]
    wheres=[]
    args=[]
    selects=[u"graph.graph_id",u"graph.token_count"]
    for i,f in enumerate(query_fields):
        match=field_re.match(f)
        assert match
        req,ftype,stype,res=match.groups() #required? field-type?  set-type?  restriction
        if req==u"!":
            j_type=u""
        elif not req:
            j_type=u"LEFT "
        else:
            assert False #should never happen
        if ftype in (u"gov",u"dep"):
            joins.append((u"%sJOIN rel AS t_%d ON graph.graph_id=t_%d.graph_id and t_%d.dtype=?"%(j_type,i,i,i),[res]))
            if stype==u"s":
                selects.append(u"t_%d.token_%s_set"%(i,ftype))
            elif stype==u"a":
                selects.append(u"t_%d.token_%s_map"%(i,ftype))
        elif ftype in (u"token",u"lemma",u"tag"):
            joins.append((u"%sJOIN %s_index AS t_%d ON graph.graph_id=t_%d.graph_id and t_%d.%s=?"%(j_type,ftype,i,i,i,ftype),[res]))
            selects.append(u"t_%d.token_set"%i)
    
    joins.sort() #This is a horrible hack, but it will sort FROM JOIN ... LEFT JOIN the right way and help the QueryPlan generator
    q=u"SELECT %s"%(u", ".join(selects))
    q+=u"\n"+(u"\n".join(j[0] for j in joins))
    q+=u"\n"
    args=[]
    for j in joins:
        args.extend(j[1])
    return q,args

def get_data_from_db(db_conn,graph_id):
    results=db_conn.execute('SELECT conllu_data_compressed,conllu_comment_compressed FROM graph WHERE graph_id=?',(str(graph_id),))
    for sent,comment in results.fetchall():
        return zlib.decompress(sent).strip(),zlib.decompress(comment).strip()
    return None,None

def load(pyxFile):
    """Loads a search pyx file, returns the module"""
    ###I need to hack around this, because this thing is messing stdout
    print >> sys.stderr, "Loading", pyxFile
    error=subprocess.call(["python","compile_ext.py",pyxFile], stdout=sys.stderr, stderr=sys.stderr)
    if error!=0:
        print >> sys.stderr, "Cannot compile search code, error:",error
        sys.exit(1)
    mod=importlib.import_module(pyxFile)
    return mod

def get_url(comments):
    for c in comments:
        if c.startswith(u"# URL:"):
            return c.split(u":",1)[1].strip()
    return None

def query_from_db(q_obj,db_name,sql_query,sql_args,max_hits,context, case):#,set_dict, set_count):

    start = time.time()
    db=db_util.DB()
    db.open(solr_url, db_name)

    print >> sys.stderr, 'q_fields',query_obj.query_fields
    rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args, solr_or_groups = map_set_id(query_obj.query_fields, db, query_obj)
    #print rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args 
    print >> sys.stderr, 'solor', solr_or_groups

    #Inits of all kind
    db.init_lmdb(c_args_s, c_args_m, rarest)
    #db.begin_search(extras_dict, [item[1:] for item in solr_args if item.startswith('!')], [item for item in solr_args if not item.startswith('!')], "http://localhost:8983/solr/dep_search")
    q_obj.set_db_options(just_all_set_ids, types, optional)    


    #import pdb;pdb.set_trace()

    from solr_query_thread import SolrQuery
    solr_q = SolrQuery(extras_dict, [item[1:] for item in solr_args if item.startswith('!')], solr_or_groups, solr_url, case)#, q_obj=q_obj)
    #print solr_q.get_solr_query()

    tree_id_queue = solr_q.get_queue()

    counter = 0
    while (not solr_q.finished or not tree_id_queue.empty()):
        res = tree_id_queue.get()
        if res == -1:break
        try:

            db.xset_tree_to_id(res)
            res_set = q_obj.check_tree_id(res, db)    

            if len(res_set) > 0:
                counter+=1
                #Get the tree text:
                tree_text = db.get_tree_text()
                tree_lines=tree_text.split("\n")
                if counter >= max_hits and max_hits > 0:
                    break
                for r in res_set:
                    print "# visual-style   " + str(r + 1) + "      bgColor:lightgreen"
                    try:
                        print "# hittoken:\t"+tree_lines[r] 
                    except:
                        pass#print '##', r
                #hittoken once the tree is really here!

                print tree_text
                print
        except: pass 

    solr_q.kill()         
    print >> sys.stderr, "Found %d trees in %.3fs time"%(counter,time.time()-start)
    return counter
    
def main(argv):
    global query_obj

    #XXX: Will fix!
    global solr_url

    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=500, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-d', '--database', default="/mnt/ssd/sdata/pb-10M/*.db",help='Name of the database to query or a wildcard of several DBs. Default: %(default)s.')
    parser.add_argument('-o', '--output', default=None, help='Name of file to write to. Default: STDOUT.')
    parser.add_argument('-s', '--solr', default="http://localhost:8983/solr/dep_search", help='Solr url. Default: %(default)s')
    parser.add_argument('search', nargs="?", default="parsubj",help='The name of the search to run (without .pyx), or a query expression. Default: %(default)s.')
    parser.add_argument('--context', required=False, action="store", default=0, type=int, metavar='N', help='Print the context (+/- N sentences) as comment. Default: %(default)d.')
    parser.add_argument('--keep_query', required=False, action='store_true',default=False, help='Do not delete the compiled query after completing the search.')
    parser.add_argument('-i', '--case', required=False, action='store_true',default=False, help='Case insensitive search.')

    args = parser.parse_args(argv[1:])

    if args.output is not None:
        sys.stdout = open(args.output, 'w')

    if os.path.exists(args.search+".pyx"):
        print >> sys.stderr, "Loading "+args.search+".pyx"
        mod=load(args.search)
    else:
        path = '/'.join(args.database.split('/')[:-1])
        json_filename = path + '/symbols.json' 
        #This is a query, compile first
        import pseudocode_ob_3 as pseudocode_ob

        import hashlib
        m = hashlib.md5()
        m.update(args.search + str(args.case) + str(args.database))

        solr_url = args.solr

        #1. Check if the queries folder has the search
        #2. If not, generate it here and move to the new folder
        try:
            os.mkdir(query_folder)
        except:
            pass

        dbs=glob.glob(args.database)
        dbs.sort()

        db=db_util.DB()
        db.open(solr_url, dbs[0])

        temp_file_name = 'qry_' + m.hexdigest() + '.pyx'
        if not os.path.isfile(query_folder + temp_file_name):
            f = open('qry_' + m.hexdigest() + '.pyx', 'wt')
            try:
                pseudocode_ob.generate_and_write_search_code_from_expression(args.search, f, json_filename=json_filename, db=db, case=args.case)
            except Exception as e:
                os.remove(temp_file_name)
                raise e

            mod=load(temp_file_name[:-4])
            os.rename(temp_file_name, query_folder + temp_file_name)
            os.rename(temp_file_name[:-4] + '.cpp', query_folder + temp_file_name[:-4] + '.cpp')
            os.rename(temp_file_name[:-4] + '.so', query_folder + temp_file_name[:-4] + '.so')

        else:

            os.rename(query_folder + temp_file_name, temp_file_name)

            mod=load(temp_file_name[:-4])            

            os.rename(temp_file_name, query_folder + temp_file_name)
            os.rename(temp_file_name[:-4] + '.cpp', query_folder + temp_file_name[:-4] + '.cpp')
            os.rename(temp_file_name[:-4] + '.so', query_folder + temp_file_name[:-4] + '.so')

    query_obj=mod.GeneratedSearch()
    #sql_query,sql_args=query(query_obj.query_fields)
    sql_query = ''
    sql_args = ''
 
    dbs=glob.glob(args.database)
    dbs.sort()

    #hacking and cracking
    print >> sys.stderr, 'dbs:',dbs
    #dbs = eval(dbs)

    #inf = open(dbs.rstrip('/') + '/set_dict.pickle','rb')
    #set_dict, set_count = pickle.load(inf)
    #inf.close()
    #print set_dict, set_count
    #import pdb;pdb.set_trace()

    total_hits=0
    for d in dbs:
        print >> sys.stderr, 'querying' ,d

        #inf = open(d.rstrip('/') + '/set_dict.pickle','rb')
        #set_dict, set_count = pickle.load(inf)
        #inf.close()

        
        total_hits+=query_from_db(query_obj,d,sql_query,sql_args,args.max,args.context, args.case)#, set_dict, set_count)
        #if total_hits >= args.max and args.max > 0:
        #    break
    print >> sys.stderr, "Total number of hits:",total_hits

    if not args.keep_query:
        try:
            pass
            #os.remove(temp_file_name)
            #os.remove(temp_file_name[:-4] + '.cpp')
            #os.remove(temp_file_name[:-4] + '.so')
        except:
            pass



if __name__=="__main__":
    sys.exit(main(sys.argv))
