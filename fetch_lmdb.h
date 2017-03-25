#ifndef _fetch_lmdb_h_
#define _fetch_lmdb_h_

#include "lmdb.h"
#include <iostream>
#include <stdint.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sstream>
#include "tree_lmdb.h"
#include <stdlib.h>

//Let us build this fetching class thing
class LMDB_Fetch{

public:
    MDB_env *mdb_env;
    MDB_txn *txn;
    MDB_dbi db_k2t; //Database mapping uint32 keys to tree number (which is uint32). Allows duplication, sorts the tree numbers.
    MDB_dbi db_tdata; //Database storing the full tree data indexed by tree number (32-bit)

    MDB_dbi db_id2c; //Token & tag etc. id to its count
    MDB_dbi db_tk2id; //Token, tag etc into its id

    MDB_cursor *k2t_cursor; //The cursor to be used
    MDB_cursor *tdata_cursor; //The cursor to be used
    
    bool finished; //We are done, tree and tree_id do not contain anything reasonable
    bool query_started;
    Tree *tree;
    uint32_t tree_id;

    uint32_t* sets;
    uint32_t* arrays;
    int len_sets;
    int len_arrays;
    uint32_t rarest; //this is the key we iterate over

    uint32_t *tree_ids; //solr fills this in db_util.pyx
    int tree_ids_count;

    int tree_id_pointer;

    
    uint32_t * count;
    uint32_t * tag_id;

    uint32_t get_tag_id();
    uint32_t get_count();

    LMDB_Fetch();

    // open and close the DB environment
    int open(const char *name);
    void close();

    // begin_search() and move_to_next_tree() iterate the cursor of k2t
    //starts the search (positions k2t_cursor), sets .finished=true if nothing found
    int begin_search(int ls, int la, uint32_t *lsets, uint32_t* larrays, uint32_t rarest);
    
    //positions k2t_cursor on next tree, sets .finished=true if nothing found
    //this is not something you want to call directly, it's called from get_next_fitting_tree()
    int move_to_next_tree();

    //sets tree and tree_id to the next fitting tree, returns 0 and .finished=false
    //returns 0 and sets .finished=true if nothing found
    //returns nonzero on error
    int get_next_fitting_tree();
    int set_tree_to_id(uint32_t tree_id);
    bool set_tree_to_id_and_check(uint32_t tree_id);

    //Checks the tree binary data at tdata w.r.t. to the sets and arrays given by begin_search() initially
    bool check_tree(void *tdata);

    int get_id_for(char *key_data, int key_size);
    int get_count_for(unsigned int q_id);
    bool has_id(char *key_data, int key_size);
    int set_tree_to_next_id(); 

};

#endif

