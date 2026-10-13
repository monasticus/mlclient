xquery version "1.0-ml";
import module namespace search = "http://marklogic.com/appservices/search"
    at "/MarkLogic/appservices/search/search.xqy";

declare variable $options external;

xdmp:unquote($options)/node()
=> search:check-options(fn:true())
=> fn:count()
