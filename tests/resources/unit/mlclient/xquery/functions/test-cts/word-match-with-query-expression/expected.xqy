xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
cts:word-match($v0, (), cts:collection-query($v1))
