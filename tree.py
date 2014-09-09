ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

class Tree(object):

    @classmethod
    def from_conll(cls,conll):
        t=cls()
        t.govs=[set() for _ in range(len(conll))]
        t.deps=[set() for _ in range(len(conll))]
        for cols in conll:
            t.tokens.append(cols[FORM])
            t.lemmas.append(cols[LEMMA])
            id=int(cols[ID])-1
            t.dict_tokens.setdefault(cols[FORM],set()).add(id)
            t.dict_lemmas.setdefault(cols[LEMMA],set()).add(id)

            t.govs[id].add(int(cols[HEAD])-1)
            t.deps[int(cols[HEAD])-1].add(id)
            t.d_deps.setdefault(cols[DEPREL],set()).add(id) #this is a DEPREL dependent
            t.d_govs.setdefault(cols[DEPREL],set()).add(int(cols[HEAD])-1) #this is a DEPREL governor
            t.tags.setdefault(cols[POS],set()).add(id)
            if cols[FEAT]!=u"_":
                for f in cols[FEAT].split(u"|"):
                    t.tags.setdefault(f,set()).add(id)
        return t

    def to_conll(self,out):
        for idx,(token,lemma) in enumerate(zip(self.tokens,self.lemmas)):
            g=list(self.govs[idx])[0]+1
            print >> out, u"\t".join((unicode(idx+1),token,lemma,lemma,u"_",u"_",u"_",u"_",unicode(g),unicode(g),u"_",u"_",u"_",u"_"))
        print >> out
    
    def __init__(self):
        self.tokens=[] #list of tokens
        self.lemmas=[] #list of lemmas
        self.d_govs={}  #deptype -> set of token ids (0-based)
        self.d_deps={}  #deptype -> set of token ids (0-based)
        self.tags={}  #morhotag -> set of token ids (0-based)
        self.govs=[] #[set(),...]
        self.deps=[] #[set(),...]
        self.dict_tokens={} #token: set()
        self.dict_lemmas={} #lemma: set()
    
            
