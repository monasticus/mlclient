xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:double external;
cts:percentile(fn:count(cts:search(/, ())[$v0]), $v1)
