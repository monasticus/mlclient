declare variable $root as xs:string external;
declare variable $root_namespace as xs:string external;
object-node { "total": cts:estimate(cts:and-query((cts:document-root-query(fn:QName($root_namespace, $root)), (cts:true-query())))), "start": 1, "pageSize": 10, "results": array-node { cts:search(fn:collection(), cts:and-query((cts:document-root-query(fn:QName($root_namespace, $root)), (cts:true-query()))), "filtered")[1 to 10] ! object-node { "uri": xdmp:node-uri(.), "document": xdmp:quote(.) } }}
