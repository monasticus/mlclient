xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
fn:insert-before((), $v0, cts:search(/, ())[$v1])
