xquery version "1.0-ml";
declare variable $v0 as xs:date external;
fn:dateTime($v0, fn:current-time())
