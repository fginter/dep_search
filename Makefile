TARGETS=db_util.so

.PHONY: setlib

all: setlib $(TARGETS)

setlib:
	$(MAKE) -C setlib

db_util.so: setlib db_util.pyx db_util.pxd setlib/tset.cpp setlib/tset.h
	python setup.py build_ext --inplace

clean:
	rm -f *.so
	$(MAKE) -C setlib clean



