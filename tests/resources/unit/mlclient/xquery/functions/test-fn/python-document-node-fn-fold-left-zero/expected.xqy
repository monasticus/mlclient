xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
fn:fold-left(fn:string($v0), xdmp:unquote($v1), fn:string($v2))
