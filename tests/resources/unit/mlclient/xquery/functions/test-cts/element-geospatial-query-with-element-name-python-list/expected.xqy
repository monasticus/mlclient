xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
declare variable $v4 as xs:integer external;
cts:element-geospatial-query((xs:QName($v0)), cts:box(xs:double($v1), xs:double($v2), xs:double($v3), xs:double($v4)))
