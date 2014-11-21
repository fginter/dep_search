import sys
from distutils.core import setup
from Cython.Build import cythonize
setup(ext_modules = cythonize(
        sys.argv[1]+".pyx",                 # our Cython source
        language="c++",             # generate C++ code
        ),script_args=["build_ext","--inplace"])
