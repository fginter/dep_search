#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include "tree_lmdb.h"

mode_t get_mode() {
  mode_t current_mask=umask(0);
  umask(current_mask);
  return 0777 & ~current_mask;
}

void report(const char* msg, int err) {
  if (err!=0) {
    printf("%s: %s\n",msg,mdb_strerror(err));
  }
  else {
    printf("%s: OK\n",msg);
  }
}

LMDB::LMDB() {
    op_count=0;
}


int LMDB::open_db(const char *name) {
    int err=mdb_env_create(&mdb_env);
    if (err) {
	report("Failed to create an environment:",err);
	return err;
    }
    err=mdb_env_set_mapsize(mdb_env,1024L*1024L*1024L*1024L); //1TB max DB size
    if (err) {
	report("Failed to set env size:",err);
	return err;
    }
    err=mdb_env_set_maxdbs(mdb_env,3); //to account for the three open databases
    if (err) {
	report("Failed to set maxdbs:",err);
	return err;
    }
    err=mdb_env_open(mdb_env,name,MDB_NOTLS|MDB_NOLOCK|MDB_NOMEMINIT,get_mode());
    if (err) {
	report("Failed to open the environment:",err);
	return err;
    }
    return 0;
}

int LMDB::start_transaction() {
    op_count=0;
    int err=mdb_txn_begin(mdb_env,NULL,0,&txn);
    if (err) {
	report("Failed to begin a transaction:",err);
	return err;
    }
    err=mdb_dbi_open(txn,"k2t",MDB_DUPSORT|MDB_DUPFIXED|MDB_INTEGERDUP|MDB_CREATE,&db_k2t); //Arbitrary key, but integer tree numbers as values
    if (err) {
	report("Failed to open k2t DBI:",err);
	return err;
    }
    err=mdb_dbi_open(txn,"f2s",MDB_INTEGERKEY|MDB_CREATE,&db_f2s); //Zero-length value, feature_sentenceid fused as the key
    if (err) {
	report("Failed to open f2s DBI:",err);
	return err;
    }
    err=mdb_dbi_open(txn,"tdata",MDB_INTEGERKEY|MDB_CREATE,&db_tdata); 
    if (err) {
	report("Failed to open tdata DBI:",err);
	return err;
    }
    return 0;
}

int LMDB::restart_transaction() {
    //Call this function every now and then to make sure our transaction doesn't grow too big
    if (op_count<10000000) { //not enough operations, keep going
	return 0;
    }
    int err=mdb_txn_commit(txn);
    if (err) {
	report("Failed to commit, that's bad!:",err);
	return err;
    }
    return start_transaction(); //...and launch a new one...
}

int LMDB::finish_indexing() {
    int err=mdb_txn_commit(txn);
    if (err) {
	report("Failed to commit, that's bad!:",err);
	return err;
    }
    return 0;
}


int LMDB::store_tree_flag(unsigned int tree_id, unsigned int flag_number) {
    MDB_val key;
    MDB_val value;
    uint64_t k=(((uint64_t)flag_number)<<32)+tree_id; //We better hope neither is bigger than 32bits!
    int err;
    key.mv_size=sizeof(uint64_t); //64bit
    value.mv_size=0;
    value.mv_data=NULL;
    key.mv_data=&k;
    err=mdb_put(txn,db_f2s,&key,&value,0);
    if (err) {
	report("Failed to put(), that's bad!:",err);
	return err;
    }
    op_count++;
    return restart_transaction();
}

int LMDB::store_tree_data(unsigned int tree_id, void *t_data, int size) {
    MDB_val key;
    MDB_val value;
    key.mv_size=sizeof(uint32_t);
    key.mv_data=&tree_id;
    value.mv_size=size;
    value.mv_data=t_data;
    int err=mdb_put(txn,db_tdata,&key,&value,0);
    if (err) {
	report("Failed to put(), that's bad!:",err);
	return err;
    }
    op_count++;
    return restart_transaction();
}

int LMDB::store_key_tree(unsigned int tree_id, void *key_data, int key_size) {
    MDB_val key;
    MDB_val value;
    key.mv_size=key_size;
    key.mv_data=&key_data;
    value.mv_size=sizeof(uint32_t);
    value.mv_data=&tree_id;
    int err=mdb_put(txn,db_tdata,&key,&value,0);
    if (err) {
	report("Failed to put(), that's bad!:",err);
	return err;
    }
    op_count++;
    return restart_transaction();
}
