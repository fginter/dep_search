#include "fetch_lmdb.h"
#include <sstream>

int main() {
    LMDB_Fetch f;
    uint32_t sets[]={90696,20};
    uint32_t arrays[]={67,281};
    int len_sets=2;
    int len_arrays=2;
    uint32_t rarest=90696;
    std::cout << "Open errcode: " << f.open("500k_compact") << std::endl;
    f.begin_search(len_sets,len_arrays,sets,arrays,rarest);
    while (!f.finished) {
    	f.get_next_fitting_tree();
	std::cout << "Tree id " << f.tree_id << std::endl;
    }
    f.close();
}
