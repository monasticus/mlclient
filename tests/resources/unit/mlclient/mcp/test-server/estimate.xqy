declare variable $root as xs:string external;
declare variable $root_namespace as xs:string external;
cts:estimate(cts:and-query((cts:document-root-query(fn:QName($root_namespace, $root)), (cts:true-query()))))
