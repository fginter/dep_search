THISDIR=`pwd`
/usr/bin/uwsgi --plugin python --module serve_webapi --callable app --socket $THISDIR/dep_search_webapi.sock --pythonpath $THISDIR --processes 5 --master --harakiri 5000 --manage-script-name --chmod-socket=666
