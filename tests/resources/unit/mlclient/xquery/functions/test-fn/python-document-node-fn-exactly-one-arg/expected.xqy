xquery version "1.0-ml";
declare variable $v0 as xs:string external;
fn:exactly-one(xdmp:unquote($v0))
