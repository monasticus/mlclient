xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
cts:value-co-occurrences(cts:element-reference(xs:QName($v0)), cts:element-reference(xs:QName($v1)), (), (), (), $v2)
