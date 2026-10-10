xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
cts:uris((), (), (), xs:double(fn:count(cts:search(/, ())[$v0])))
