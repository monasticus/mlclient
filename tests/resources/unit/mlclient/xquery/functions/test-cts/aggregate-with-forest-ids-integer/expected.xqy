xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:integer external;
cts:aggregate($v0, $v1, cts:element-reference(xs:QName($v2)), (), (), (), $v3)
