xquery version "1.0-ml";

declare variable $host as xs:string external;
declare variable $port as xs:integer external;
declare variable $timeout as xs:integer external;

(: An eval may reach any host behind a load balancer. :)
let $address :=
    if ($host eq xdmp:host-name(xdmp:host())) then "localhost"
    else $host
return
    try {
        xdmp:http-get(
            "http://" || $address || ":" || $port || "/",
            <options xmlns="xdmp:http">
                <timeout>{$timeout}</timeout>
            </options>
        )[1]/*:code = 200
    } catch ($e) { fn:false() }
