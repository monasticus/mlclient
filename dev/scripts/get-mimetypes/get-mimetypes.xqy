xquery version "1.0-ml";

declare private variable $local:NEW-LINE as xs:string := "&#xa;";

declare private function local:transform-to-jsons(
  $mimetype-elements as element()+
) as json:object+ {
  $mimetype-elements ! (
    json:object()
    => map:with("mime-type", ./*:name/xs:string(.))
    => map:with("extensions", ./*:extensions/xs:string(.) => fn:tokenize(" "))
    => map:with("doc-type", ./*:format/xs:string(.))
  )
};

declare private function local:build-yaml(
  $mimetype-jsons as json:object+
) as xs:string {
  (
    "mimetypes:",
    "",
    $mimetype-jsons ! (
      "  - mime-type: " || map:get(., "mime-type"),
      "    extensions: [ " || map:get(., "extensions") => fn:string-join(", ") || " ]",
      "    doc-type: " || map:get(., "doc-type"),
      ""
    )
  ) => fn:string-join($local:NEW-LINE)
};

xdmp:mimetypes()
=> local:transform-to-jsons()
=> local:build-yaml()