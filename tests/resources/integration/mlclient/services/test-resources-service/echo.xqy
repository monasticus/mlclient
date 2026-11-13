xquery version "1.0-ml";

module namespace echo = "http://marklogic.com/rest-api/resource/mlclient-resources-test";

declare function echo:get(
  $context as map:map,
  $params as map:map
) as document-node()*
{
  echo:report($context, "get", $params, ())
};

declare function echo:post(
  $context as map:map,
  $params as map:map,
  $input as document-node()*
) as document-node()*
{
  if (map:contains($params, "echo"))
  then (
    map:put($context, "output-types", $input ! echo:content-type(.)),
    $input
  )
  else echo:report($context, "post", $params, $input)
};

declare function echo:put(
  $context as map:map,
  $params as map:map,
  $input as document-node()*
) as document-node()?
{
  echo:report($context, "put", $params, $input)
};

declare function echo:delete(
  $context as map:map,
  $params as map:map
) as document-node()?
{
  echo:report($context, "delete", $params, ())
};

declare private function echo:report(
  $context as map:map,
  $method as xs:string,
  $params as map:map,
  $input as document-node()*
) as document-node()
{
  map:put($context, "output-types", "application/json"),
  xdmp:to-json(
    map:new((
      map:entry("method", $method),
      map:entry("database", xdmp:database-name(xdmp:database())),
      map:entry("params", $params),
      map:entry("input-types", json:to-array($input ! echo:content-type(.))),
      map:entry("input-count", fn:count($input))
    ))
  )
};

declare private function echo:content-type(
  $document as document-node()
) as xs:string
{
  typeswitch ($document/node())
    case element() return "application/xml"
    case object-node() return "application/json"
    case array-node() return "application/json"
    case text() return "text/plain"
    default return "application/octet-stream"
};
