xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
cts:collections(fn:string(cts:search(/, ())[$v0]))
