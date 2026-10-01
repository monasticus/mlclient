xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:double external;
declare variable $v2 as xs:integer external;
fn:subsequence(cts:search(/, ())[$v0], $v1, fn:count(cts:search(/, ())[$v2]))
