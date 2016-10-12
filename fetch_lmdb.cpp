#include "lmdb.h"
#include <iostream>
#include <stdint.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sstream>
#include "tree_lmdb.h"
#include <stdlib.h>
#include <iomanip>
#include "fetch_lmdb.h"


LMDB_Fetch::LMDB_Fetch(){

    tree = new Tree();
}


/* Initializes the search */
// Returns zero and sets .finished=True if not a single key hit found
// Returns zero and sets .finished=False if found
// Returns nonzero on error
int LMDB_Fetch::begin_search(int len_sets, int len_arrays, uint32_t *lsets, uint32_t *larrays, uint32_t rarest) {

    MDB_val key,val;
    uint32_t k=rarest;
    int err;
    
    key.mv_size=sizeof(k);
    key.mv_data=&k;
    val.mv_size=0;
    val.mv_data=NULL;

    finished=false;
    this->rarest = rarest;
    this->sets = lsets;
    this->arrays= larrays;
    this->len_sets=len_sets;
    this->len_arrays=len_arrays;

    err=mdb_cursor_get(k2t_cursor,&key,&val,MDB_SET);
    if (!err) {
	return err; //0
    }
    else if (err==MDB_NOTFOUND) {
	// Not a single instance in the db!
	std::cout << "Initial get failed" << std::endl;
	finished=true;
	return 0;
    }
    else {
	report("Cursor_get failed",err);
	return err;
    }
}

// Positions the k2t cursor on the next tree for the "rarest" key
// returns 0 and sets .finished=False if found
// returns 0 and sets .finished=True if not found
// returns nonzero on error
int LMDB_Fetch::move_to_next_tree() {
    MDB_val key,val;
    uint32_t k=rarest;
    int err;
    key.mv_size=sizeof(uint32_t);
    key.mv_data=&k;
    val.mv_size=0;
    val.mv_data=NULL;

    if (finished) {
	return 0;
    }
    
    err=mdb_cursor_get(k2t_cursor,&key,&val,MDB_NEXT_DUP);
    if (!err) {
	return 0;
    }
    else if (err==MDB_NOTFOUND) {
	std::cout << "Next not found, done" << err << std::endl;
	finished=true;
	return 0;
    }
    else {
	report("Cursor next failed for k2t",err);
	return err;
    }
}

//sets tree and tree_id to the next fitting tree, returns 0 and .finished=false
//returns 0 and sets .finished=true if nothing found
//returns nonzero on error
int LMDB_Fetch::get_next_fitting_tree() {
    //this assumes that you ran begin_search() if this is the first call
    //so the k2t cursor is pointing at a tree not seen so far
    MDB_val key,tree_id_val,t_val;
    int err;
    while (!finished) {
	err=mdb_cursor_get(k2t_cursor,&key,&tree_id_val,MDB_GET_CURRENT);
	if (err || (*((uint32_t*)key.mv_data)!=rarest)) {
	    std::cerr << "In get_next_fitting_tree key is " << *((uint32_t*)key.mv_data) << " but rarest is set to " << rarest << std::endl;
	    report("Failed to retrieve from k2t",err);
	    return err;
	}
	//Now tree_id_val holds the tree id of the tree we want, so let's grab it
	err=mdb_cursor_get(tdata_cursor,&tree_id_val,&t_val,MDB_SET_KEY);
	if (err) {
	    report("Failed to retrieve tree from tdata",err);
	    return err;
	}
	//Now t_val points to serialized tree data
	//Does it have all we need?
	if (check_tree(t_val.mv_data)) { //YES!
	    tree_id=*((uint32_t*)tree_id_val.mv_data);
	    //the tree itself is now deserialized in tree, so that should be okay
	    return 0;
	}
	move_to_next_tree();
    }
    //Ran out of trees, ie found nothing
    return 0; //finished is false now, so that is our signal
}

	
	
/* Closes everything */
void LMDB_Fetch::close() {
    mdb_cursor_close(k2t_cursor);
    mdb_cursor_close(tdata_cursor);
    mdb_txn_abort(txn);
    mdb_env_close(mdb_env);
}

/* Opens everything needed */
int LMDB_Fetch::open(const char *name) {
    int err;
    err=mdb_env_create(&mdb_env);
    if (err) {
        report("Failed to create an environment:",err);
        return err;
    }
    err=mdb_env_set_mapsize(mdb_env,1024L*1024L*1024L*1024L); //1TB max DB size
    if (err) {
        report("Failed to set env size:",err);
        return err;
    }
    err=mdb_env_set_maxdbs(mdb_env,2); //to account for the two open databases
    if (err) {
        report("Failed to set maxdbs:",err);
        return err;
    }
    err=mdb_env_open(mdb_env,name,MDB_NOTLS|MDB_NOLOCK|MDB_NOMEMINIT,get_mode());
    if (err) {
        report("Failed to open the environment:",err);
        return err;
    }
    err=mdb_txn_begin(mdb_env,NULL,0,&txn);
    if (err) {
        report("Failed to begin a transaction:",err);
        return err;
    }
    err=mdb_dbi_open(txn,"k2t",MDB_INTEGERKEY|MDB_DUPSORT|MDB_DUPFIXED|MDB_INTEGERDUP,&db_k2t); //integer key, integer tree numbers as values
    if (err) {
        report("Failed to open k2t DBI:",err);
        return err;
    }
    err=mdb_dbi_open(txn,"tdata",MDB_INTEGERKEY,&db_tdata); //integer key, integer tree numbers as values
    if (err) {
        report("Failed to open k2t DBI:",err);
        return err;
    }
    err = mdb_cursor_open(txn, db_k2t, &k2t_cursor);
    if (err){
        report("Failed to open k2t cursor", err);
    }
    err = mdb_cursor_open(txn, db_tdata, &tdata_cursor);
    if (err){
        report("Failed to open tdata cursor", err);
    }
    return 0;
}



//Given a pointer to tree data, check that it has all the required sets
bool LMDB_Fetch::check_tree(void *tree_data) {
    tree->deserialize(tree_data);
    for(int i=0; i<len_sets;i++){
        if (binary_search(sets[i], tree->set_indices, tree->set_indices+tree->set_count) == 0){
            return false;
        }
        sets++;
    }
    for(int i=0; i<len_arrays;i++){
        if (binary_search(arrays[i], tree->map_indices, tree->map_indices+tree->map_count) == 0){
            return false;
        }
    }
    return true;
}


