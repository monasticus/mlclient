@@prolog@@
declare variable $serialized_xml as xs:string external;
declare variable $serialized_json as xs:string external;
let $native := @@body@@
return (xdmp:quote(xdmp:to-json($native)), xdmp:quote(xdmp:to-json(cts:query(xdmp:unquote($serialized_xml)/*))), xdmp:quote(xdmp:to-json(cts:query(xdmp:unquote($serialized_json)/node()))))