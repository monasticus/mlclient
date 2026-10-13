xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:string external;
declare variable $v4 as xs:string external;
declare variable $v5 as xs:double external;
declare variable $v6 as xs:integer external;
cts:element-child-geospatial-values(xs:QName($v0), xs:QName($v1), cts:search(/, ())[$v2], $v3, $v4, $v5, $v6)
