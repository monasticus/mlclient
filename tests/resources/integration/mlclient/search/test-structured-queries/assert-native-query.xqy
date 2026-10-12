xquery version "1.0-ml";
import module namespace search = "http://marklogic.com/appservices/search"
    at "/MarkLogic/appservices/search/search.xqy";
import module namespace csu = "http://marklogic.com/rest-api/config-query-util"
    at "/MarkLogic/rest-api/lib/config-query-util.xqy";

declare namespace r = "https://example.com/example/reports";
declare variable $query external;
declare variable $query_json external;
declare variable $options external;

let $structured-xml := xdmp:unquote($query)/node()
let $structured-json := xdmp:unquote($query_json) => csu:json-to-xml()
let $options := <search:options>
    <search:return-results>false</search:return-results>
    <search:return-facets>false</search:return-facets>
    <search:return-query>true</search:return-query>
    {xdmp:unquote($options)/search:options/node()}
</search:options>
let $actual := search:resolve($structured-xml, $options)/search:query/node()
let $actual_json := search:resolve($structured-json, $options)/search:query/node()
let $expected := <container>{@@native@@}</container>/node()
return
    if (
        fn:deep-equal($structured-json, $structured-xml)
        and fn:deep-equal($actual, $expected)
        and fn:deep-equal($actual_json, $expected)
    ) then
        fn:true()
    else (
        <actual>{$actual}</actual>,
        <actual-json>{$actual_json}</actual-json>,
        <expected>{$expected}</expected>
    )
