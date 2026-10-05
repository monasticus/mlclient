import pytest

from mlclient.functions.xqy import Cts, ModuleFunctionCall, fn, xpath


@pytest.mark.parametrize(
    ("expression", "position", "expected_code", "expected_variables"),
    [
        (
            Cts.uris(),
            fn.last(),
            ('xquery version "1.0-ml";\ncts:uris()[fn:last()]'),
            {},
        ),
        (
            Cts.uris(),
            [fn.last(), fn.last()],
            ('xquery version "1.0-ml";\ncts:uris()[fn:last() to fn:last()]'),
            {},
        ),
        (
            Cts.search(),
            fn.last(),
            ('xquery version "1.0-ml";\ncts:search(/, ())[fn:last()]'),
            {},
        ),
        (
            Cts.search(),
            [fn.last(), fn.last()],
            ('xquery version "1.0-ml";\ncts:search(/, ())[fn:last() to fn:last()]'),
            {},
        ),
        (
            Cts.uris().pos(1),
            fn.last(),
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "cts:uris()[$v0][fn:last()]"
            ),
            {"v0": "1"},
        ),
        (
            Cts.uris().pos(1),
            [fn.last(), fn.last()],
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "cts:uris()[$v0][fn:last() to fn:last()]"
            ),
            {"v0": "1"},
        ),
        (
            Cts.uris().pos([1, 5]),
            fn.last(),
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:integer external;\n"
                "cts:uris()[$v0 to $v1][fn:last()]"
            ),
            {"v0": "1", "v1": "5"},
        ),
        (
            Cts.uris().pos([1, 5]),
            [fn.last(), fn.last()],
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:integer external;\n"
                "cts:uris()[$v0 to $v1][fn:last() to fn:last()]"
            ),
            {"v0": "1", "v1": "5"},
        ),
        (
            ModuleFunctionCall(
                "normalize",
                ["coffee"],
                namespace="https://monasticus.com/mlclient/examples/labels",
                module_path="/examples/labels.xqy",
            ),
            fn.last(),
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "declare variable $v3 as xs:string external;\n"
                "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), "
                "$v3)[fn:last()]"
            ),
            {
                "v0": "https://monasticus.com/mlclient/examples/labels",
                "v1": "normalize",
                "v2": "/examples/labels.xqy",
                "v3": "coffee",
            },
        ),
        (
            ModuleFunctionCall(
                "normalize",
                ["coffee"],
                namespace="https://monasticus.com/mlclient/examples/labels",
                module_path="/examples/labels.xqy",
            ),
            [fn.last(), fn.last()],
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "declare variable $v3 as xs:string external;\n"
                "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), "
                "$v3)[fn:last() to fn:last()]"
            ),
            {
                "v0": "https://monasticus.com/mlclient/examples/labels",
                "v1": "normalize",
                "v2": "/examples/labels.xqy",
                "v3": "coffee",
            },
        ),
        (
            xpath("/product/title"),
            fn.last(),
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v0">{$v0}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v1)\n"
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
            ),
            {"v0": "/product/title", "v1": "(/product/title)[fn:last()]"},
        ),
        (
            xpath("/product/title"),
            [fn.last(), fn.last()],
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v0">{$v0}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v1)\n"
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
            ),
            {"v0": "/product/title", "v1": "(/product/title)[fn:last() to fn:last()]"},
        ),
        (
            Cts.search().xpath("product/title"),
            fn.last(),
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v0">{$v0}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v1)\n"
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
            ),
            {
                "v0": "product/title",
                "v1": "(cts:search(/, ()) ! product/title)[fn:last()]",
            },
        ),
        (
            Cts.search().xpath("product/title"),
            [fn.last(), fn.last()],
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v0">{$v0}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v1)\n"
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
            ),
            {
                "v0": "product/title",
                "v1": "(cts:search(/, ()) ! product/title)[fn:last() to fn:last()]",
            },
        ),
    ],
)
def test_position_predicates_group_paths_but_not_function_calls(
    expression,
    position,
    expected_code,
    expected_variables,
):
    code, variables = expression.pos(position).compile()

    assert code == expected_code
    assert variables == expected_variables


def test_default_search_uses_database_root():
    expression = Cts.search()
    code, variables = expression.compile()

    assert code == ('xquery version "1.0-ml";\ncts:search(/, ())')
    assert variables == {}


def test_pos_none_preserves_expression():
    expression = Cts.uris()

    assert expression.pos(None) is expression


@pytest.mark.parametrize("position", [[], [1], [1, 2, 3], (), (1,), (1, 2, 3)])
def test_pos_rejects_ranges_without_two_positions(position):
    with pytest.raises(TypeError) as error:
        Cts.uris().pos(position)

    assert str(error.value) == "pos ranges must contain exactly two positions"
