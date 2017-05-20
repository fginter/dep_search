import traceback
import sys
import pysolr
import requests
import json

ID,FORM,LEMMA,UPOS,XPOS,FEATS,HEAD,DEPREL,DEPS,MISC=range(10)

class SolrIDX(object):

    def __init__(self,args):
        self.documents=[] # List of documents to be pushed into solr at the next convenient occasion
        self.batch_size=10000
        self.tree_count=0
        self.solr_url=args.solr
        self.current_id=0
        self.url=u"unknown"
        self.lang=unicode(args.lang)
        self.source=unicode(args.source)
        self.query_for_id()

    def query_for_id(self):
        s=pysolr.Solr(self.solr_url,timeout=600)
        r=requests.get(self.solr_url+"/select",data={u"q":u"*:*",u"stats.field":"id",u"stats":u"true",u"wt":u"json",u"rows":0})
        response=json.loads(r.text)
        max_id=response["stats"]["stats_fields"]["id"]["max"]
        if max_id is None:
            self.current_id=0
        else:
            self.current_id=int(max_id)
        print "Solr setting id to",self.current_id
        
    def commit(self,force=False):
        if force or len(self.documents)>=self.batch_size:
            try:
                s=pysolr.Solr(self.solr_url,timeout=600)
                self.tree_count+=len(self.documents) #sum(len(d[u"_childDocuments_"]) for d in self.documents)
                print >> sys.stderr, self.tree_count, "trees in Solr"
                s.add(self.documents)
                self.documents=[]
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()
                if len(self.documents)>10*self.batch_size:
                    print >> sys.stderr, "Too many documents uncommitted", len(self.documents)
                    sys.exit(-1)

    def next_id(self):
        self.current_id+=1
        return self.current_id
        
    def new_doc(self,url,lang):
        self.url=url
        self.lang=lang
        #self.documents.append({u"id":self.next_id(),u"url":url,u"lang":lang,u"_childDocuments_":[]})
        
    def add_to_idx(self, conllu):
        """ 
        id - integer id
        conllu - list of lists as usual
        """
        
        feats=set()
        words=[]
        lemmas=[]
        relations=set()

        for cols in conllu:
            feats.add(cols[UPOS])
            if cols[FEATS]!=u"_":
                feats|=set(cols[FEATS].split(u"|"))
            words.append(cols[FORM])
            lemmas.append(cols[LEMMA])
            if cols[DEPREL]!=u"root":
                relations.add(cols[DEPREL])
            if cols[DEPS]!=u"_":
                for g_dtype in cols[DEPS].split(u"|"):
                    g,dtype=g_dtype.split(u":",1)
                    if dtype!=u"root":
                        relations.add(dtype)
        d={}
        d[u"id"]=self.next_id()
        d[u"words"]=u" ".join(words)
        d[u"lemmas"]=u" ".join(lemmas)
        if feats:
            d[u"feats"]=list(feats)
        if relations:
            d[u"relations"]=list(relations)
        d[u"url"]=self.url
        d[u"lang"]=self.lang
        d[u"source"]=self.source

        self.documents.append(d)
        self.commit()
        return d[u"id"]
