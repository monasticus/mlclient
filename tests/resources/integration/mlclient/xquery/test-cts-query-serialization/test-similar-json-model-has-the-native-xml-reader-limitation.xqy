@@prolog@@
declare variable $xml external;
declare variable $json external;

let $native := @@body@@
return array-node {
    (
        <a>{$native}</a>,
        xdmp:unquote($xml),
        xdmp:unquote($json)
    ) ! (./node() => cts:query() => xdmp:to-json()) ! ./node()
}
