xquery version "1.0-ml";
declare variable $v0 as xs:string external;
cts:contains(xdmp:unquote($v0), cts:true-query())
