xquery version "1.0-ml";
declare variable $v0 as xs:double external;
declare variable $v1 as xs:double external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:double external;
cts:box($v0, $v1, xs:double(fn:count(cts:search(/, ())[$v2])), $v3)
