import setlib.pytset as pytset
import json

ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

class SymbolStats(object):

    def __init__(self):
        self.d={} #{(symbol,type,full_form):count}

    def symb(self,symb,s_type,full_form,count=1):
        self.d[(symb,s_type,full_form)]=self.d.get((symb,s_type,full_form),0)+count

    def update_with_json(self,f_name):
        """update own counts with those from the previously saved symbols.json --- needed for indexing in parallel"""
        with open(f_name,"r") as otherf:
            other_d=json.load(otherf)
        for symbol,counts in other_d.iteritems():
            for (s_type,full_f,cnt) in counts:
                self.symb(symbol,s_type,full_f,cnt)

    def save_json(self,f_name):
        #Make a dictionary where a symbol can be loooked up right away
        new_d={}
        for (symb,s_type,full_f),cnt in self.d.iteritems():
            new_d.setdefault(symb,[]).append((s_type,full_f,cnt))
        for v in new_d.itervalues():
            v.sort(key=lambda x:x[-1],reverse=True)
        with open(f_name,"w") as f:
            json.dump(new_d,f,sort_keys=True)

class Tree(object):

    @classmethod
    def from_conll(cls,comments,conll,symb_stats):
        t=cls()
        lines=[] #will accumulate here conll-u lines
        for idx,cols in enumerate(conll):
            # convert second layer into conll-u
            if len(cols)==10: #conllu
                ID,FORM,LEMMA,POS,LANGPOS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)
                lines.append(cols) #this is conll-u already
                deps=cols[DEPS] #conll09 doesn't have this, so we have it in a variable
            else:
                #conll09 for old code compat
                ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)
                heads,deprels=cols[HEAD].split(u","),cols[DEPREL].split(u",")
                deps=[]
                for index,(g,dtype) in enumerate(zip(heads,deprels)):
                    if index==0:
                        continue
                    deps.append((int(g),dtype))
                cols[HEAD]=heads[0]
                cols[DEPREL]=deprels[0]
                if deps:
                    deps=u"|".join(unicode(g)+u":"+dtype for g,dtype in sorted(deps))
                else:
                    deps=u"_"
                lines.append([cols[ID],cols[FORM],cols[LEMMA],cols[POS],cols[POS],cols[FEAT],cols[HEAD],cols[DEPREL],deps,u"_"])
            if cols[FORM] not in t.tokens:
                t.tokens[cols[FORM]]=pytset.PyTSet(len(conll))
            if cols[LEMMA] not in t.lemmas:
                t.lemmas[cols[LEMMA]]=pytset.PyTSet(len(conll))
            t.tokens[cols[FORM]].add_item(idx)
            t.lemmas[cols[LEMMA]].add_item(idx)
            if cols[POS]!=u"_":
                pos=cols[POS]
                if pos not in t.tags:
                    t.tags[pos]=pytset.PyTSet(len(conll))
                t.tags[pos].add_item(idx)
                symb_stats.symb(pos,u"TAG",None)
            if cols[FEAT]!=u"_":
                for f in cols[FEAT].split(u"|"):
                    if u"=" in f:
                        cat,val=f.split(u"=",1)
                        symb_stats.symb(cat,u"CAT",None)
                        symb_stats.symb(val,u"VAL",f)
                    else:
                        cat,val=None,None
                    symb_stats.symb(f,u"CAT=VAL",None)
                    if f not in t.tags:
                        t.tags[f]=pytset.PyTSet(len(conll))
                    if cat is not None and cat not in t.tags:
                        t.tags[cat]=pytset.PyTSet(len(conll))
                    t.tags[f].add_item(idx)
                    if cat is not None:
                        t.tags[cat].add_item(idx)
            if cols[HEAD] not in (u"_",u"0"):
                t.add_rel(int(cols[HEAD])-1,idx,cols[DEPREL],len(conll))
                symb_stats.symb(cols[DEPREL],"DTYPE",None)
                t.add_rel(int(cols[HEAD])-1,idx,u"anyrel",len(conll))
                if deps!=u"_":
                    for dep in deps.split(u"|"):
                        g,dtype=dep.split(u":",1)
                        t.add_rel(int(g)-1,idx,dtype,len(conll))
                        symb_stats.symb(dtype,"DTYPE",None)
        t.comments=u"\n".join(comments)
        t.conllu=u"\n".join(u"\t".join(l) for l in lines)
        return t

    def add_rel(self,gov_idx,dep_idx,dtype,graph_len):
        if dtype not in self.rels:
            self.rels[dtype]=([set() for _ in range(graph_len)], [set() for _ in range(graph_len)])
        gidx,didx=self.rels[dtype]
        gidx[gov_idx].add(dep_idx)
        didx[dep_idx].add(gov_idx)

    
    def __init__(self):
        self.rels={}  #key: rel or "anyrel"  value: ([govs as a list of set(), deps as a list of set()]) e.g. ([set(2),_,_],[_,_,set(0)]) means token 0 governs token 2, and token 2 is governed by token 0

        self.tokens={} #key: token, value: PyTSet()
        self.lemmas={} #key: lemma: value PyTSet()
        self.tags={} #key: tag value: PyTSet()
        self.conllu=None #string
        self.comments=u""
