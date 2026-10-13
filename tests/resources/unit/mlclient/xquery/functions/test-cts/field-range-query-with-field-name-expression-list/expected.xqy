xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:string external;
cts:field-range-query((fn:string(cts:search(/, ())[$v0]), fn:string(cts:search(/, ())[$v1])), xs:string($v2), $v3)
