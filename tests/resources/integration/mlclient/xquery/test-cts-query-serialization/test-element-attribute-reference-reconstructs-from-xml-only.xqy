@@prolog@@
declare variable $serialized_xml as xs:string external;

let $native := @@body@@
return (
    $native,
    xdmp:unquote($serialized_xml)/node() => cts:query()
) ! (xdmp:to-json(.) => xdmp:quote())
