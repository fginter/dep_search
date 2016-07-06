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
        MDB_txn *tdata_txn;
        MDB_txn *k2t_txn;
        MDB_txn *txn;
        MDB_dbi db_f2s; //Database mapping arbitrary keys to tree number (which is an integer). Allows duplication, sorts the tree numbers.
        MDB_dbi db_k2t; //Database mapping arbitrary keys to tree number (which is an integer). Allows duplication, sorts the tree numbers.
        MDB_dbi db_tdata; //Database storing the full tree data indexed by tree number (32-bit)
        MDB_cursor *cursor; //The cursor to be used

        MDB_val c_key, c_data;
        MDB_val t_key, t_data;
        Tree *tree;

        uint32_t* sets;
        uint32_t* arrays;
        int len_sets;
        int len_arrays;
        int rarest;

        LMDB_Fetch();
        int open_env(const char *name);
        int open_dbs();
        int start_transaction();
        int set_search_cursor_key(unsigned int flag);
        int cursor_get_next_tree_id(unsigned int flag);
        int cursor_get_next_tree(unsigned int flag);
        uint32_t* get_current_tree_id();
        int cursor_load_tree();
        bool check_current_tree(uint32_t *sets, int len_sets, uint32_t *arrays, int len_arrays);

        uint32_t* get_first_fitting_tree();//uint32_t rarest);
        uint32_t* get_next_fitting_tree();//uint32_t rarest);
        void set_set_map_pointers(int ls, int la, uint32_t *lsets, uint32_t* larrays, uint32_t rarest);
        void get_a_treehex(uint32_t tree_id);

};

bool prefix(const char *pre, const char *str);
int print_sets_and_arrays(Tree *t);
