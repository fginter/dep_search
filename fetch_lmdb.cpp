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
        int cursor_load_tree();
        bool check_current_tree(uint32_t *sets, int len_sets, uint32_t *arrays, int len_arrays);
        uint32_t*  get_first_fitting_tree();//uint32_t rarest);
        uint32_t* get_next_fitting_tree();//uint32_t rarest);
        void* tree_get_first_fitting_tree();//uint32_t rarest);
        void* tree_get_next_fitting_tree();//uint32_t rarest);
        void set_set_map_pointers(int ls, int la, uint32_t *lsets, uint32_t* larrays, uint32_t rarest);
};

bool prefix(const char *pre, const char *str){
    return strncmp(pre, str, strlen(pre)) == 0;
}

int print_sets_and_arrays(Tree *t){

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
           std::cout << "\n";
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

int LMDB_Fetch::cursor_get_next_tree(unsigned int flag){

    int err = cursor_get_next_tree_id(flag);
    if (err == 0){
        //t_key.mv_size = sizeof(uint32_t);
        //t_key.mv_data = (uint32_t*)c_key.mv_data;
        //err = mdb_get(txn, db_tdata, &t_key, &t_data);
        err = cursor_load_tree();
        if (err!=0){
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
    tree->deserialize(t_data.mv_data);
    for(int i=0; i<len_sets;i++){
        if (binary_search(*sets, tree->set_indices, tree->set_indices+tree->set_count) == 0){
            //std::cout << *sets << "-set\n";
            //print_sets_and_arrays(tree);
            return false;
        }
        sets++;
    }
    for(int i=0; i<len_arrays;i++){
        if (binary_search(*arrays, tree->map_indices, tree->map_indices+tree->map_count) == 0){
            //std::cout << *arrays << "-map\n";
            //print_sets_and_arrays(tree);
            return false;
        }
        arrays++;
    }
    return true;
}

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
       if(err!=0){
           return NULL;
           break;
       }
    if (err == 0){
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
   //Find next fitting
   //   if not found return like -1
   int err = this->set_search_cursor_key(this->rarest);
   while(true){
    //int err = fetch->set_search_cursor_key(rarest);
    if (err == 0){
       if(this->check_current_tree(&this->sets[0], this->len_sets, &this->arrays[0], this->len_arrays)){
           return (uint32_t*)this->c_key.mv_data;
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



int main(int argc, char* argv[]){

    int len_sets = 0;
    int len_arrays = 0;
    char* env_name;

    for(int i=0; i < argc;i++){
        if (prefix("-s", argv[i])){
            len_sets++;}
        if (prefix("-m", argv[i])){
            len_arrays++;}
    }
    //int *sets = malloc(set_count*sizeof(uint32_t));
    //int *arrays = malloc(map_count*sizeof(uint32_t));
    uint32_t arrays[len_arrays];
    uint32_t sets[len_sets];
    uint32_t *arr;
    uint32_t *sts;
    arr = arrays;
    sts = sets;

    for(int i=0; i < argc;i++){

        //std::cout << argv[i] << "\n";
        if (prefix("-m", argv[i])){
            *arr = (uint32_t)atoi(argv[i]+2);
            arr++;
        }
        if (prefix("-s", argv[i])){
            *sts = (uint32_t)atoi(argv[i]+2);
            /*
            std::cout << "atoi-x" << (uint32_t)atoi(argv[i]+2) << "\n";
            std::cout << "atoi-y" << (*(uint32_t*)sts) << "\n";
            std::cout << "atoi-y" << ((uint32_t)(uint32_t*)sts) << "\n";
            */
            sts++;
        }
        if (prefix("-e", argv[i])){

            env_name = (argv[i]+2);
        }

    }




    //Let us open up the database
    LMDB_Fetch* fetch = new LMDB_Fetch();
    //Let's open our little environment, 'ebin'
    fetch->open_env("ebin");
    //Now with the env opened, let's open out two databases and open transactions for both of them
    fetch->start_transaction();
    //Get all the tree_ids
    //uint32_t sets[2] = {4, 7}; 
    //uint32_t arrays[1] = {9};
    //int len_sets = 2;
    //int len_arrays = 1;
    uint32_t rarest = *sets;
    Tree *t;
    t = new Tree();

    std::cout << "AR" << arrays[0] << "\n";
    std::cout << "STS" << sets[0] << "\n";

    uint32_t* st;
    st = &sets[0];
    std::cout << "ERC " << *(st+1) << "\n";




    //put sets and arrays into place
    /*
    uint32_t * target;
    fetch->set_set_map_pointers(len_sets, len_arrays, &sets[0],&arrays[0], rarest);
    target = fetch->get_first_fitting_tree();//rarest);
     if (target != NULL){
         std::cout <<"T"<< *target << "\n";
     }
     while(true){

     target = fetch->get_next_fitting_tree();//rarest);
     if (target != NULL){
         std::cout <<"T"<< *target << "\n";
         }
     else{
         break;

     }

     }


    */
    /*
    int err = fetch->set_search_cursor_key(rarest);
    if (err == 0){
       if(fetch->check_current_tree(&sets[0], len_sets, &arrays[0], len_arrays)){
           std::cout << *((uint32_t*)fetch->c_key.mv_data) << "\n";
       }else{
           //std::cout << *((uint32_t*)fetch->c_key.mv_data) << "!\n";
           //t->deserialize(fetch->t_data.mv_data);
           //print_sets_and_arrays(t);
       }
    }
    while (err == 0){
        err = fetch->cursor_get_next_tree(rarest);
        if (err==0){
           if(fetch->check_current_tree(&sets[0], len_sets, &arrays[0], len_arrays)){
               std::cout << *((uint32_t*)fetch->c_key.mv_data) << "\n";
           }else{

           //std::cout << *((uint32_t*)fetch->c_key.mv_data) << "!\n";
           //t->deserialize(fetch->t_data.mv_data);
           //print_sets_and_arrays(t);

           }
       }
    }*/
}



