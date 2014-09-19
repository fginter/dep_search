ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

class Tree(object):

    @classmethod
    def from_conll(cls,conll):
        t=cls()
        t.govs=[set() for _ in range(len(conll))]
        t.deps=[set() for _ in range(len(conll))]
        t.heads=[] #For every token its conll (head,deprel) fields: TODO non-tree
        for cols in conll:
            t.tokens.append(cols[FORM])
            t.lemmas.append(cols[LEMMA])
            id=int(cols[ID])-1
            t.dict_tokens.setdefault(cols[FORM],set()).add(id)
            t.dict_lemmas.setdefault(cols[LEMMA],set()).add(id)
            t.heads.append((int(cols[HEAD])-1,cols[DEPREL]))

            t.govs[id].add(int(cols[HEAD])-1)
            t.deps[int(cols[HEAD])-1].add(id)
            t.d_deps.setdefault(cols[DEPREL],set()).add(id) #this is a DEPREL dependent
            t.d_govs.setdefault(cols[DEPREL],set()).add(int(cols[HEAD])-1) #this is a DEPREL governor
            t.type_deps.setdefault(cols[DEPREL],{}).setdefault(int(cols[HEAD])-1,set()).add(id) # id is a DEPREL dependent for HEAD
            t.type_govs.setdefault(cols[DEPREL],{}).setdefault(id,set()).add(int(cols[HEAD])-1) # HEAD is a DEPREL governor for id
            t.tags.setdefault(cols[POS],set()).add(id)
            if cols[FEAT]!=u"_":
                for f in cols[FEAT].split(u"|"):
                    t.tags.setdefault(f,set()).add(id)
        return t

    def __getstate__(self):
        """
        Pickle uses this to serialize. Because the way this works, we will only
        serialize .tokens and .lemmas and nothing else. The rest will be fetched
        from the DB on a need-to-know basis. This method returns a dictionary
        which pickle will then set to be the de-serialized object's __dict__
        """
        return {"tokens":self.tokens, "lemmas":self.lemmas, "heads":self.heads, "dict_tokens":self.dict_tokens, "dict_lemmas":self.dict_lemmas}

    def to_conll(self,out,form=u"conllu",highlight=None):
        """highlight: set of token indices (0-based) to highlight"""
        if highlight is not None:
            for tidx in sorted(highlight):
                print >> out, u"# visual-style\t%d\tbgColor:green"%(tidx+1)
        for idx,(token,lemma,(head,deprel)) in enumerate(zip(self.tokens,self.lemmas,self.heads)):
            if form==u"conllu":
                print >> out, u"\t".join((unicode(idx+1),token,lemma,u"_",u"_",u"_",unicode(head+1),deprel,u"_",u"_"))
            else:
                print >> out, u"\t".join((unicode(idx+1),token,lemma,lemma,u"_",u"_",u"_",unicode(head+1),unicode(head+1),deprel,deprel,u"_",u"_"))
        print >> out
    
    def __init__(self):
        self.tokens=[] #list of tokens
        self.lemmas=[] #list of lemmas
        self.d_govs={}  #deptype -> set of token ids (0-based)
        self.d_deps={}  #deptype -> set of token ids (0-based)
        self.type_govs={} #deptype -> dict of key:token id, value: set of governors with deptype
        self.type_deps={} #deptype -> dict of key:token id, value: set of dependents with deptype
        self.tags={}  #morhotag -> set of token ids (0-based)
        self.govs=[] #[set(),...]
        self.deps=[] #[set(),...]
        self.dict_tokens={} #token: set()
        self.dict_lemmas={} #lemma: set()
    
            
