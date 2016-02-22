#ifndef __tree_lmdb_h__
#define __tree_lmdb_h__

#include <lmdb.h>
#include "setlib/tset.h"
using namespace tset;


//The data is serialized in this order
class Tree {
public:
    Tree();
    ~Tree();

    //This data is saved
    uint16_t tree_length; 
    uint16_t set_count; //Number of sets stored in set_indices and sets
    uint16_t map_count; //Number of maps stored in map_indices and maps
    uint32_t *set_indices; //Index for every set (i.e. what kind of set is it?
    uint32_t *map_indices; //Index for every map (i.e. what kind of map is it?
    uint16_t *map_lengths; //For every map, the length (in bytes) of the data it stores
    uint64_t *set_data; //Set data arrays for the sets in set_indices
    void *serialized_map_data; //Serialized array for the maps in map_indices
    uint16_t zipped_tree_text_length; //length of the zipped tree data
    void *zipped_tree_text;  //zipped tree data
    
    //This data is not saved
    int array_length;
    uint16_t *map_data_pointer_byte_offsets;

    void deserialize(void *serialized_data);
    //serialize is written on the python side because we don't need it here

    //Fill count many sets into set_pointers
    //set_types: 1:tset  2:tsetarray
    int fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count);
};

mode_t get_mode();
void report(const char* msg, int err);
uint32_t *binary_search(uint32_t what, uint32_t *beg, uint32_t *end); 

#endif
