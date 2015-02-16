import setlib.pytset as pytset

ID,FORM,LEMMA,PLEMMA,POS,PPOS,FEAT,PFEAT,HEAD,PHEAD,DEPREL,PDEPREL=range(12)

class Tree(object):

    @classmethod
    def from_conll(cls,comments,conll):
        t=cls()
        lines=[] #will accumulate here conll-u lines
        for idx,cols in enumerate(conll):
            # convert second layer into conll-u
            heads,deprels=cols[HEAD].split(u","),cols[DEPREL].split(u",")
            deps=[]
            for index,(g,dtype) in enumerate(zip(heads,deprels)):
                if index==0:
                    continue
                deps.append((int(g),dtype))
            cols[HEAD]=heads[0]
            cols[DEPREL]=deprels[0]
            if deps:
                DEPS=u"|".join(unicode(g)+u":"+dtype for g,dtype in sorted(deps))
            else:
                DEPS=u"_"
            lines.append([cols[ID],cols[FORM],cols[LEMMA],cols[POS],cols[POS],cols[FEAT],cols[HEAD],cols[DEPREL],DEPS,u"_"])
            if cols[FORM] not in t.tokens:
                t.tokens[cols[FORM]]=pytset.PyTSet(len(conll))
            if LEMMA not in t.lemmas:
                t.lemmas[cols[LEMMA]]=pytset.PyTSet(len(conll))
            t.tokens[cols[FORM]].add_item(idx)
            t.lemmas[cols[LEMMA]].add_item(idx)
            if cols[POS]!=u"_":
                pos=u"POS_"+cols[POS]
                if pos not in t.tags:
                    t.tags[pos]=pytset.PyTSet(len(conll))
                t.tags[pos].add_item(idx)
            if cols[FEAT]!=u"_":
                for f in cols[FEAT].split(u"|"):
                    if f not in t.tags:
                        t.tags[f]=pytset.PyTSet(len(conll))
                    t.tags[f].add_item(idx)
            if cols[HEAD] not in (u"_",u"0"):
                t.add_rel(int(cols[HEAD])-1,idx,cols[DEPREL],len(conll))
                t.add_rel(int(cols[HEAD])-1,idx,u"anyrel",len(conll))
                if DEPS!=u"_":
                    for dep in DEPS.split(u"|"):
                        g,dtype=dep.split(u":")
                        t.add_rel(int(g)-1,idx,dtype,len(conll))
        t.comments=u"\n".join(comments)
        t.conllu=u"\n".join(u"\t".join(l) for l in lines)
        return t

    def add_rel(self,gov_idx,dep_idx,dtype,graph_len):
        if dtype not in self.rels:
            self.rels[dtype]=([set() for _ in range(graph_len)], [set() for _ in range(graph_len)])
        gidx,didx=self.rels[dtype]
        gidx[gov_idx].add(dep_idx)
        didx[dep_idx].add(gov_idx)


    def serialized(self,symbols_table):
        zipped_txt=zlib.compress((self.comments+u"\n"+self.conllu).encode("utf-8"))
        

        for token, token_set in t.tokens.iteritems():
            conn.execute('INSERT INTO token_index VALUES(?,?,?)', [token,sent_idx,buffer(token_set.tobytes())])
        for lemma, token_set in t.lemmas.iteritems():
            conn.execute('INSERT INTO lemma_index VALUES(?,?,?)', [lemma,sent_idx,buffer(token_set.tobytes())])
        for tag, token_set in t.tags.iteritems():
            conn.execute('INSERT INTO tag_index VALUES(?,?,?)', [sent_idx,tag,buffer(token_set.tobytes())])
        for dtype, (govs,deps) in t.rels.iteritems():
            ne_g=[x for x in govs if x]
            ne_d=[x for x in deps if x]
            assert ne_g and ne_d
            gov_set=pytset.PyTSet(len(sent),(idx for idx,s in enumerate(govs) if s))
            dep_set=pytset.PyTSet(len(sent),(idx for idx,s in enumerate(deps) if s))
            conn.execute('INSERT INTO rel VALUES(?,?,?,?,?,?)', [sent_idx,dtype,buffer(gov_set.tobytes()),buffer(serialize_as_tset_array(len(sent),govs)),buffer(dep_set.tobytes()),buffer(serialize_as_tset_array(len(sent),deps))])

    
    def __init__(self):
        self.rels={}  #key: rel or "anyrel"  value: ([govs as a list of set(), deps as a list of set()]) e.g. ([set(2),_,_],[_,_,set(0)]) means token 0 governs token 2, and token 2 is governed by token 0

        self.tokens={} #key: token, value: PyTSet()
        self.lemmas={} #key: lemma: value PyTSet()
        self.tags={} #key: tag value: PyTSet()
        self.conllu=None #string
        self.comments=u""
