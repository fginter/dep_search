#include "fetch_lmdb.h"
#include <sstream>

int main() {
    LMDB_Fetch f;
    uint32_t sets[0];
    uint32_t arrays[]={41};
    int len_sets=0;
    int len_arrays=1;
    uint32_t rarest=41;
    std::cout << "Open errcode: " << f.open("50k") << std::endl;
    f.begin_search(len_sets,len_arrays,sets,arrays,rarest);
    while (!f.finished) {
    	f.get_next_fitting_tree();
	std::cout << "Tree id " << f.tree_id << std::endl;
    }
    f.close();
}

    
