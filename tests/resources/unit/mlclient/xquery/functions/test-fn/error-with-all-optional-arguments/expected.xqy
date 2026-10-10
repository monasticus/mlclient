xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
fn:error(cts:search(/, ())[$v0], $v1, cts:search(/, ())[$v2])
