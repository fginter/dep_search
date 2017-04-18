Requirements
============

The toolkit requires libsqlite3 development files, header files and static libraries for Python and Cython.

For Ubuntu, these are available as following packages:  
libsqlite3-dev  
python-dev  
cython  

The webUI requires python library flask and for uWSGI based deployment uwsgi & uwsgi-python plugin.

For Ubuntu, these are available as:  
    uwsgi  
    uwsgi-python-plugin  
    python-flask  

Installation
============

    git clone https://github.com/fginter/dep_search.git   
    cd dep_search
    git submodule init   
    git submodule update   
    make   

Command line usage
==================

Indexing data
-------------

The data needs to be indexed before querying. Data is stored as sqlite databeses and the data is expected to be to be in conllu-format.

The data will be indexed by build_index.py which expects the conllu data in standard input and creates the required databases.

The following command will index the first 100000 trees from a conllu file fi-ud-train.conllu and save it into a folder fi.data  

    cat ../UD_Finnish/fi-ud-train.conllu | python build_index.py --max 100000 -d fi.data  

Querying the data
-----------------

The data can be queried in command line using using query.py  

The following command will query perform a query '_ <nsubj _' of the trees indexed in database(s) located in folder fi-data, the result will be outputted in standard output in conll-u format. As --max argument is set only the first 50 hits will be returned. Setting --max 0 will remove the restrictions. 

    python query.py '_ <nsubj' --max 50 -d './fi-data/*.db'  


Web Interface
=============

The web interface of `dep_search` has two components. An API which is part of the dep_search codebase (`webapi` directory), and a browseable web interface which can be tested live at http://bionlp-www.utu.fi/dep_search. The code for the web interface is a separate project released at https://github.com/fginter/dep_search_serve.

The instructions for setting everything up are here: https://fginter.github.io/dep_search/

Query Language
==============

Query language is described in detail at: http://bionlp.utu.fi/searchexpressions-new.html

