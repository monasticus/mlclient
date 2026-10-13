xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
fn:upper-case(fn:string(cts:search(/, ())[$v0]))
