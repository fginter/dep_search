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
    tree_length=((uint16_t *)serialized_data)[0]; //first 2B is tree length
    array_length=(tree_length/sizeof(uint64_t)+1); //how many uint64_t's are needed to store the set?
    set_count=*(&tree_length+1); //next 2B is set_count
    map_count=*(&tree_length+2); //next 2B
    set_indices=(uint32_t *)(void*)(&map_count+1); //after this we have an array of 32bit set indices (TODO: would 16bit do?)
    map_indices=set_indices+set_count; //after which we have an array of 32bit map indices (TODO: would 16bit do?)
    map_lengths=(uint16_t *)(void*)(map_indices+map_count); //next we have the map lengths
    set_data=(uint64_t *)(void *)(map_lengths+map_count); //and set data
    serialized_map_data=(void*)(set_data+array_length*set_count); //and map data
    map_data_pointer_byte_offsets[0]=0; //serialized maps are of varying lengths - accumulate here byte offset for their data
    for (int i=1; i<map_count; i++) {
	map_data_pointer_byte_offsets[i]=map_data_pointer_byte_offsets[i-1]+map_lengths[i-1];
    }
    //skip over the map data and you get the zipped block
    void *zipped_block=(void*) ((map_count==0) ? serialized_map_data : ((char *)serialized_map_data)+map_data_pointer_byte_offsets[map_count-1]+map_lengths[map_count-1]);
    zipped_tree_text_length=*((uint16_t *)(zipped_block)); //it starts with its length
    zipped_tree_text=(void*)((char*)zipped_block+sizeof(uint16_t)); //and here's the zipped data
}

/*
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
		
		    
		
*/
