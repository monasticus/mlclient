xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:string external;
cts:triple-range-query($v0, (fn:count(cts:search(/, ())[$v1]), fn:count(cts:search(/, ())[$v2])), $v3)
