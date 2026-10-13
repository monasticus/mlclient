xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
cts:geospatial-co-occurrences(xs:QName($v0), xs:QName(()), xs:QName(()), xs:QName($v1), (), (), fn:string(cts:search(/, ())[$v2]))
