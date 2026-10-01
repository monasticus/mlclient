xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
declare variable $v4 as xs:integer external;
declare variable $v5 as xs:string external;
cts:json-property-geospatial-query($v0, cts:box(xs:float($v1), xs:float($v2), xs:float($v3), xs:float($v4)), ($v5))
