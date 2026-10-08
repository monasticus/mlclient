xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:string external;
cts:highlight(cts:search(/, ())[$v0], $v1, ((function($node, $queries) { $node }), (function($node, $queries) { $node })))
