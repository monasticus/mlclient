xquery version "1.0-ml";
declare variable $v0 as xs:date external;
declare variable $v1 as xs:integer external;
fn:format-date($v0, fn:string(cts:search(/, ())[$v1]))
