xquery version "1.0-ml";
declare variable $v0 as xs:date external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:integer external;
fn:format-date($v0, $v1, (), (), fn:string(cts:search(/, ())[$v2]))
