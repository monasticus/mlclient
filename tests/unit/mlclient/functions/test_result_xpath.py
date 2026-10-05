import pytest

from mlclient.functions.xqy import Cts, XqyExpression


@pytest.mark.parametrize(
    ("expression", "path", "expected_code", "expected_variables"),
    [
        (
            Cts.search(),
            "some/child",
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
            {"v0": "some/child", "v1": "cts:search(/, ()) ! some/child"},
        ),
        (
            Cts.search(),
            "/some-root/some/child",
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
                "v0": "/some-root/some/child",
                "v1": "cts:search(/, ()) ! /some-root/some/child",
            },
        ),
        (
            Cts.search(),
            "/",
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
            {"v0": "/", "v1": "cts:search(/, ()) ! /"},
        ),
        (
            Cts.search().pos(1),
            "some/child",
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v1">{$v1}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v2)\n"
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
                "v0": "1",
                "v1": "some/child",
                "v2": "cts:search(/, ())[$v0] ! some/child",
            },
        ),
        (
            Cts.search().pos(1),
            "/some-root/some/child",
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v1">{$v1}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v2)\n"
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
                "v0": "1",
                "v1": "/some-root/some/child",
                "v2": "cts:search(/, ())[$v0] ! /some-root/some/child",
            },
        ),
        (
            Cts.search().pos(1),
            "/",
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v1">{$v1}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v2)\n"
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
            {"v0": "1", "v1": "/", "v2": "cts:search(/, ())[$v0] ! /"},
        ),
        (
            Cts.search().pos([1, 10]),
            "some/child",
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:integer external;\n"
                "declare variable $v2 as xs:string external;\n"
                "declare variable $v3 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v2">{$v2}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v3)\n"
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
                "v0": "1",
                "v1": "10",
                "v2": "some/child",
                "v3": "cts:search(/, ())[$v0 to $v1] ! some/child",
            },
        ),
        (
            Cts.search().pos([1, 10]),
            "/some-root/some/child",
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:integer external;\n"
                "declare variable $v2 as xs:string external;\n"
                "declare variable $v3 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v2">{$v2}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v3)\n"
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
                "v0": "1",
                "v1": "10",
                "v2": "/some-root/some/child",
                "v3": "cts:search(/, ())[$v0 to $v1] ! /some-root/some/child",
            },
        ),
        (
            Cts.search().pos([1, 10]),
            "/",
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:integer external;\n"
                "declare variable $v1 as xs:integer external;\n"
                "declare variable $v2 as xs:string external;\n"
                "declare variable $v3 as xs:string external;\n"
                "let $invalid-paths := (\n"
                '    <path kind="xpath" binding="v2">{$v2}</path>\n'
                ")[fn:not(\n"
                "    try { cts:valid-extract-path(.) }\n"
                "    catch ($error) { fn:false() }\n"
                ")]\n"
                "return if (fn:empty($invalid-paths)) then\n"
                "    xdmp:value($v3)\n"
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
                "v0": "1",
                "v1": "10",
                "v2": "/",
                "v3": "cts:search(/, ())[$v0 to $v1] ! /",
            },
        ),
    ],
)
def test_xpath_preserves_selected_results(
    expression,
    path,
    expected_code,
    expected_variables,
):
    code, variables = expression.xpath(path).compile()

    assert code == expected_code
    assert variables == expected_variables


@pytest.mark.parametrize(
    ("path", "error_type", "message"),
    [
        (None, TypeError, "xpath must be a string"),
        ("", ValueError, "xpath must not be empty"),
        ("  ", ValueError, "xpath must not be empty"),
    ],
)
def test_result_xpath_rejects_invalid_input(path, error_type, message):
    with pytest.raises(error_type) as error:
        Cts.search().xpath(path)

    assert str(error.value) == message


def test_xpath_groups_compound_source():
    class Conditional(XqyExpression):
        def render(self, _ctx):
            return "if (true()) then <a/> else <b/>"

    expression = Conditional().xpath("*")
    code, variables = expression.compile()

    assert code == (
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
    )
    assert variables == {"v0": "*", "v1": "(if (true()) then <a/> else <b/>) ! *"}
