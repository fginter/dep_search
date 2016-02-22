# distutils: language = c++
# distutils: libraries = lmdb
# distutils: sources = tree_lmdb.cpp
import struct
import json
import zlib
import setlib.pytset as pytset

ID,FORM,LEMMA,UPOS,XPOS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)

cdef class Py_Tree:

    def __cinit__(self):
        self.thisptr=new Tree()

    def __dealloc__(self):
        del self.thisptr

    def __init__(self):
        pass

    def deserialize(self, char *binary_blob):
        self.thisptr.deserialize(<void *>binary_blob)
        #print self.thisptr.zipped_tree_text_length

    def serialize_from_conllu(self, lines, comments, set_dict):
        #this we need to save
        tree_data={"comments":comments,
                   "tokens":list(l[FORM] for l in lines),
                   "lemmas":list(l[LEMMA] for l in lines),
                   "misc":list(l[MISC] for l in lines)}
        tree_data_gz=json.dumps(tree_data)#zlib.compress(json.dumps(tree_data))
        
        #Sets for the UPOS and FEAT
        token_sets={} #Key: set number, Value: Python set() of integers
        arrays={} #Key: relation number, Value: Python set() of (from,to) integer pairs
        for t_idx,line in enumerate(lines):
            for tag in [u"p_"+line[UPOS],u"f_"+line[FORM],u"l_"+line[LEMMA]]+line[FEAT].split(u"|"):
                if tag[2:]!=u"_":
                    set_id=set_dict.setdefault(tag,len(set_dict))
                    token_sets.setdefault(set_id,set()).add(t_idx)
            if line[DEPREL]!=u"_":
                for gov,dep,dtype in [(int(line[HEAD])-1,t_idx, line[DEPREL])]:
                    if gov==-1:
                        continue
                    #TODO: DEPS field
                    set_id_g=set_dict.setdefault(u"g_"+dtype,len(set_dict))
                    arrays.setdefault(set_id_g,set()).add((gov,dep))
                    set_id_g=set_dict.setdefault(u"g_anyrel",len(set_dict))
                    arrays.setdefault(set_id_g,set()).add((gov,dep))

                    set_id_d=set_dict.setdefault(u"d_"+dtype,len(set_dict))
                    arrays.setdefault(set_id_d,set()).add((dep,gov))
                    set_id_d=set_dict.setdefault(u"d_anyrel",len(set_dict))
                    arrays.setdefault(set_id_d,set()).add((dep,gov))

        #Produces the packed map data
        map_lengths=[]
        map_data=""
        for map_num,pairs in sorted(arrays.iteritems()):
            pairs_packed="".join(struct.pack("=HH",*pair) for pair in sorted(pairs))
            map_lengths.append(len(pairs_packed))
            map_data+=pairs_packed

        #Produces the packed set data
        set_data=""
        for set_num, indices in sorted(token_sets.iteritems()):
            s=pytset.PyTSet(len(lines),indices)
            bs=s.tobytes(include_size=False)
#            assert len(bs)/8==len(lines)/8+1, (len(bs)/8,len(lines)/8+1)
            set_data+=bs
        #treelen  16
        #set_count 16
        #map_count 16
        #set_indices 32
        #map_indices  32
        #map_lengths 16
        #set_data  8
        #map_data 8
        #zip_len 16
        #zip_data 8
        blob="=HHH%(set_count)dI%(map_count)dI%(map_count)dH%(set_data_len)ds%(map_data_len)dsH%(zip_data_len)ds"%\
            {"set_count":len(token_sets),
             "map_count":len(arrays),
             "set_data_len":len(set_data),
             "map_data_len":len(map_data),
             "zip_data_len":len(tree_data_gz)}
        args=[len(lines),len(token_sets),len(arrays)]+\
              sorted(token_sets)+\
              sorted(arrays)+\
              map_lengths+\
              [set_data,map_data,len(tree_data_gz),tree_data_gz]
        serialized=struct.pack(blob,*args)
        #print "serializer:", len(lines),len(token_sets),len(arrays), len(set_data), len(map_data), len(tree_data_gz), map_lengths, sorted(token_sets)
        return serialized, blob #The binary blob of the sentence
