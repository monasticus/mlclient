xquery version "1.0-ml";
declare variable $v0 as xs:integer external;
cts:element-walk(cts:search(/, ())[$v0], xs:QName(()), (function($node, $queries) { $node }))
