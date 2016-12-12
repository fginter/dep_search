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

The webUI requires the python libraries flask and yaml, and for uWSGI based deployment uwsgi & uwsgi-python plugin. For Ubuntu, these are available as:  

* uwsgi  
* uwsgi-python-plugin  
* python-flask
* python-yaml

```
sudo apt-get install libsqlite3-dev python-dev cython uwsgi uwsgi-python-plugin python-flask python-yaml
```

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

# Full installation command log

In the file [install_webui_into_clean_ubuntu.txt](https://github.com/fginter/dep_search/blob/master/install_webui_into_clean_ubuntu.txt) you can find all the required commands needed to install the software onto a clean, out-of-the-box Ubuntu Linux.
