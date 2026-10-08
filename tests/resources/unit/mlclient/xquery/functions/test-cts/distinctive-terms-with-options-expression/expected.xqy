xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
cts:distinctive-terms(cts:search(/, ())[$v0], (map:map()))
