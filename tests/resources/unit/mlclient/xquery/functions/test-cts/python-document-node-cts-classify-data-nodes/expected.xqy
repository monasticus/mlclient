xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
cts:classify(xdmp:unquote($v0), fn:string($v1))
