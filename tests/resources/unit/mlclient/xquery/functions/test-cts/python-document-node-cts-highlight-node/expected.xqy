xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
cts:highlight(xdmp:unquote($v0), cts:true-query(), fn:string($v1))
