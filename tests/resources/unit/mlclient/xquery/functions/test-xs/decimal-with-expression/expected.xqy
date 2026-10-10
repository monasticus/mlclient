xquery version "1.0-ml";
declare variable $v0 as xs:string external;
xs:decimal(cts:sum-aggregate(cts:element-reference(xs:QName($v0))))
