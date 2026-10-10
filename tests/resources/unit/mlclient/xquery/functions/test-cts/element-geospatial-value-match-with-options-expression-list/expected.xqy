xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
cts:element-geospatial-value-match(xs:QName($v0), $v1, (fn:string(cts:search(/, ())[$v2]), fn:string(cts:search(/, ())[$v3])))
