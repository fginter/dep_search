from __future__ import print_function
import re
import yaml
import os.path
import glob

THISDIR=os.path.abspath(os.path.dirname(__file__))

class Corpus(object):

    def __init__(self,id,name,paths):
        self.id=id
        self.name=name
        self.dbs=[]
        #expand path - space separated list of paths that can be globbed or are a directory
        for p in paths.split():
            if os.path.isdir(p):
                p=os.path.join(p,'*.db')
            self.dbs.extend(sorted(glob.glob(p)))

    def as_dict(self):
        return {"id":self.id,"name":self.name,"dbs":self.dbs}

def get_corpora(corpora_yaml):
    corpora={} # id -> Corpus()
    with open(corpora_yaml) as f:
        for corpus_id, corpus_data in yaml.load(f).iteritems():
            if corpus_id.startswith("wildcard_"): #wildcard, look for pathglob
                corpus_id=corpus_id.replace("wildcard_","") #remove the wildcard_ string
                cpaths=sorted(glob.glob(corpus_data["pathglob"])) #These are the corpora matched by the wildcard
                pathre=re.compile(corpus_data["pathre"]) #Regex to match the path and pick the name from it
                for cpath in cpaths: #One path from the glob, ie one indexed corpus
                    match=pathre.match(cpath)
                    if not match:
                        continue
                    cname=match.expand(corpus_data["name"]) #name with \1 substitution
                    c=Corpus(match.expand(corpus_id),cname,cpath)
                    corpora[c.id]=c.as_dict()
            else:
                c=Corpus(corpus_id,**corpus_data)
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
    corpora=get_corpora(os.path.join(THISDIR,"corpora.yaml"))
    corpus_groups=get_corpus_groups(os.path.join(THISDIR,"corpus_groups.yaml"),corpora)
    print(corpus_groups)

