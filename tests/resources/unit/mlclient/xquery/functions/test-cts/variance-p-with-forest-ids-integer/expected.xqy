xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:integer external;
cts:variance-p(cts:element-reference(xs:QName($v0)), (), (), $v1)
