@@prolog@@
declare variable $xml external;declare variable $json external;
let $native := @@body@@
return array-node {
xdmp:to-json(cts:query(<a>{$native}</a>/*))/node(), xdmp:to-json(cts:query(xdmp:unquote($xml)/*))/node(), xdmp:to-json(cts:query(xdmp:unquote($json)/node()))/node()}