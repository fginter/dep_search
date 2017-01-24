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

In a local setup, this would be `http://127.0.0.1:45678` where `45678` is the default port number on which the API runs (see [here](webapi.html) on how to change), but of course if you have the API running at some other address in your web server, then you provide that URL. If you set up `nginx` by [these instructions](webapi.html), then you can set it to `http://you_machine_name/dep_search_webapi`.

# Running the web application

## Standalone

```
python serve_depsearch.py
...or...
python3 serve_depsearch.py
```

should be all you need. Point your browser to the address printed and you should be all set.

## Under nginx

The logic is exactly the same as for the [web API](webapi.html), so the deployment under `nginx` happens in two parts:

1. Launch the serve_depsearch web application using `uwsgi` and tell it to talk over a unix socket.
2. Tell the `nginx` web server where this socket is.

### uWSGI socket

The below command to start the application via uWSGI is in the `launch_webgui_via_uwsgi.sh` script for your convenience. The `processes` parameter controls how many concurrent requests you are able to serve, and the `harakiri` places a timeout on serving a single request.

```
# you can also use --plugin python3
/usr/bin/uwsgi
    --plugin python
    --module serve_depsearch
    --callable app
    --socket /path/to/dep_search_webgui.sock
    --pythonpath /path/to/dep_search_serve
    --processes 5
    --master
    --harakiri 5000
    --manage-script-name
    --chmod-socket=666
```

But it might be a better idea to use the `supervisord` daemon to manage this process if you are deploying this for real. Supervisord will launch the job, restart it for you, etc. You can place a `dep_search_webgui.conf` in `/etc/supervisor.d/conf.d` looking like this, start the process using `supervisorctl` and you will be all set.

```
# you can also use --plugin python3
[program:dep_search_webgui]
command=/usr/bin/uwsgi
  --plugin python
  --module serve_depsearch
  --callable app
  --socket /path/to/dep_search_webgui.sock
  --pythonpath /path/to/dep_search_serve
  --processes 5
  --master
  --harakiri 5000
  --manage-script-name
  --chmod-socket=666
directory=/path/to/dep_search_serve
user=ginter
autostart=true
autorestart=true
stdout_logfile=/path/to/dep_search_serve/dep_search_webgui.log
redirect_stderr=true
stopsignal=QUIT
```

Once the `uwsgi` process is running and the `dep_search_webgui.sock` exists, you can configure `nginx` to pass traffic to it.

### nginx config

This is all that should be needed as far as nginx goes:

```
location /dep_search_webgui/ {
         rewrite /dep_search_webgui(.*) $1 break;
         include uwsgi_params;
         uwsgi_pass unix:/full/path/to/dep_search_webgui.sock;
         uwsgi_param SCRIPT_NAME /dep_search_webgui;
}
```
