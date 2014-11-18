#include <stdio.h>
#include "query_functions.h"

using namespace tset;

void pairing(TSet *index_set, TSet *other_set, TSetArray *mapping, bool negated) {
    TSet result(index_set->tree_length,0);
    for (int i=0;i<index_set->tree_length;i++) {
        if (index_set->has_item(i)) {
            mapping->get_set(i,&result);
            if (negated==true) {
                if (other_set->intersection_not_empty(&result)) {
                    index_set->delete_item(i);
                }

            }
            else {
                if (!other_set->intersection_not_empty(&result)) {
                    index_set->delete_item(i);
                }
            }
        }
    }

}
