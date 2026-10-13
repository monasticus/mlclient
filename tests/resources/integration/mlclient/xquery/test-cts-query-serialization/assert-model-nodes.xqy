@@prolog@@
declare variable $xml external;
declare variable $json external;

let $native := (@@body@@)
let $xml := xdmp:unquote($xml)/node() => cts:query()
let $json := xdmp:unquote($json)/node() => cts:query()
return object-node {
    "xmlNodes": cts:@@kind@@-query-nodes($native)
        => fn:deep-equal(cts:@@kind@@-query-nodes($xml)),
    "jsonNodes": cts:@@kind@@-query-nodes($native)
        => fn:deep-equal(cts:@@kind@@-query-nodes($json)),
    "native": xdmp:to-json($native)/node(),
    "xml": xdmp:to-json($xml)/node(),
    "json": xdmp:to-json($json)/node()
}
