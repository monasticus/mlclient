xquery version "1.0-ml";

declare variable $collection as xs:string external;
declare variable $start external;
declare variable $size external;

let $start := xs:integer($start)
let $size := xs:integer($size)
return
if ($start lt 1 or $size lt 1 or $size gt 1000) then
  fn:error(xs:QName("local:INVALID-PAGE"), "Use positive start and size up to 1000")
else
  let $query := cts:collection-query($collection)
  let $hits := cts:search(/, $query, ("filtered", "score-zero", cts:document-order("ascending")))
  return document {
    object-node {
      "estimated-fragments": xdmp:estimate($hits),
      "uris": array-node {
        fn:subsequence($hits, $start, $size) ! fn:base-uri(.)
      }
    }
  }
