xquery version "1.0-ml";

declare variable $port as xs:integer external;
declare variable $timeout as xs:integer external;

map:new(
    for $host in xdmp:hosts()
    (: The configured host name may not resolve on the host itself. :)
    let $address :=
        if ($host eq xdmp:host()) then "localhost"
        else xdmp:host-name($host)
    return map:entry(xdmp:host-name($host), (
        try {
            xdmp:http-get(
                "http://" || $address || ":" || $port || "/",
                <options xmlns="xdmp:http">
                    <timeout>{$timeout}</timeout>
                </options>
            )[1]/*:code = 200
        } catch ($e) { fn:false() }
    ))
)
