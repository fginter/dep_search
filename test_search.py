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
            return False

        #so, now s_N are nouns not governing a cop
        #shit - do I need a for loop here really?
        for k in s_koska:
            if t.govs[k]&s_N:
                return True
        return False

class SearchPtv(Query):
    
    def __init__(self):
        Query.__init__(self)
        self.query_fields=[u"govs",u"deps",u"!d_govs_nsubj",u"!d_deps_nsubj",u"!d_govs_dobj",u"!d_deps_dobj",u"!tags_N",u"!tags_CASE_Par",u"d_govs_num",u"d_deps_num",u"d_deps_xcomp",u"d_deps_iccomp"]

    def match(self,t):
        """
        _ >nsubj (N+Par !>num !Par) >dobj Par !<xcomp _ !<iccomp _ 
        """

        s_N_Par=t.tags[u"CASE_Par"]&t.tags[u"N"]

        num_Par=(t.d_deps["num"]-t.tags[u"CASE_Par"]) # num tokens which are not partitive --> we don't want these
        for num in num_Par:
            s_N_Par-=t.govs[num]
        #s_N_Par is now nouns in partitive not governing num

        s_N_Par&=t.d_deps[u"nsubj"] #...and only those which are governed by a subject

        if not s_N_Par:
            return False

        s_nsubj_dobj=t.d_govs[u"dobj"]&t.d_govs[u"nsubj"] #words that govern both a subject and an object
        s_nsubj_dobj-=t.d_deps[u"xcomp"]
        s_nsubj_dobj-=t.d_deps[u"iccomp"]
        #...and are not governed by xcomp & iccomp

        if not s_nsubj_dobj:
            return False

        #Again a for loop! Do I really need it?
        for subj in s_N_Par:
            govs=t.govs[subj]&s_nsubj_dobj # now we have to find all objects and check the word order
            for gov in govs:
                objs=t.deps[gov]&t.d_deps[u"dobj"]&t.tags[u"CASE_Par"] # only partitive objects
                for obj in objs:
                    if subj<obj:
                        return True
        return False
