xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
cts:element-value-geospatial-co-occurrences(xs:QName($v0), xs:QName($v1), (), (), (), (), (), (fn:count(cts:search(/, ())[$v2]), fn:count(cts:search(/, ())[$v3])))
