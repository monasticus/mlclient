xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
cts:registered-query($v0, (), xs:double(fn:count(cts:search(/, ())[$v1])))
