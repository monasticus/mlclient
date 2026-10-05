xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
cts:path-geospatial-query((), cts:box(xs:float($v0), xs:float($v1), xs:float($v2), xs:float($v3)))
