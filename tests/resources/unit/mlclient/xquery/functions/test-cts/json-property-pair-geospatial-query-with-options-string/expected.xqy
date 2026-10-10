xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:integer external;
declare variable $v4 as xs:integer external;
declare variable $v5 as xs:integer external;
declare variable $v6 as xs:integer external;
declare variable $v7 as xs:string external;
cts:json-property-pair-geospatial-query($v0, $v1, $v2, cts:box(xs:double($v3), xs:double($v4), xs:double($v5), xs:double($v6)), $v7)
