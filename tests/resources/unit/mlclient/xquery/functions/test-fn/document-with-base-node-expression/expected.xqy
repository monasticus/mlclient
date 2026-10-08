xquery version "1.0-ml";
declare namespace p = "https://example.com/products";
declare variable $v0 as xs:integer external;
declare variable $v1 as xs:string external;
declare variable $v2 as xs:string external;
let $invalid-paths := (
    <path kind="xpath" binding="v1">{$v1}</path>
)[fn:not(
    try { cts:valid-extract-path(.) }
    catch ($error) { fn:false() }
)]
return if (fn:empty($invalid-paths)) then
    xdmp:value($v2)
else
    fn:error(fn:QName("", "MLCLIENT-INVALID-PATH"),
        fn:concat("Invalid XPath(s): ", fn:string-join(
            for $path in $invalid-paths
            return fn:concat("[", fn:string($path/@kind), ":",
                fn:string($path/@binding), "] ", fn:string($path)),
            "; ")),
        $invalid-paths)
