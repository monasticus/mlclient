xquery version "1.0-ml";

json:to-array(
    for $host in xdmp:hosts()
    return xdmp:host-name($host)
)
