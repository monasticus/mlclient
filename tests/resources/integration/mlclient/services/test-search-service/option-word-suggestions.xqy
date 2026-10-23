xquery version "1.0-ml";
import module namespace search="http://marklogic.com/appservices/search"
    at "/MarkLogic/appservices/search/search.xqy";
import module namespace csu="http://marklogic.com/rest-api/config-query-util"
    at "/MarkLogic/rest-api/lib/config-query-util.xqy";
declare variable $options as xs:string external;
let $parsed := xdmp:unquote($options)
let $resolved := if ($parsed/object-node())
    then csu:options-from-json($parsed)
    else $parsed/search:options
return string-join(search:suggest("al", $resolved), "|")
