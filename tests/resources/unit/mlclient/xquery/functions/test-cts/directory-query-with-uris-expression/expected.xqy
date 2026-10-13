xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:string external;
cts:directory-query(fn:string(cts:search(/, ())[$v0]), xs:string($v1))
