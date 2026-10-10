xquery version "1.0-ml";
declare variable $v0 as xs:string external;
fn:one-or-more(xdmp:unquote($v0))
