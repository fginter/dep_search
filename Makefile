TARGETS=test_fetch_lmdb
#py_tree_lmdb.so

.PHONY: setlib

all: setlib $(TARGETS)

test_fetch_lmdb: test_fetch_lmdb.cpp fetch_lmdb.h setlib/tset.h tree_lmdb.cpp fetch_lmdb.cpp
	g++ test_fetch_lmdb.cpp fetch_lmdb.cpp setlib/tset.cpp tree_lmdb.cpp -llmdb -o test_fetch_lmdb

setlib:
	$(MAKE) -C setlib

db_util.so: setlib db_util.pyx db_util.pxd setlib/tset.cpp setlib/tset.h
	python setup.py build_ext --inplace

py_tree_lmdb.so: py_tree_lmdb.pyx py_tree_lmdb.pxd fetch_lmdb.cpp store_lmdb.cpp tree_lmdb.cpp tree_lmdb.h setlib/tset.h Makefile setup.py
	python setup.py build_ext --inplace

test: test.cpp tree_lmdb.cpp
	g++ -o test test.cpp tree_lmdb.cpp setlib/tset.cpp -llmdb

clean:
	rm -f *.so
	$(MAKE) -C setlib clean



