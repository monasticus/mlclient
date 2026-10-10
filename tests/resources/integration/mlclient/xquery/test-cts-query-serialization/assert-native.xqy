@@prolog@@
declare variable $serialized_xml as xs:string external;
declare variable $serialized_json as xs:string external;
let $native := @@body@@
let $xml := xdmp:unquote($serialized_xml)/*
let $json := xdmp:unquote($serialized_json)/node()
return fn:deep-equal(<a>{cts:query($xml)}</a>/*, <a>{$native}</a>/*) and fn:deep-equal(<a>{cts:query($json)}</a>/*, <a>{$native}</a>/*)