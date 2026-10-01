xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
fn:hours-from-duration(fn:string(cts:search(/, ())[$v0]))
