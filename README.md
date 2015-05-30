Requirements
============

The toolkit requires libsql3 development files, header files and static libraries for Python and Cython.

For Ubuntu, these are available as following packages:  
libsql3-dev  
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

WebUI
=====

Web based UI for the query system provides a nice way to query the data and it can be deployed locally or as a web service. It is a python flask app and it uses brat for visualization.

Setting Up
----------

### Set up corpora

The webUi expects two files describing the corpora used for the search.  
The files are corpora.json and available_corpora.json. The corpora.json describes
the locations and names for indexed data. While available_corpora.json lists
the order of the corpora and which of them are available for query.

Corpora.json file is a dictionary in json format, where key is the name of the data and
value is the folder with the database files.  

An example corpora.json could look like this:  
{   
  "Finnish": "/mnt/data/dep_search/Finnish.data",   
  "English": "/mnt/data/dep_search/English.data",   
  "Czech": "/mnt/data/dep_search/Czech.data"   
}   

And an available_corpora.json might look like this:   
[   
  "Finnish",   
  "English",   
  "Czech"   
]   

### Editing serve.py

If you're deploying your webUI you will have to add your host into serve.py. You can also enable debug and change ports.

uWSGI deployment
----------------

As a flask application it can be set up as a web service. A way to deploy the application using uWSGI is described at flask-documentation at: http://flask.pocoo.org/docs/0.10/deploying/uwsgi/

Query Language
==============

Query language is described in detail at: http://bionlp.utu.fi/searchexpressions-new.html
