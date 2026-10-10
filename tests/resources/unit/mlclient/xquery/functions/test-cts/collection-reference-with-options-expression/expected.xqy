xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
cts:collection-reference(fn:string(cts:search(/, ())[$v0]))
