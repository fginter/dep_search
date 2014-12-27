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

//binary search
//Returns pointer to the occurrence of what in the array [beg,...,end] if found, or NULL otherwise
uint32_t *binary_search(uint32_t what, uint32_t *beg, uint32_t *end) {
    uint32_t *mid;
    do {
	mid=beg+(end-beg)/2; //pointer to the middle
	if (*mid == what) {
	    return mid;
	}
	else if (*mid < what) { //start one to the right of mid
	    beg=mid+1;
	}
	else { //*mid > what, end one to the left of mid
	    end=mid-1;
	}
    } while (beg<=end);
    return NULL;
}

void Tree::deserialize(void *serialized_data) {
    tree_length=((uint16_t *)serialized_data)[0];
    array_length=(tree_length/sizeof(uint64_t)+1); //how many uint64_t's are needed to store the set?
    set_count=*(&tree_length+1);
    map_count=*(&tree_length+2);
    set_indices=(uint32_t *)(void*)(&map_count+1);
    map_indices=set_indices+set_count;
    map_lengths=(uint16_t *)(void*)(map_indices+map_count);
    set_data=(uint64_t *)(void *)(map_lengths+map_count);
    serialized_map_data=(void*)(set_data+array_length*set_count);
    map_data_pointer_byte_offsets[0]=0; //serialized maps are of varying lengths - accumulate here byte offset for their data
    for (int i=1; i<map_count; i++) {
	map_data_pointer_byte_offsets[i]=map_data_pointer_byte_offsets[i-1]+map_lengths[i-1];
    }
    void *zipped_block=(void*) ((map_count==0) ? serialized_map_data : ((char *)serialized_map_data)+map_data_pointer_byte_offsets[map_count-1]+map_lengths[map_count-1]);
    zipped_tree_text_length=*((uint16_t *)(zipped_block));
    zipped_tree_text=(void*)((char*)zipped_block+sizeof(uint16_t));
}

int Tree::fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count) {
    //set_pos -> index into set_pointers etc, runs in range [0,count)
    for (int set_pos=0; set_pos<count; set_pos++) {
	if (set_types[set_pos]==1) { //we are looking for a tset
	    TSet *tset=(TSet *) set_pointers[set_pos]; //current set
	    uint32_t* p=binary_search(indices[set_pos],set_indices,set_indices+set_count-1); //return NULL, or a pointer to indices
	    if (p==NULL && !optional[set_pos]) { //didn't find it and it was compulsory...
		return 1;
	    }
	    else if (p==NULL) { //didn't find it and it was not compulsory
		tset->set_length(tree_length);
		tset->erase();
	    }
	    else {
		//got a set!
		int set_index=p-set_indices; //binary search returns a pointer, so p-set_indices is the index of the item found
		tset->deserialize(tree_length,(const void*)&set_data[set_index*array_length]);
	    }
	}
	else if (set_types[set_pos]==2) { //we are looking for an array
	    TSetArray *tsetarray=(TSetArray *) set_pointers[set_pos]; //current set
	    uint32_t* p=binary_search(indices[set_pos],map_indices,map_indices+map_count-1); //return NULL, or a pointer to indices
	    if (p==NULL && !optional[set_pos]) { //didn't find it and it was compulsory...
		return 1;
	    }
	    else if (p==NULL) { //didn't find it and it was not compulsory
		tsetarray->set_length(tree_length);
		tsetarray->erase();
	    }
	    else {
		//got an array!
		int set_index=p-map_indices; //binary search returns a pointer, so p-set_indices is the index of the item found
		tsetarray->deserialize(tree_length,(void*)((char*)serialized_map_data+map_data_pointer_byte_offsets[set_index]),map_lengths[set_index]);
	    }
	}
    }
    return 0;
}
		
		    
		
