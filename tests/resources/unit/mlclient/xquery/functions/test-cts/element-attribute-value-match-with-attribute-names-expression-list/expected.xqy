xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:string external;
declare variable $v4 as xs:string external;
declare variable $v5 as xs:string external;
cts:element-attribute-value-match(xs:QName($v0), (fn:QName($v1, $v2), fn:QName($v3, $v4)), $v5)
