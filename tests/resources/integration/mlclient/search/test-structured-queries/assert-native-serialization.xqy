xquery version "1.0-ml";
import module namespace csu = "http://marklogic.com/rest-api/config-query-util"
    at "/MarkLogic/rest-api/lib/config-query-util.xqy";

declare variable $xml external;
declare variable $json external;

let $actual := xdmp:unquote($json) => csu:json-to-xml()
let $expected := xdmp:unquote($xml)/node()
return
    if (fn:deep-equal($actual, $expected)) then
        fn:true()
    else (
        <actual>{$actual}</actual>,
        <expected>{$expected}</expected>
    )
