from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize(
           "example_queries.pyx",                 # our Cython source
           sources=["query_functions.cpp","setlib/tset.cpp"],  # additional source file(s)
           language="c++",             # generate C++ code
          include_dirs=["setlib",]
      ))

setup(ext_modules = cythonize(
          "db_util.pyx",                 # our Cython source
          language="c++",             # generate C++ code
          sources=["setlib/tset.cpp"],
          libraries=["sqlite3"],
          include_dirs=["setlib"],
     ))


