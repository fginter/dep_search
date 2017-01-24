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

This involves two files: `corpora.yaml` tells about every indexed treebank and `corpus_groups.yaml` tells how the treebanks group together, to build the hierarchical treebank selection menu on the main page. These files are under the `webapi` directory of dep_search. Below you can find simple examples, but we keep the full files in GitHub - go have a look [here](https://github.com/fginter/dep_search/blob/master/webapi/corpora.yaml) and [here](https://github.com/fginter/dep_search/blob/master/webapi/corpus_groups.yaml).

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

This happens in two parts:

1. Launch the dep_search webapi using `uwsgi` and tell it to talk over a unix socket.
2. Tell the `nginx` web server where this socket is.

### uWSGI socket

The below command to start the application via uWSGI is in the `launch_via_uwsgi.sh` script for your convenience. The `processes` parameter controls how many concurrent requests you are able to serve, and the `harakiri` places a timeout on serving a single request.

```
/usr/bin/uwsgi
  --plugin python
  --module serve_webapi
  --callable app
  --socket /path/to/dep_search_webapi/webapi/dep_search_webapi.sock
  --pythonpath /path/to/dep_search_webapi/webapi
  --processes 5
  --master
  --harakiri 5000
  --manage-script-name
  --chmod-socket=666
```

But it might be a better idea to use the `supervisord` daemon to manage this process if you are deploying this for real. Supervisord will launch the job, restart it for you, etc. You can place a `dep_search_webapi.conf` in `/etc/supervisor.d/conf.d` looking like this, start the process using `supervisorctl` and you will be all set.

```
[program:dep_search_webapi]
command=/usr/bin/uwsgi
  --plugin python
  --module serve_webapi
  --callable app
  --socket /path/to/dep_search_webapi/webapi/dep_search_webapi.sock
  --pythonpath /path/to/dep_search_webapi/webapi
  --processes 5
  --master
  --harakiri 5000
  --manage-script-name
  --chmod-socket=666
directory=/home/ginter/online_live/dep_search_webapi/webapi
user=ginter
autostart=true
autorestart=true
stdout_logfile=/home/ginter/online_live/dep_search_webapi/webapi/dep_search_webapi.log
redirect_stderr=true
stopsignal=QUIT
```

Once the `uwsgi` process is running and the `dep_search_webapi.sock` exists, you can configure `nginx` to pass traffic to it.

### nginx config

This is all that should be needed as far as nginx goes:

```
location /dep_search_webapi/ {
         rewrite /dep_search_webapi(.*) $1 break;
         include uwsgi_params;
         uwsgi_pass unix:/full/path/to/dep_search_webapi.sock;
         uwsgi_param SCRIPT_NAME /dep_search_webapi;
}
```
