from mlclient.xquery import Cts, fn


def test_all_nested_path_literals_are_bound_and_guarded():
    paths = ["/p:one", '/two[fn:contains(., "quote"&")]', "/a", "/b"]
    expression = fn.count(
        [
            Cts.search(paths[0]),
            Cts.search(paths[1]),
            Cts.uris(query=Cts.path_range_query(paths[2:], "=", 3)),
        ],
    )
    code, variables = expression.compile(
        namespaces={"p": "https://monasticus.com/mlclient/examples/one"},
    )

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare namespace p = "
        '"https://monasticus.com/mlclient/examples/one";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "declare variable $v3 as xs:string external;\n"
        "declare variable $v4 as xs:string external;\n"
        "declare variable $v5 as xs:integer external;\n"
        "declare variable $v6 as xs:string external;\n"
        "let $invalid-paths := (\n"
        '    <path kind="search" binding="v0">{$v0}</path>,\n'
        '    <path kind="search" binding="v1">{$v1}</path>\n'
        ")[fn:not(\n"
        "    try { cts:valid-extract-path(.) }\n"
        "    catch ($error) { fn:false() }\n"
        ")]\n"
        "return if (fn:empty($invalid-paths)) then\n"
        "    xdmp:value($v6)\n"
        "else\n"
        '    fn:error(fn:QName("", "MLCLIENT-INVALID-PATH"),\n'
        '        fn:concat("Invalid XPath(s): ", fn:string-join(\n'
        "            for $path in $invalid-paths\n"
        '            return fn:concat("[", fn:string($path/@kind), '
        '":",\n'
        '                fn:string($path/@binding), "] ", '
        "fn:string($path)),\n"
        '            "; ")),\n'
        "        $invalid-paths)"
    )
    assert variables == {
        "v0": "/p:one",
        "v1": '/two[fn:contains(., "quote"&")]',
        "v2": "/a",
        "v3": "/b",
        "v4": "=",
        "v5": "3",
        "v6": (
            "fn:count((cts:search(/p:one, ()), cts:search(/two[fn:co"
            'ntains(., "quote"&")], ()), cts:uris((), (), cts:path-r'
            "ange-query(($v2, $v3), xs:string($v4), $v5))))"
        ),
    }
