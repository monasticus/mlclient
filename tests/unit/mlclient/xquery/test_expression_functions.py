import pytest
import re

from mlclient.xquery import Cts, fn, namespace_bindings, xpath


def test_xpath_compiles_one_guarded_body_with_readable_diagnostics():
    expression = fn.count(xpath("/a"))
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
    assert variables == {"v0": "/a", "v1": "fn:count(/a)"}


def test_count_string_is_bound_data_without_a_path_guard():
    expression = fn.count("/a")
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "fn:count($v0)"
    )
    assert variables == {"v0": "/a"}


def test_search_path_is_bound_before_validation():
    attack = "(: (( :) /), cts:false-query()), 424242, (( (: )) :)"
    expression = Cts.search(attack, Cts.true_query())
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "let $invalid-paths := (\n"
        '    <path kind="search" binding="v0">{$v0}</path>\n'
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
    assert variables == {
        "v0": "(: (( :) /), cts:false-query()), 424242, (( (: )) :)",
        "v1": (
            "cts:search((: (( :) /), cts:false-query()), 424242, (( "
            "(: )) :), cts:true-query())"
        ),
    }


def test_word_query_value_is_bound_data():
    attack = "(: (( :) /), cts:false-query()), 424242, (( (: )) :)"
    expression = Cts.word_query(attack)
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "cts:word-query($v0)"
    )
    assert variables == {"v0": "(: (( :) /), cts:false-query()), 424242, (( (: )) :)"}


def test_search_path_preserves_eqnames_and_comments():
    source = (
        "/Q{https://monasticus.com/mlclient/examples/example}item "
        "(: a valid ) comment :)"
    )
    expression = Cts.search(xpath(source))
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
    assert variables == {
        "v0": (
            "/Q{https://monasticus.com/mlclient/examples/example}ite"
            "m (: a valid ) comment :)"
        ),
        "v1": (
            "cts:search(/Q{https://monasticus.com/mlclient/examples/"
            "example}item (: a valid ) comment :), ())"
        ),
    }


def test_searchable_expression_rejects_other_values():
    with pytest.raises(TypeError) as error:
        Cts.search(1)

    assert (
        str(error.value)
        == "searchable expressions require a path string or XqyExpression"
    )


@pytest.mark.parametrize(
    ("source", "error_type", "message"),
    [
        (1, TypeError, "xpath source must be a string"),
        ("  ", ValueError, "xpath source must not be empty"),
    ],
)
def test_xpath_rejects_invalid_source_inputs(source, error_type, message):
    with pytest.raises(error_type) as error:
        xpath(source)

    assert str(error.value) == message


@pytest.mark.parametrize(
    ("namespaces", "message"),
    [
        ([], "namespaces must be a mapping of prefixes to URI strings"),
        (
            "p=https://monasticus.com/mlclient/examples/p",
            "namespaces must be a mapping of prefixes to URI strings",
        ),
        (
            {1: "https://monasticus.com/mlclient/examples/p"},
            "namespace prefixes and URIs must be strings",
        ),
        ({"p": 1}, "namespace prefixes and URIs must be strings"),
    ],
)
def test_namespace_binding_types(namespaces, message):
    with pytest.raises(TypeError) as error:
        Cts.search("/p:item").compile(namespaces=namespaces)

    assert str(error.value) == message


def test_namespace_snapshot():
    original = {
        "": "https://monasticus.com/mlclient/examples/default",
        "p": "https://monasticus.com/mlclient/examples/p",
    }
    snapshot = namespace_bindings(original)
    original["p"] = "changed"

    assert snapshot == {
        "": "https://monasticus.com/mlclient/examples/default",
        "p": "https://monasticus.com/mlclient/examples/p",
    }


def test_namespace_rejects_empty_uri():
    with pytest.raises(
        ValueError,
        match=r"^empty or reserved namespace binding: 'p'$",
    ) as error:
        namespace_bindings({"p": ""})

    assert str(error.value) == "empty or reserved namespace binding: 'p'"


@pytest.mark.parametrize("prefix", ["p:x", "p; fn:error()", "two words", "1prefix"])
def test_invalid_namespace_prefix_cannot_enter_prolog(prefix):
    with pytest.raises(
        ValueError,
        match=re.escape(f"namespace prefix must be an XML NCName: {prefix!r}"),
    ) as error:
        Cts.search("/*").compile(
            namespaces={prefix: "https://monasticus.com/mlclient/examples/test"},
        )

    assert str(error.value) == f"namespace prefix must be an XML NCName: {prefix!r}"


def test_namespace_declarations_escape_literals():
    uri = 'https://monasticus.com/mlclient/examples/"; fn:error(); (: &quoted;\t\r\n'
    expression = fn.count([])
    code, variables = expression.compile(namespaces={"p": uri})

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare namespace p = "
        '"https://monasticus.com/mlclient/examples/""; fn:error(); (: '
        '&amp;quoted;&#9;&#13;&#10;";\n'
        "fn:count(())"
    )
    assert variables == {}


def test_default_namespace_declaration():
    expression = fn.count([])
    code, variables = expression.compile(
        namespaces={"": "https://monasticus.com/mlclient/examples/default"},
    )

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare default element namespace "
        '"https://monasticus.com/mlclient/examples/default";\n'
        "fn:count(())"
    )
    assert variables == {}


def test_unicode_namespace_declaration():
    expression = fn.count([])
    code, variables = expression.compile(
        namespaces={"ż": "https://monasticus.com/mlclient/examples/z"},
    )

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare namespace ż = "
        '"https://monasticus.com/mlclient/examples/z";\n'
        "fn:count(())"
    )
    assert variables == {}
