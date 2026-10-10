xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
declare variable $v4 as xs:integer external;
declare variable $v5 as xs:integer external;
cts:json-property-child-geospatial-query(fn:string(cts:search(/, ())[$v0]), $v1, cts:box(xs:double($v2), xs:double($v3), xs:double($v4), xs:double($v5)))
