@@prolog@@declare variable $xml external;declare variable $json external;
let $native := (@@body@@)
let $xml := cts:query(xdmp:unquote($xml)/*)
let $json := cts:query(xdmp:unquote($json)/node())
return object-node {
"xmlNodes": fn:deep-equal(cts:@@kind@@-query-nodes($native), cts:@@kind@@-query-nodes($xml)),
"jsonNodes": fn:deep-equal(cts:@@kind@@-query-nodes($native), cts:@@kind@@-query-nodes($json)),
"native": xdmp:to-json($native)/node(), "xml": xdmp:to-json($xml)/node(), "json": xdmp:to-json($json)/node()}