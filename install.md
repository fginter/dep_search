---
layout: page
title: "dep_search installation"
---

# Requirements

The toolkit requires `libsqlite3` development files, header files and static libraries for Python and Cython.

For Ubuntu, these are available as following packages:

* libsqlite3-dev  
* python-dev  
* cython

The webUI requires the python libraries flask, requests and yaml, and for uWSGI based deployment the uwsgi program and its python plugin. For Ubuntu, these are available as:  

* uwsgi  
* uwsgi-plugin-python
* python-flask
* python-yaml
* python-requests

You also need a basic build environment (make, C compiler, ...):

* build-essential

```
sudo apt-get install build-essential libsqlite3-dev python-dev cython uwsgi uwsgi-plugin-python python-flask python-yaml python-requests
```

# Python3

The web application, but not (yet) the web API is also compatible with Python3. The support for Python3 for the web API is in the works.

# Installation

```
git clone https://github.com/fginter/dep_search.git   
cd dep_search
git submodule init   
git submodule update   
make
```

# Index and test a treebank

dep_search comes with the file `example_en.conllu` which contains a handful of sentences from UD English, so you can test the query tool:

```
cat example_en.conllu | python build_index.py --wipe -d example_en_db
python query.py '_ <nsubj _' --dblist example_en_db/*.db
```

