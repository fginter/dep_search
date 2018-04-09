from distutils.core import setup, Extension
from Cython.Build import cythonize

setup(
     ext_modules=cythonize(
          Extension(
               "db_util",
               ["db_util.pyx"],
               language="c++",
               libraries=["sqlite3"],
          )
     )
)
