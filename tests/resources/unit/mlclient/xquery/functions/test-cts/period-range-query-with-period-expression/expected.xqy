xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:dateTime external;
declare variable $v3 as xs:dateTime external;
cts:period-range-query($v0, $v1, cts:period($v2, $v3))
