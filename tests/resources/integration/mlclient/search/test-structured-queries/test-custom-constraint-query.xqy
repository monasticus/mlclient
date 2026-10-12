xquery version "1.0-ml";
module namespace custom = "https://example.com/example/structured-custom";

declare namespace search = "http://marklogic.com/appservices/search";

declare function custom:parse(
    $query as element(),
    $options as element(search:options)
) as cts:query {
    $query/search:text/fn:string(.) => cts:word-query()
};
