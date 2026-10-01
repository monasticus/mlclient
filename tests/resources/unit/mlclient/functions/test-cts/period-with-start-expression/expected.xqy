xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
cts:period(fn:current-dateTime(), $v0)
