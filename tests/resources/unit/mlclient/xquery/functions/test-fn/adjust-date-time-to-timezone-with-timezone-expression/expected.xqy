xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
declare variable $v1 as xs:integer external;
fn:adjust-dateTime-to-timezone($v0, fn:string(cts:search(/, ())[$v1]))
