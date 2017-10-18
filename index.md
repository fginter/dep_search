---
layout: page
---

# About dep_search

`dep_search` is a tool for treebank search especially tuned towards large-scale parsebanks. You can [test it in action](http://bionlp-www.utu.fi/dep_search/) at the Turku BioNLP group's pages, and it also powers the [Universal Dependencies content validation system](http://universaldependencies.org/svalidation.html).

# Query language documentation

The [documentation of the query language is here](http://bionlp.utu.fi/searchexpressions-new.html).

# Installation

## dep_search

`dep_search` is a command line tool which can be installed according to [these instructions](install.html). This will give you the opportunity to index and query treebanks from the command line, and may be all you need.

## API and Web application

`dep_search` also includes a Web API built using Python Flask which lets you query your treebanks using simple HTTP requests, and a Web application which gives you a browser-based interface which renders the trees. These power the main dep_search web interface at [http://bionlp-www.utu.fi/dep_search/] but you can also run them locally.

* Set up the API [instructions](webapi.html)
* Run the web application [instructions](webui.html)

# Citations

If you use `dep_search` in your research, please cite papers:

J. Luotolahti; J. Kanerva; S. Pyysalo; F. Ginter. SETS: Scalable and Efficient Tree Search in Dependency Graphs. Proceedings of the 2015 Conference of the North American Chapter of the Association for Computational Linguistics: Demonstrations. 2015

J. Luotolahti; J. Kanerva; F. Ginter. Dep_search: Efficient Search Tool for Large Dependency Parsebanks. Proceedings of the 21st Nordic Conference on Computational Linguistics (NoDaLiDa). 2017
