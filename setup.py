from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize(
          "db_util.pyx",                 # our Cython source
          language="c++",             # generate C++ code
          libraries=["sqlite3"],
     ))

setup(ext_modules = cythonize(
          "py_tree_lmdb.pyx",                 # our Cython source
          language="c++",             # generate C++ code
          sources=["tree_lmdb.cpp"]
     ))


