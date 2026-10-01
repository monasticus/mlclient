xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:integer external;
cts:uri-match($v0, (), (), (), fn:count(cts:search(/, ())[$v1]))
