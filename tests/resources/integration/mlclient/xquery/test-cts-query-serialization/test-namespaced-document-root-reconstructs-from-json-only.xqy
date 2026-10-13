@@prolog@@
declare variable $serialized_json as xs:string external;

let $native := @@body@@
return (
    $native,
    xdmp:unquote($serialized_json)/node() => cts:query()
) ! (xdmp:to-json(.) => xdmp:quote())
