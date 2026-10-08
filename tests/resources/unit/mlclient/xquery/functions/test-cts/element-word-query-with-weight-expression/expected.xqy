xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
cts:element-word-query(xs:QName($v0), $v1, (), xs:double(fn:count(cts:search(/, ())[$v2])))
