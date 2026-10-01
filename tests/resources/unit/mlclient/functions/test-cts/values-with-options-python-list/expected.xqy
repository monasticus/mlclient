xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
cts:values(cts:element-reference(xs:QName($v0)), (), ($v1))
