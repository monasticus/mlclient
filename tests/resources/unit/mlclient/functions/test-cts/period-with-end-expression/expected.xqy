xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
cts:period($v0, fn:current-dateTime())
