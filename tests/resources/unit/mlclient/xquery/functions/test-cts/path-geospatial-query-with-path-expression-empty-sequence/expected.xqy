xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
cts:path-geospatial-query((), cts:box(xs:double($v0), xs:double($v1), xs:double($v2), xs:double($v3)))
