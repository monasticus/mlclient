xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
cts:json-property-reference(fn:string(cts:search(/, ())[$v0]))
