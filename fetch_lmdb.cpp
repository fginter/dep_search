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
        int close_env();

        int start_transaction();
        int set_search_cursor_key(unsigned int flag);
        int cursor_get_next_tree_id(unsigned int flag);
        int cursor_get_next_tree(unsigned int flag);
        int cursor_load_tree();
        uint32_t* get_current_tree_id();
        bool check_current_tree(uint32_t *sets, int len_sets, uint32_t *arrays, int len_arrays);
        uint32_t*  get_first_fitting_tree();//uint32_t rarest);
        uint32_t* get_next_fitting_tree();//uint32_t rarest);
        void* tree_get_first_fitting_tree();//uint32_t rarest);
        void* tree_get_next_fitting_tree();//uint32_t rarest);
        void set_set_map_pointers(int ls, int la, uint32_t *lsets, uint32_t* larrays, uint32_t rarest);
        std::string hexStr(unsigned char* data, int len);
        void get_a_treehex(uint32_t tree_id);
};

bool prefix(const char *pre, const char *str){
    return strncmp(pre, str, strlen(pre)) == 0;
}

int print_sets_and_arrays(Tree *t){

           std::cout << "SETS and Arrays" << "\n";

           std::cout << t->set_count << "\n";
           for(int i=0;i<t->set_count;i++){
               //
               std::cout << *(t->set_indices + i) << ";";
           }
           std::cout << "\n";

           for(int i=0;i<t->map_count;i++){
               //
               std::cout << *(t->map_indices + i) << ";";
           }
           std::cout << "\nEND\n";
}

LMDB_Fetch::LMDB_Fetch(){

    tree = new Tree();
}


void LMDB_Fetch::set_set_map_pointers(int ls, int la, uint32_t *lsets, uint32_t *larrays, uint32_t rarest){


        this->rarest = rarest;
        this->sets = lsets;
        this->arrays= larrays;
        this->len_sets=ls;
        this->len_arrays=la;

        std::cout << "sets" << *((uint32_t*)this->sets) << "\n";
        //this->arrays= larrays[0];
        std::cout << "arrays" << *((uint32_t*)this->arrays) << "\n";
        this->len_sets=ls;
        this->len_arrays=la;

}


//The END

int LMDB_Fetch::close_env() {

    //Something here fails, and it fucking sucks!

    /*
    std::cout << "close_env\n";
    std::cout << "0\n";

    mdb_cursor_close(cursor);
    std::cout << "1\n";

    std::cout << "2\n";
    mdb_txn_abort(k2t_txn);
    mdb_txn_abort(tdata_txn);
    //mdb_txn_abort(txn);
    std::cout << "2.5\n";
    //mdb_dbi_close(mdb_env, db_k2t);
    //mdb_dbi_close(mdb_env, db_f2s);
    //mdb_dbi_close(mdb_env, db_tdata);
    std::cout << "3\n";
    //Fuck you: *** Error in `python': double free or corruption (!prev): 0x00000000017ecc90 ***
    */
    mdb_env_close(mdb_env);

    /*
        MDB_env *mdb_env;
        MDB_txn *tdata_txn;
        MDB_txn *k2t_txn;
        MDB_txn *txn;
        MDB_dbi db_f2s; //Database mapping arbitrary keys to tree number (which is an integer). Allows duplication, sorts the tree numbers.
        MDB_dbi db_k2t; //Database mapping arbitrary keys to tree number (which is an integer). Allows duplication, sorts the tree numbers.
        MDB_dbi db_tdata; //Database storing the full tree data indexed by tree number (32-bit)
        MDB_cursor *cursor; //The cursor to be used
        */

}



//Thanks, Filip!
int LMDB_Fetch::open_env(const char *name) {
    int err=mdb_env_create(&mdb_env);
    if (err) {
        report("Failed to create an environment:",err);
        return err;
    }
    //std::cout << mdb_env;
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

//Thanks again, Filip!
int LMDB_Fetch::open_dbs(){

    int err=mdb_txn_begin(mdb_env,NULL,0,&k2t_txn);
    if (err) {
        report("Failed to begin a transaction:",err);
        return err;
    }
    err=mdb_dbi_open(k2t_txn,"k2t",MDB_DUPSORT|MDB_DUPFIXED|MDB_INTEGERDUP|MDB_CREATE,&db_k2t); //Arbitrary key, but integer tree numbers as values
    if (err) {
        report("Failed to open k2t DBI:",err);
        return err;
    }

    err=mdb_txn_begin(mdb_env,NULL,0,&tdata_txn);
    err=mdb_dbi_open(tdata_txn,"tdata",MDB_INTEGERKEY|MDB_CREATE,&db_tdata);
    if (err) {
        report("Failed to open tdata DBI:",err);
        return err;
    }
    return 0;
}


int LMDB_Fetch::start_transaction() {
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





int LMDB_Fetch::cursor_load_tree(){

    t_key.mv_size = sizeof(uint32_t);

    //std::cout << *((uint32_t*)c_key.mv_data) << "\n";

    t_key.mv_data = (uint32_t*)c_key.mv_data;
    int err = mdb_get(txn, db_tdata, &t_key, &t_data);
    return err;
}




uint32_t* LMDB_Fetch::get_current_tree_id(){

    return (uint32_t*)c_key.mv_data;
}


//std::string LMDB_Fetch::get_a_treehex(uint32_t tree_id){
void LMDB_Fetch::get_a_treehex(uint32_t tree_id){
    t_key.mv_size = sizeof(uint32_t);

    //std::cout << *((uint32_t*)c_key.mv_data) << "\n";

    t_key.mv_data = &tree_id;
    int err = mdb_get(txn, db_tdata, &t_key, &t_data);
    
    //alright, the tree pointer is now in t_data


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

    void * data = t_data.mv_data;
    //To get it out we need to get its size
    tree_length=((uint16_t *)data)[0]; //first 2B is tree length
    array_length=(tree_length/(sizeof(uint64_t)*8)+1); //how many uint64_t's are needed to store the set?
    set_count=((uint16_t *)data)[1]; //next 2B is set_count
    map_count=((uint16_t *)data)[2]; //next 2B
//    printf("Deserializer: %d %d %d ",tree_length,set_count,map_count);
    data=(void *)((char *)data+3*sizeof(uint16_t));

    //Okay, this far I get this!

    set_indices=(uint32_t *)(data); //after this we have an array of 32bit set indices (TODO: would 16bit do?)
    map_indices=set_indices+set_count; //after which we have an array of 32bit map indices (TODO: would 16bit do?)
    map_lengths=(uint16_t *)(void*)(map_indices+map_count); //next we have the map lengths



    //Wait, what why 64 bits?
    //Okay, this thing is fucked :/


    set_data=(uint64_t *)(uint16_t *)(void *)(map_lengths+map_count); //and set data
//    printf(" >%d< ",array_length*set_count*8);
    serialized_map_data=(void*)(set_data+array_length*set_count); //and map data

//    printf("[");
    if (map_count>0) {
	map_data_pointer_byte_offsets=new uint16_t[map_count];
	map_data_pointer_byte_offsets[0]=0; //serialized maps are of varying lengths - accumulate here byte offset for their data
//	printf(" %d/0",map_lengths[0]);
	for (int i=1; i<map_count; i++) {
	    map_data_pointer_byte_offsets[i]=map_data_pointer_byte_offsets[i-1]+map_lengths[i-1];
//	    printf(" %d/%d",map_lengths[i],map_data_pointer_byte_offsets[i]);
	}
    }



    //skip over the map data and you get the zipped block
    void *zipped_block=(void*) ((map_count==0) ? serialized_map_data : ((char *)serialized_map_data)+map_data_pointer_byte_offsets[map_count-1]+map_lengths[map_count-1]);
    zipped_tree_text_length=*((uint16_t *)(zipped_block)); //it starts with its length
//    printf("] %d\n",zipped_tree_text_length);
    zipped_tree_text=(void*)((char*)zipped_block+sizeof(uint16_t)); //and here's the zipped data



    std::cout << "\nTree Deserialized\nLen " << tree_length << "\nSet_Count " << set_count << "\nMap_count " << map_count <<
    "\nzipped_len " << zipped_tree_text_length << "\n"; 


    //Print these now
    std::cout << "set_indices\n";
    for(int i=0; i<set_count; i++){
        std::cout << set_indices[i] << ";";
    }
    std::cout << "\n";
    std::cout << "map_indices\n";
    for(int i=0; i<map_count; i++){
        std::cout << map_indices[i] << ";";
    }
    std::cout << "\n";
    std::cout << "map_lengths\n";
    for(int i=0; i<map_count; i++){
        std::cout << map_lengths[i] << ";";
    }
    std::cout << "\n";

    //Correct so far!



    //Zipped data
    for(int i=0; i<200; i++){
        std::cout << ((char *)zipped_tree_text)[i]; 
    }
    std::cout << "\n";
    //return err;
}




int LMDB_Fetch::cursor_get_next_tree(unsigned int flag){

    int err = cursor_get_next_tree_id(flag);
    if (err == 0){
        //report("cursor_get_next_tree.cursor_get_next_tree_id:",err);
        //t_key.mv_size = sizeof(uint32_t);
        //t_key.mv_data = (uint32_t*)c_key.mv_data;
        //err = mdb_get(txn, db_tdata, &t_key, &t_data);
        err = cursor_load_tree();
        if (err!=0){
            //report("cursor_get_next_tree.Cursor Load Tree:",err);
            return err;
            }
        }
    return err;
    }

int LMDB_Fetch::cursor_get_next_tree_id(unsigned int flag){

    int err = mdb_cursor_get(cursor, &c_key, &c_data, MDB_NEXT);
    if (err){
    report("Problems getting next tree_id", err);
    }

    if (*((uint32_t*)c_key.mv_data + 1) > flag){
        return -1;
    }

    return err;
}

//int LMDB_Fetch::check_tree(uint32_t** indexes, int size){
   //here I guess I'll use the binary tree search 
//}


int LMDB_Fetch::set_search_cursor_key(unsigned int flag){

    //c_key.mv_size=sizeof(uint32_t);
    //c_key.mv_data=&flag;
    //c_data.mv_size=sizeof(uint32_t);
    //c_data.mv_data=&flag;
    uint64_t k=(((uint64_t)flag)<<32);
    c_key.mv_size = sizeof(uint64_t);
    c_key.mv_data = &k;//(((uint64_t)flag)<<32);
    int err = mdb_cursor_open(txn, db_f2s, &cursor);
    if (err){
        report("Problems opening cursor!", err);
    }
    err = mdb_cursor_get(cursor, &c_key, &c_data, MDB_SET_RANGE);//MDB_SET_KEY);
    //err = mdb_cursor_get(cursor, &c_key, &c_data, MDB_GET_CURRENT);
    if (err){
        report("Problems pointing cursor!", err);
    }
    if (*((uint32_t*)c_key.mv_data + 1) > flag){
        return -1;
    }
    cursor_load_tree();
    return err;
}


bool LMDB_Fetch::check_current_tree(uint32_t *sets, int len_sets, uint32_t *arrays, int len_arrays){

    //hexStr(t_data.mv_data, t_data.mv_len);
    //std::cout << "<check current tree>\n";


    tree->deserialize(t_data.mv_data);
    //print_sets_and_arrays(tree);
    for(int i=0; i<len_sets;i++){
        if (binary_search(*sets, tree->set_indices, tree->set_indices+tree->set_count) == 0){
            //std::cout << *sets << " set to test\n";
            //std::cout << binary_search(*sets, tree->set_indices, tree->set_indices+tree->set_count) << "\n";
            return false;
        }
        sets++;
    }
    for(int i=0; i<len_arrays;i++){
        if (binary_search(*arrays, tree->map_indices, tree->map_indices+tree->map_count) == 0){
            //std::cout << *arrays << " map to test\n";
            //std::cout << binary_search(*arrays, tree->map_indices, tree->map_indices+tree->map_count) << "\n";
            return false;
        }
        arrays++;
    }
    return true;
}


/*
bool LMDB_Fetch::check_current_tree_supposed_working(uint32_t *sets, int len_sets, uint32_t *arrays, int len_arrays){

    //hexStr(t_data.mv_data, t_data.mv_len);
    std::cout << "HEX\n" << hexStr((unsigned char *)t_data.mv_data, 100) << "\n";


    tree->deserialize(t_data.mv_data);
    for(int i=0; i<len_sets;i++){
        if (binary_search(*sets, tree->set_indices, tree->set_indices+tree->set_count) == 0){
            std::cout << *sets << "-set\n";
            print_sets_and_arrays(tree);
            return false;
        }
        sets++;
    }
    for(int i=0; i<len_arrays;i++){
        if (binary_search(*arrays, tree->map_indices, tree->map_indices+tree->map_count) == 0){
            std::cout << *arrays << "-map\n";
            print_sets_and_arrays(tree);
            return false;
        }
        arrays++;
    }
    return true;
}
*/




//int get_first_fitting_tree(uint32_t rarest, uint32_t* compulsory_flags[], int size_flags){

    //Set cursor
    //Find next fitting
    //   if not found return like -1

//}
uint32_t* LMDB_Fetch::get_next_fitting_tree(){//uint32_t rarest){
   //int err = this->set_search_cursor_key(rarest);
   int err;
   while(true){
    //int err = fetch->set_search_cursor_key(rarest);
       err = this->cursor_get_next_tree(this->rarest);
       //std::cout << "get_next_ft.get_next_tree " << err << "\n"; 

       if(err!=0){
           return NULL;
           break;
       }
    if (err == 0){

       //std::cout << "check_tree" << this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays) << "\n";

       if(this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays)){
           return (uint32_t*)this->c_key.mv_data;
           break;
       }
       //err = this->cursor_get_next_tree(rarest);
       //if(err!=0){
       //    return NULL;
       //    break;
       }
    }

}
uint32_t* LMDB_Fetch::get_first_fitting_tree(){//uint32_t rarest){
   int err = this->set_search_cursor_key(rarest);
   //int err;
   while(true){
    //int err = fetch->set_search_cursor_key(rarest);
       err = this->cursor_get_next_tree(this->rarest);
       //std::cout << "get_next_ft.get_next_tree " << err << "\n"; 

       if(err!=0){
           return NULL;
           break;
       }
    if (err == 0){

       //std::cout << "check_tree" << this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays) << "\n";

       if(this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays)){
           return (uint32_t*)this->c_key.mv_data;
           break;
       }
       //err = this->cursor_get_next_tree(rarest);
       //if(err!=0){
       //    return NULL;
       //    break;
       }
    }

}


void* LMDB_Fetch::tree_get_next_fitting_tree(){//uint32_t rarest){
   //int err = this->set_search_cursor_key(rarest);
   int err;
   while(true){
    //int err = fetch->set_search_cursor_key(rarest);
       err = this->cursor_get_next_tree(this->rarest);
       if(err!=0){
           return NULL;
           break;
       }
    if (err == 0){
       if(this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays)){
           return (void*)this->tree;//t_data.mv_data;
           break;
       }
       //err = this->cursor_get_next_tree(rarest);
       //if(err!=0){
       //    return NULL;
       //    break;
       }
    }

}
void* LMDB_Fetch::tree_get_first_fitting_tree(){//uint32_t rarest){
   //Find next fitting
   //   if not found return like -1
   int err = this->set_search_cursor_key(this->rarest);
   while(true){
    //int err = fetch->set_search_cursor_key(rarest);
    if (err == 0){
       if(this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays)){
           return (void*)this->tree;//this->t_data.mv_data;
           break;
       }
       err = this->cursor_get_next_tree(this->rarest);
       

       if(err!=0){
           return NULL;
           break;
       }
    }

}
}



std::string LMDB_Fetch::hexStr(unsigned char* data, int len)
{
    std::stringstream ss;
    ss << std::hex;
    for(int i=0;i<len;++i)
        ss << std::setw(2) << std::setfill('0') << (int)data[i];
    return ss.str();
}






