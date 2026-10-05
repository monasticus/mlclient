xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
declare variable $v4 as xs:integer external;
declare variable $v5 as xs:integer external;
declare variable $v6 as xs:string external;
declare variable $v7 as xs:double external;
cts:element-child-geospatial-query(xs:QName($v0), xs:QName($v1), cts:box(xs:float($v2), xs:float($v3), xs:float($v4), xs:float($v5)), $v6, $v7)
