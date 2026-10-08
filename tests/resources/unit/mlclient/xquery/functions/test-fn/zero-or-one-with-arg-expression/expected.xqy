xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
fn:zero-or-one(cts:search(/, ())[$v0])
