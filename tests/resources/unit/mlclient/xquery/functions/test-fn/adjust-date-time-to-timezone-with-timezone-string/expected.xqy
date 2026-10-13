xquery version "1.0-ml";
declare variable $v0 as xs:dateTime external;
declare variable $v1 as xs:string external;
fn:adjust-dateTime-to-timezone($v0, $v1)
