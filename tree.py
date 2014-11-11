import setlib.setlib.pytset as pytset

ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

class Tree(object):

    @classmethod
    def from_conll(cls,comments,conll):
        t=cls()
        lines=[] #will accumulate here conll-u lines
        for idx,cols in enumerate(conll):
            lines.append([cols[ID],cols[FORM],cols[LEMMA],cols[POS],cols[POS],cols[FEAT],cols[HEAD],cols[DEPREL],u"_",u"_"])
            if cols[FORM] not in t.tokens:
                t.tokens[cols[FORM]]=pytset.PyTSet(len(conll))
            if LEMMA not in t.lemmas:
                t.lemmas[cols[LEMMA]]=pytset.PyTSet(len(conll))
            t.tokens[cols[FORM]].add_item(idx)
            t.lemmas[cols[LEMMA]].add_item(idx)

            if cols[FEAT]!=u"_":
                for f in cols[FEAT].split(u"|"):
                    if f not in t.tags:
                        t.tags[f]=pytset.PyTSet(len(conll))
                    t.tags[f].add_item(idx)
            if cols[HEAD] not in (u"_",u"0"):
                t.add_rel(int(cols[HEAD])-1,idx,cols[DEPREL],len(conll))
                t.add_rel(int(cols[HEAD])-1,idx,u"anyrel",len(conll))
        t.comments=u"\n".join(comments)
        t.conllu=u"\n".join(u"\t".join(l) for l in lines)
        return t

    def add_rel(self,gov_idx,dep_idx,dtype,graph_len):
        if dtype not in self.rels:
            self.rels[dtype]=([set() for _ in range(graph_len)], [set() for _ in range(graph_len)])
        gidx,didx=self.rels[dtype]
        gidx[gov_idx].add(dep_idx)
        gidx[dep_idx].add(gov_idx)

    
    def __init__(self):
        self.rels={}  #key: rel or "anyrel"  value: ([govs as a list of set(), deps as a list of set()]) e.g. ([set(2),_,_],[_,_,set(0)]) means token 0 governs token 2, and token 2 is governed by token 0

        self.tokens={} #key: token, value: PyTSet()
        self.lemmas={} #key: lemma: value PyTSet()
        self.tags={} #key: tag value: PyTSet()
        self.conllu=None #string
        self.comments=u""
