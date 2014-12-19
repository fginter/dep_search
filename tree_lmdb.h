#ifndef __tree_lmdb_h__
#define __tree_lmdb_h__

#include <lmdb.h>

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
    uint64_t *setdata; //Set data arrays for the sets in set_indices
};
    

#endif
