xquery version "1.0-ml";
declare variable $v0 as xs:string external;
cts:parse(cts:true-query(), xdmp:unquote($v0))
