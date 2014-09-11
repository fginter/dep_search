import cPickle as pickle
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
        self.d_govs=OnDemandDict()  #deptype -> set of token ids (0-based)
        self.d_deps=OnDemandDict()  #deptype -> set of token ids (0-based)
        self.tags=OnDemandDict()  #morhotag -> set of token ids (0-based)
        self.govs=[] #[set(),...]
        self.deps=[] #[set(),...]
        self.dict_tokens=OnDemandDict() #token: set()
        self.dict_lemmas=OnDemandDict() #lemma: set()
    
            

class P(object):

    def __init__(self,obj):
        self.s=pickle.dumps(obj,pickle.HIGHEST_PROTOCOL)

    def __repr__(self):
        return "P("+self.s+")"

class OnDemandDict(object):

    def __init__(self):
        self.d={}

    def __getstate__(self):
        """Pickle every item separately"""
        x={}
        for k,v in self.d.iteritems():
            x[k]=P(v)
        return x

    def __setstate__(self,s):
        """Simply stores the dictionary with every item separately pickled"""
        self.d=s

    def __getitem__(self,key):
        """Unpickles on-demand"""
        v=self.d[key]
        if isinstance(v,P):
            o=pickle.loads(v.s)
            self.d[key]=o
            return o
        else:
            return v
    
    def __setitem__(self,key,value):
        self.d[key]=value

    
    def setdefault(self,key,value):
        return self.d.setdefault(key,value)

    def __contains__(self,key):
        return key in self.d

class OnDemandList(object):

    def __init__(self):
        self.l=[]

    def __getstate__(self):
        """Pickle every item separately"""
        x=[]
        for v in self.l:
            x.append(P(v))
        return x

    def __setstate__(self,s):
        """Simply stores the dictionary with every item separately pickled"""
        self.l=s


    def append(self,x):
        self.l.append(x)

    def __getitem__(self,i):
        v=self.l[i]
        if isinstance(v,P):
            o=pickle.loads(v)
            self.l[i]=o
            return o
        else:
            return o
