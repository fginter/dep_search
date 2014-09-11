def search_koska(t):
    """
    koska < (N+Nom !>cop _)
    """
    if u"koska" not in t.dict_tokens:
        return False
    s_koska=t.dict_tokens[u"koska"]

    if u"N" not in t.tags:
        return False
    s_N=t.tags[u"N"] #all nouns

    if u"CASE_Nom" not in t.tags:
        return False
    s_N&=t.tags[u"CASE_Nom"]

    if u"cop" in t.d_govs:
        s_N-=t.d_govs[u"cop"] #must not govern cop

    if not s_N:
        return False

    #so, now s_N are nouns not governing a cop
    #shit - do I need a for loop here really?
    for k in s_koska:
        if t.govs[k]&s_N:
            return True

    return False

def search_ptv(t):
    """
    _ >nsubj (N+Par !>num !Par) >dobj _ !<xcomp _ !<ccomp _ 
    """

    if u"dobj" not in t.d_govs or u"nsubj" not in t.d_govs or u"N" not in t.tags or u"CASE_Par" not in t.tags:
         return False

    s_N_Par=t.tags[u"CASE_Par"]&t.tags[u"N"]


    if u"num" in t.d_govs:
         s_N_Par-=(t.d_govs["num"]-t.tags[u"CASE_Par"])
    #s_N_Par is now nouns in partitive not governing num

    s_N_Par&=t.d_deps[u"nsubj"] #...and only those which are governed by a subject

    if not s_N_Par:
        return False

    s_nsubj_dobj=t.d_govs[u"dobj"]&t.d_govs[u"nsubj"] #words that govern both a subject and an object
    if u"xcomp" in t.d_deps:
        s_nsubj_dobj-=t.d_deps[u"xcomp"]
    if u"ccomp" in t.d_deps:
        s_nsubj_dobj-=t.d_deps[u"ccomp"]
    #...and are not governed by xcomp & ccomp

    if not s_nsubj_dobj:
        return False
    
    
    #Again a for loop! Do I really need it?
    for subj in s_N_Par:
        if t.govs[subj]&s_nsubj_dobj:
            return True
    return False
