TARGETS=db_util.so py_tree_lmdb.so test

.PHONY: setlib

all: setlib $(TARGETS)

setlib:
	$(MAKE) -C setlib

db_util.so: setlib db_util.pyx db_util.pxd setlib/tset.cpp setlib/tset.h
	python setup.py build_ext --inplace

py_tree_lmdb.so: py_tree_lmdb.pyx py_tree_lmdb.pxd tree_lmdb.cpp tree_lmdb.h Makefile setup.py
	python setup.py build_ext --inplace

test: test.cpp tree_lmdb.cpp
	g++ -o test test.cpp tree_lmdb.cpp setlib/tset.cpp -llmdb

clean:
	rm -f *.so
	$(MAKE) -C setlib clean



