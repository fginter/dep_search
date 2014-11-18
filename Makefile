TARGETS=db_util.so example_queries.so

.PHONY: setlib

all: setlib $(TARGETS)

setlib:
	$(MAKE) -C setlib

db_util.so: db_util.pyx db_util.pxd setlib/tset.cpp setlib/tset.h
	python setup.py build_ext --inplace

example_queries.so: example_queries.pyx setlib/tset.cpp setlib/tset.h query_functions.cpp query_functions.h
	python setup.py build_ext --inplace

clean:
	rm -rf $(TARGETS)
	$(MAKE) -C setlib clean



