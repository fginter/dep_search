---
layout: page
title: dep_search API documentation
---

# About

The dep_search API exposes a local dep_search via a simple HTTP-based API. It allows you to query treebanks using HTTP requests and is used to automate dep_search runs and as a back-end for the [web application](webui.html). You can try it live - the following command queries UD English with the query `_ <nsubj _` and returns 10 trees:

```
curl -L 'http://bionlp-www.utu.fi/dep_search_webapi?search=_%20%3Cnsubj%20_&db=UD_English-v13&case=True&retmax=10&dl'
```


There are three steps to get going:

1. Index at least one treebank
2. Tell the API where to find the index on the local drive
3. Start the service so that it can be queried

# Indexing a treebank

All you need is to cat a treebank in the [`CoNLL-U` format](http://universaldependencies.org/format.html) to the `build_index` command like so:

```
cat example_en.conllu | python build_index.py --wipe -d example_en_db
```

which will create a directory `example_en_db` with the treebank index.

# Telling dep_search API where the treebank is

This involves two files: `corpora.yaml` tells about every indexed treebank and `corpus_groups.yaml` tells how the treebanks group together, to build the hierarchical treebank selection menu on the main page. These files are under the `webui` directory of dep_search. Below you can find simple examples, but we keep the full files in GitHub - go have a look [here](https://github.com/fginter/dep_search/blob/master/webui/corpora.yaml) and [here](https://github.com/fginter/dep_search/blob/master/webui/corpus_groups.yaml).

## corpora.yaml

This file lists the indexed corpora the API should know about. A simple entry looks like this:

```
english_demo:
  paths: /path/to/example_en_db
  name: "Small English demo corpus"
```

Here `english_demo` is a handle which is used in the API requests, `paths` is where the index is located locally, and `name` is shown in the corpus selection drop-down in the web application.

## corpus_groups.yaml

This file groups the corpora into logical groups. Currently it is used to group the corpora for the corpus selection drop-down in the web application.

```
-
  name: "My dev treebanks"
  corpora: english_demo
```

Where `My dev treebanks` is a group of corpora, and `corpora` is a space-separated list of corpora from `corpora.yaml`.

# Running the API

## In terminal

```
python serve_webapi.py
```

By default, this will serve the API at all interfaces, port `45678`. You can change these settings in `serve_webapi.py`. You can test it by pointing your browser to <http://127.0.0.1:45678>  in the default setup and then to <http://127.0.0.1:45678/metadata/>

## Under nginx

TODO