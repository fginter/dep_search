#ifndef __tset_h__
#define __tset_h__

#include <string.h>

typedef unsigned long aelem;

namespace tset {
class TSet {
    public:
        int tree_length;
        int array_len;
        aelem *bitdata;
        aelem enum_state; // integer with already enumerated 1s removed
        size_t enum_state_idx; // index in the array
        bool delete_memory; // Have we allocated bitdata ourselves?

        TSet(int tree_length);
        TSet(int tree_length, aelem *bitdata);
        ~TSet();
        void intersection_update(TSet *other);
        void union_update(TSet *other);
        void minus_update(TSet *other);
        void add_item(int item);
        bool has_item(int item);
        void erase();
        void copy(TSet *other);
        bool next_item(TSet *result);
        void start_iteration();
        bool is_empty();
        bool intersection_not_empty(TSet *other);
        void delete_item(int item);
        char* get_data_as_char(int *size);
        void deserialize(const void *data);
        void deserialize(int s_length, const void *data);
        void fill_ones();
        void set_length(int tree_length);
        void complement();
	void print_set();

};

class TSetArray {
    public:
        int tree_length;
        int array_len;
        aelem *bitdata;

        TSetArray(int length);
        void intersection_update(TSetArray *other);
        void union_update(TSetArray *other);
        void minus_update(TSetArray *other);
////        void add_item(int item);
////        bool has_item(int item);
        void erase();
        void copy(TSetArray *other);
////        bool next_item(TSet *result);
////        void start_iteration();
        void get_set(int index, TSet *result);
        void deserialize(const void *data, int size);
        void deserialize(int s_length, const void *data, int size);
        void set_length(int tree_length);
        void make_lin(int window);
        void make_lin_2(int window, int begin);
        void filter_direction(bool direction);
	void print_array();
};
}

#endif

