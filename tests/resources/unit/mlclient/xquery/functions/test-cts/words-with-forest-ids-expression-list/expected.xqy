xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
cts:words((), (), (), (), (fn:count(cts:search(/, ())[$v0]), fn:count(cts:search(/, ())[$v1])))
