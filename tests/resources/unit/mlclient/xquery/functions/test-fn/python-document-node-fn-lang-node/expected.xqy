xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
fn:lang(fn:string($v0), xdmp:unquote($v1))
