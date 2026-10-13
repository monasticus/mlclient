xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
declare variable $v1 as xs:dateTime external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:dateTime external;
declare variable $v4 as xs:dateTime external;
cts:period-compare(cts:period($v0, $v1), fn:string(cts:search(/, ())[$v2]), cts:period($v3, $v4))
