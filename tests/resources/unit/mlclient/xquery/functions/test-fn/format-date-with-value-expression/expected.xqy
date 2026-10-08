xquery version "1.0-ml";
declare variable $v0 as xs:string external;
fn:format-date(fn:current-date(), $v0)
