xquery version "1.0-ml";
declare variable $v0 as xs:string external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
declare variable $v3 as xs:string external;
declare variable $v4 as xs:integer external;
cts:element-attribute-value-co-occurrences(xs:QName($v0), xs:QName($v1), xs:QName($v2), xs:QName($v3), fn:string(cts:search(/, ())[$v4]))
