xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
fn:filter(fn:function-lookup(fn:QName($v0, $v1), $v2), cts:search(/, ())[$v3])
