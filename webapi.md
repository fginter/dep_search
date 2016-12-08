---
layout: page
title: "dep_search API setup"
---

# dep_search API

1. You need to index a treebank and tell dep_search where to find it
2. You need to start the service

# Indexing a treebank

All you need is to cat a treebank in the `CoNLL-U` format to the `build_index` command like so:

```
cat ../UD_Finnish/fi-ud-train.conllu | python build_index.py --wipe -d ud_finnish_idx
```

which will create a directory `ud_finnish_idx` with the treebank index.

# Telling dep_search API where the treebank is

## corpora.yaml

This file lists the indexed corpora the API should know about. One entry looks like this:

```
ud_finnish:
  paths: /path/to/ud_finnish_idx
  name: "My UD Finnish corpus"
```

## corpus_groups.yaml

This file groups the corpora for the drop-down menu. One entry looks like this:

```
-
  name: "My dev treebanks"
  corpora: ud_finnish
```

# Running the API

## In terminal

```
python serve_webapi.py
```




