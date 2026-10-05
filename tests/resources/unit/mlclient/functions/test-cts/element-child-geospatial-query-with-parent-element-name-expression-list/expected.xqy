xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:string external;
declare variable $v4 as xs:string external;
declare variable $v5 as xs:integer external;
declare variable $v6 as xs:integer external;
declare variable $v7 as xs:integer external;
declare variable $v8 as xs:integer external;
cts:element-child-geospatial-query((fn:QName($v0, $v1), fn:QName($v2, $v3)), xs:QName($v4), cts:box(xs:float($v5), xs:float($v6), xs:float($v7), xs:float($v8)))
