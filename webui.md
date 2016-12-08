---
layout: page
title: dep_search web UI
---

# About

The dep_search web UI runs the web application you can see for example at [http://bionlp-www.utu.fi/dep_search/]. A typical place for it would be in a web server, but it can also run in a terminal just fine.

# Installation

```
git clone https://github.com/fginter/dep_search_serve.git
cd dep_search_serve
```

# Configuration

The only thing the application needs to know is where to find the API which can answer the queries.

* Create a file `config_local.py` containing:

```
DEP_SEARCH_WEBAPI="http://127.0.0.1:XXXX"
```

where `XXXX` is the port on which the API runs, but of course if you have the API running at some other place in your web server, then you provide that URL.

# Running

```
python serve_depsearch.py
```

should be all you need. Point your browser to the address printed and you should be all set.
