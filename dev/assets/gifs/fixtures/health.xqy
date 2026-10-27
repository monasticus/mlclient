xquery version "1.0-ml";
let $count := xdmp:get-server-field("demo-probes", 0) + 1
return (
  xdmp:set-server-field("demo-probes", $count),
  if ($count gt 8) then xdmp:set-response-code(200, "OK")
  else xdmp:set-response-code(503, "Service Unavailable")
)
