import sys
import requests
import re
import StringIO
import time
from multiprocessing import Process, Queue

field_re=re.compile(ur"^(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
class SolrQuery():


    def __init__(self,extras_dict, compulsory_items,or_groups, solr):

        self.or_groups = or_groups
        self.extras_dict = extras_dict
        self.compulsory_items = compulsory_items
        self.solr = solr
        self.tree_id_queue = Queue()
        self.finished = False
        self.started = False

	#Start the main loop thread
        self.process = Process(target=self.main_loop)
        self.process.start()

    def get_queue(self):
        return self.tree_id_queue


    def main_loop(self):
        self.started=True
        for idx in self.ids_from_solr_gen():
            #Feed it to the queue
            self.tree_id_queue.put(idx)
        self.finished=True
        self.tree_id_queue.put(-1)

    def kill(self):
        self.process.terminate()


    def get_solr_query(self):

        terms=[]
        for c in self.compulsory_items:

            print >> sys.stderr, 'item', c


            match=field_re.match(c)
            assert match, ("Not a known field description", c)
            if match.group(1) in (u"gov",u"dep"):
                if match.group(3)==u"anyrel":
                   terms.append(u'+relations:*')
                else:
                   terms.append(u'+relations:"%s"'%match.group(3))
            elif match.group(1)==u"tag":
                terms.append(u'+feats:"%s"'%match.group(3))
            elif match.group(1)==u"lemma":
                terms.append(u'+lemmas:"%s"'%match.group(3))
            elif match.group(1)==u"token":
                terms.append(u'+words:"%s"'%match.group(3))

        or_terms = []
        for group in self.or_groups.values():
            g_terms = []
            for item in group:

                print >> sys.stderr, 'or_group_item', item

                match=field_re.match(item)
                assert match, ("Not a known field description", item)
                if match.group(1) in (u"gov",u"dep"):
                    if match.group(3)==u"anyrel":
                       g_terms.append(u'relations:*')
                    else:
                       g_terms.append(u'relations:"%s"'%match.group(3))
                elif match.group(1)==u"tag":
                    g_terms.append(u'feats:"%s"'%match.group(3))
                elif match.group(1)==u"lemma":
                    g_terms.append(u'lemmas:"%s"'%match.group(3))
                elif match.group(1)==u"token":
                    g_terms.append(u'words:"%s"'%match.group(3))
            print >> sys.stderr, 'g_terms', g_terms
            or_terms.append(u'(' + u' OR '.join(g_terms)  + u')')

        qry=u" ".join(terms)
        if len(terms) > 0 and len(or_terms) > 0:
            qry += u' AND '
        if len(or_terms) > 0:
            qry += u' AND '.join(or_terms)
            
        return qry




    def ids_from_solr_gen(self):

        qry= self.get_solr_query()

        print >> sys.stderr, "Solr qry", qry
        #### XXX TODO How many rows?
        beg=time.time()
        r=requests.get(self.solr+"/select",params={u"q":qry,u"wt":u"csv",u"rows":500000,u"fl":u"id",u"sort":u"id asc"}, stream=True)
        r_iter = r.iter_lines()

        #row_count=r.text.count(u"\n")-1 #how many lines? minus one header line
        #cdef uint32_t *id_array=<uint32_t *>malloc(row_count*sizeof(uint32_t))
        #r_txt=StringIO.StringIO(r.text)
        col_name=r_iter.next() #column name
        assert col_name==u"id", repr(col_name)
        hits = 0
        for idx,id in enumerate(r_iter):
            #assert idx<row_count, (idx,row_count)
            hits +=1
            yield int(id)

        print "Hits from solr:", hits, " in", time.time()-beg, "seconds"
