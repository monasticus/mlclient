xquery version "1.0-ml";
module namespace example = "http://marklogic.com/rest-api/transform/@@name@@";
declare function example:transform(
  $context as map:map, $params as map:map, $content as document-node()
) as document-node() {
  let $root := $content/*
  return document {
    element {node-name($root)} {
      attribute transformed {map:get($params, "value")},
      $root/@*, $root/node()
    }
  }
};