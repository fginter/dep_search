#ifndef __tree_lmdb_h__
#define __tree_lmdb_h__

#include <lmdb.h>
#include "setlib/tset.h"
using namespace tset;

uint32_t *binary_search(uint32_t what, uint32_t *beg, uint32_t *end);

class LMDB {
public:
    LMDB();
    int op_count; //Counter of operations in the current transaction so we commit every now and then
    MDB_env *mdb_env;
    MDB_txn *txn;
    MDB_dbi db_k2t; //Database mapping arbitrary keys to tree number (which is an integer). Allows duplication, sorts the tree numbers.
    MDB_dbi db_f2s; //Database mapping integer (32-bit) keys and tree number (32-bit) as a single DB key
    MDB_dbi db_tdata; //Database storing the full tree data indexed by tree number (32-bit)

    int open_db(const char *name); //Opens the DB with flags suitable for indexing, etc... Not meant to be general.

    int start_transaction();
    int restart_transaction();
    int finish_indexing();
    int store_tree_flag(unsigned int tree_id, unsigned int flag_number);
    int store_tree_data(unsigned int tree_id, void *t_data, int size);
    int store_key_tree(unsigned int tree_id, void *key_data, int key_size);
};
 

class Tree {
public:
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
    
    int array_length;
    uint16_t *map_data_pointer_byte_offsets;

    void deserialize(void *serialized_data);

    //Fill count many sets into set_pointers
    //set_types: 1:tset  2:tsetarray
    int fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count);
};
    

#endif
