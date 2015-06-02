# -*- coding: utf-8 -*-
from query import Query

class SearchKoska(Query):

    def __init__(self):
        Query.__init__(self)
        self.words=[u"koska"]
        self.query_fields=[u"!tags_N",u"!tags_CASE_Nom",u"d_govs_cop",u"govs"]

    def match(self,t):
        """
        koska < (N+Nom !>cop _)
        """
        s_koska=t.dict_tokens[u"koska"]
        s_N=t.tags[u"N"] #all nouns
        s_N&=t.tags[u"CASE_Nom"]
        #Note, cop is an empty set if there's no cop, maybe that's not too logical?
        s_N-=t.d_govs[u"cop"] #must not govern cop

        if not s_N:
            return set()

        #so, now s_N are nouns not governing a cop
        result=set()
        for k in s_koska:
            if t.govs[k]&s_N:
                result.add(k)
        return result

class SearchPtv(Query):
    
    def __init__(self):
        Query.__init__(self)
        self.query_fields=[u"!d_govs_nsubj",u"!d_deps_nsubj",u"!type_deps_nsubj",u"!d_govs_dobj",u"!d_deps_dobj",u"!type_deps_dobj",u"!tags_N",u"!tags_CASE_Par",u"d_deps_num",u"type_govs_num",u"d_deps_xcomp",u"d_deps_iccomp"]

    def match(self,t):
        """
        _ >nsubj (N+Par !>num !Par) >dobj Par !<xcomp _ !<iccomp _ 
        """

        s_N_Par=t.tags[u"CASE_Par"]&t.tags[u"N"]

        num_Par=(t.d_deps["num"]-t.tags[u"CASE_Par"]) # num tokens which are not partitive --> we don't want these
        for num in num_Par:
            s_N_Par-=t.type_govs.get(u"num",{}).get(num,set()) # oho, this is really complex...
        #s_N_Par is now nouns in partitive not governing num

        s_N_Par&=t.d_deps[u"nsubj"] #...and only those which are governed by a subject

        if not s_N_Par:
            return set()

        s_par_obj=t.tags[u"CASE_Par"]&t.d_deps[u"dobj"] # partitive objects

        if not s_par_obj:
            return set()

        s_nsubj_dobj=t.d_govs[u"dobj"]&t.d_govs[u"nsubj"] #words that govern both a subject and an object
        s_nsubj_dobj-=t.d_deps[u"xcomp"]
        s_nsubj_dobj-=t.d_deps[u"iccomp"]
        #...and are not governed by xcomp & iccomp

        if not s_nsubj_dobj:
            return set()

        result=set()
        for item in s_nsubj_dobj:
            if t.type_deps[u"nsubj"].get(item,set())&s_N_Par and t.type_deps[u"dobj"].get(item,set())&s_par_obj:
                # now the word order...
                max_obj=max(t.type_deps[u"dobj"][item]&s_par_obj)
                for subj in t.type_deps[u"nsubj"][item]&s_N_Par:
                    if subj<max_obj: # we found at least one subject which is smaller than one object
                        result.add(item)
                        break

        return result

class SearchNSubjCop(Query):
    
    def __init__(self):
        Query.__init__(self)
        self.query_fields=[u"!d_deps_nsubj-cop"]
        self.words=[u"Turku"]

    def match(self,t):
        """
        _ >nsubj-cop Turku
        """
        s_abo=t.dict_tokens[u"Turku"]
        s_abo&=t.d_deps[u"nsubj-cop"]
        return s_abo
