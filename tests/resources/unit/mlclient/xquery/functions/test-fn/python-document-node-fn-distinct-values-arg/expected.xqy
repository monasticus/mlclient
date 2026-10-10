xquery version "1.0-ml";
declare variable $v0 as xs:string external;
fn:distinct-values(xdmp:unquote($v0))
