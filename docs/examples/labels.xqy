xquery version "1.0-ml";

module namespace label = "https://monasticus.com/mlclient/examples/labels";

declare function label:normalize($value as xs:string) as xs:string {
  fn:upper-case(fn:normalize-space($value))
};

declare function label:join($first as xs:string, $second as xs:string) as xs:string {
  label:join($first, $second, " ")
};

declare function label:join(
  $first as xs:string,
  $second as xs:string,
  $separator as xs:string
) as xs:string {
  fn:concat($first, $separator, $second)
};
