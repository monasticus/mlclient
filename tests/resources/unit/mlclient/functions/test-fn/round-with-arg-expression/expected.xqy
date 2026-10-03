xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
fn:round(fn:count(cts:search(/, ())[$v0]))
