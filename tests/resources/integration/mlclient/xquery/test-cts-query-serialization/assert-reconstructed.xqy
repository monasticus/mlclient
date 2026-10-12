@@prolog@@
declare variable $serialized_xml as xs:string external;
declare variable $serialized_json as xs:string external;

let $native := @@body@@
return (
    $native,
    (
      $serialized_xml,
      $serialized_json
    ) ! (xdmp:unquote(.)/node() => cts:query())
) ! (xdmp:to-json(.) => xdmp:quote())
