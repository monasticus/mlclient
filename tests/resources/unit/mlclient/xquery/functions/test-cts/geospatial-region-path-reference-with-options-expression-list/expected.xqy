xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
cts:geospatial-region-path-reference($v0, (fn:string(cts:search(/, ())[$v1]), fn:string(cts:search(/, ())[$v2])))
