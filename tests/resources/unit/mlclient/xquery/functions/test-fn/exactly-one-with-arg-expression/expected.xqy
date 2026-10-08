xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
fn:exactly-one(cts:search(/, ())[$v0])
