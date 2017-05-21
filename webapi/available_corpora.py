from __future__ import print_function
import re
import yaml
import os.path
import glob
import requests
import json

THISDIR=os.path.abspath(os.path.dirname(__file__))

class Corpus(object):

    def __init__(self,id,name):
        self.id=id
        self.name=name
        self.dbs=[]
        # #expand path - space separated list of paths that can be globbed or are a directory
        # for p in paths.split():
        #     if os.path.isdir(p):
        #         p=os.path.join(p,'*.db')
        #     self.dbs.extend(sorted(glob.glob(p)))

    def as_dict(self):
        return {"id":self.id,"name":self.name}#,"dbs":self.dbs}

def get_corpora(corpora_yaml,solr_url):
    r=requests.get(solr_url+"/select",params={"q":"*:*","stats":"on","stats.field":"source","stats.calcdistinct":"true","rows":"0","wt":"json"})
    response=r.text
    if not response.strip():
        return {}
    known_corpora=json.loads(response)["stats"]["stats_fields"]["source"]["distinctValues"] #corpus ids known in solr
    corpora={} # id -> Corpus()
    with open(corpora_yaml) as f:
        for corpus_id_re, corpus_data in yaml.load(f).iteritems():
            #Which corpora match?
            corpus_id_re=re.compile(u"^"+corpus_id_re+u"$")
            for known_c in known_corpora:
                match=corpus_id_re.match(known_c)
                if match:
                    cname=match.expand(corpus_data["name"])
                    c=Corpus(known_c,cname)
                    corpora[c.id]=c.as_dict()
    return corpora

def matching_corpora(idregex,corpora):
    idre=re.compile(idregex)
    return sorted(cid for cid in corpora if idre.match(cid))

def get_corpus_groups(available_corpora_yaml,corpora):
    groups=[]
    with open(available_corpora_yaml) as f:
        for cgroup in yaml.load(f):
            group_corpus_ids=[]
            for regex in cgroup["corpora"].split():
                group_corpus_ids.extend(matching_corpora(regex,corpora))
            group_corpus_names=list(corpora[c]["name"] for c in group_corpus_ids)
            groups.append({"name":cgroup["name"],"corpora":list(zip(group_corpus_ids,group_corpus_names))})
    return groups

if __name__=="__main__":
    corpora=get_corpora(os.path.join(THISDIR,"corpora.yaml"),"http://localhost:8983/solr/depsearch6")
    corpus_groups=get_corpus_groups(os.path.join(THISDIR,"corpus_groups.yaml"),corpora)
    print(corpus_groups)

