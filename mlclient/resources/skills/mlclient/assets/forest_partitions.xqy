xquery version "1.0-ml";

(: Run in the intended content database; cluster topology privileges required.
   Primary forest scopes are captured once. Replicas are excluded. :)
let $database-forests := xdmp:database-forests(xdmp:database(), fn:false())
return array-node {
  for $host in xdmp:hosts()
  let $forests := xdmp:host-forests($host)[. = $database-forests]
  where fn:exists($forests)
  return object-node {
    "host": xdmp:host-name($host),
    "forests": array-node { $forests }
  }
}
