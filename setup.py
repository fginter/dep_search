from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize(
           "example_queries.pyx",                 # our Cython source
           sources=["query_functions.cpp"],  # additional source file(s)
           language="c++",             # generate C++ code
      ))

setup(ext_modules = cythonize(
          "db_util.pyx",                 # our Cython source
          language="c++",             # generate C++ code
          libraries=["sqlite3"],
     ))


