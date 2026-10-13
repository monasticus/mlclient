xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
declare variable $v2 as xs:integer external;
declare variable $v3 as xs:integer external;
declare variable $v4 as xs:integer external;
cts:classify(cts:search(/, ())[$v0], cts:train(cts:search(/, ())[$v1], cts:search(/, ())[$v2]), (), (cts:search(/, ())[$v3], cts:search(/, ())[$v4]))
