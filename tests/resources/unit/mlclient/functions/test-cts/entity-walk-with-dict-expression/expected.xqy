xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:integer external;
cts:entity-walk(cts:search(/, ())[$v0], (function($node, $queries) { $node }), cts:search(/, ())[$v1])
