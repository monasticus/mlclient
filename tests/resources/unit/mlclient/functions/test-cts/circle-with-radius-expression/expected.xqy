xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
cts:circle(xs:double(fn:count(cts:search(/, ())[$v0])), cts:point($v1, $v2))
