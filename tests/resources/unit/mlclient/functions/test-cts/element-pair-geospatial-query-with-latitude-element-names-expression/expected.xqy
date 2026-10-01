xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:string external;
declare variable $v4 as xs:integer external;
declare variable $v5 as xs:integer external;
declare variable $v6 as xs:integer external;
declare variable $v7 as xs:integer external;
cts:element-pair-geospatial-query(xs:QName($v0), fn:QName($v1, $v2), xs:QName($v3), cts:box(xs:float($v4), xs:float($v5), xs:float($v6), xs:float($v7)))
