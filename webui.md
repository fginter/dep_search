---
layout: page
title: dep_search web application documentation
---

# About

The dep_search web application is what you can see at <http://bionlp-www.utu.fi/dep_search/>. It is a simple application for visualizing dep_search query results in various datasets. A typical place for it would be to run under a web server, but it can also run in isolation and serve the content on a local port. This application talks to the [API](webapi.html) and pointing it to the API is pretty much the only configuration it needs.

# Installation

```
git clone https://github.com/fginter/dep_search_serve.git
cd dep_search_serve
```

# Configuration

The only thing the application needs to know is where to find the API which can answer the queries and provide the list of available corpora.

* Create a file `config_local.py` containing:

```
DEP_SEARCH_WEBAPI="http://..."
```

In a local setup, this would be `http://127.0.0.1:45678` where `45678` is the default port number on which the API runs (see [here](webapi.html) on how to change), but of course if you have the API running at some other address in your web server, then you provide that URL.

# Running the web application

## Standalone

```
python serve_depsearch.py
```

should be all you need. Point your browser to the address printed and you should be all set.

## Under nginx

TODO


