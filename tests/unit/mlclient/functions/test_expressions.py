from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from mlclient.functions.xqy import (
    ModuleFunctionCall,
    XqyCompilationContext,
    XqyExpression,
    cts,
    fn,
    xpath,
    xs,
)
from mlclient.functions.xqy.expressions import namespace_bindings


@pytest.mark.parametrize(
    ("args", "optionals", "suffix", "values"),
    [
        ((), (), ")", []),
        ((None,), (), ", ())", []),
        ((["a", "b"],), (), ", ($v3, $v4))", ["a", "b"]),
        (("a",), (None, "b", None), ", $v3, (), $v4)", ["a", "b"]),
        ((), (None,), ")", []),
    ],
)
def test_module_call_preserves_argument_slots(args, optionals, suffix, values):
    expression = ModuleFunctionCall(
        "normalize",
        args,
        optionals,
        namespace="https://monasticus.com/mlclient/examples/labels",
        module_path="/ext/labels.xqy",
    )

    code, variables = expression.compile()

    expected_values = [
        "https://monasticus.com/mlclient/examples/labels",
        "normalize",
        "/ext/labels.xqy",
        *values,
    ]
    assert variables == {f"v{i}": value for i, value in enumerate(expected_values)}
    assert code == (
        'xquery version "1.0-ml";\n'
        + "".join(
            f"declare variable $v{i} as xs:string external;\n"
            for i in range(len(expected_values))
        )
        + "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2)"
        + suffix
    )


@pytest.mark.parametrize("field", ["name", "namespace", "module_path"])
@pytest.mark.parametrize(
    ("value", "error"),
    [(None, TypeError), (1, TypeError), (" ", ValueError)],
)
def test_module_call_rejects_invalid_identifiers(field, value, error):
    arguments = {
        "name": "normalize",
        "namespace": "https://monasticus.com/mlclient/examples/labels",
        "module_path": "/ext/labels.xqy",
    }
    arguments[field] = value

    with pytest.raises(error, match=field):
        ModuleFunctionCall(**arguments)


@pytest.mark.parametrize("name", ["label:normalize", "1name", "normalize()", "a b"])
def test_module_call_requires_a_local_function_name(name):
    with pytest.raises(ValueError, match="NCName"):
        ModuleFunctionCall(
            name,
            namespace="https://monasticus.com/mlclient/examples/labels",
            module_path="/ext/labels.xqy",
        )


def test_module_call_snapshots_arguments_and_preserves_types():
    values = [True, Decimal("1.25")]
    args = [values]
    optionals = [fn.string_length("abc")]
    expression = ModuleFunctionCall(
        "calculate",
        args,
        optionals,
        namespace="https://monasticus.com/mlclient/examples/math",
        module_path="/ext/math.xqy",
    )
    original = expression.compile()
    values.clear()
    args.clear()
    optionals.clear()

    code, bindings = expression.compile()

    assert (code, bindings) == original
    assert bindings == {
        "v0": "https://monasticus.com/mlclient/examples/math",
        "v1": "calculate",
        "v2": "/ext/math.xqy",
        "v3": True,
        "v4": "1.25",
        "v5": "abc",
    }
    assert "declare variable $v3 as xs:boolean external;" in code
    assert "declare variable $v4 as xs:decimal external;" in code
    assert code.endswith(
        "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), "
        "($v3, $v4), fn:string-length($v5))",
    )


def test_nested_module_calls_bind_identifiers_without_shared_imports():
    namespace = 'https://monasticus.com/mlclient/examples/"; fn:error(); (: &'
    path = '/ext/"; fn:error(); (: .xqy'
    inner = ModuleFunctionCall(
        "normalize",
        ('"quoted"',),
        namespace=namespace,
        module_path=path,
    )
    expression = ModuleFunctionCall(
        "normalize",
        (inner,),
        namespace="https://monasticus.com/mlclient/examples/outer",
        module_path="/ext/outer.xqy",
    )

    code, variables = expression.compile()

    assert variables == {
        "v0": "https://monasticus.com/mlclient/examples/outer",
        "v1": "normalize",
        "v2": "/ext/outer.xqy",
        "v3": namespace,
        "v4": "normalize",
        "v5": path,
        "v6": '"quoted"',
    }
    assert code.endswith(
        "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), "
        "xdmp:apply(xdmp:function(fn:QName($v3, $v4), $v5), $v6))",
    )
    assert "import module" not in code
    assert "declare namespace" not in code
    assert namespace not in code
    assert path not in code


def test_compiler_bindings_are_read_only_snapshots():
    context = XqyCompilationContext()
    assert context.bind("original") == "$v0"
    snapshot = context.variables
    snapshot["v0"] = "changed"
    snapshot["v1"] = "injected"
    assert context.variables == {"v0": "original"}
    with pytest.raises(AttributeError):
        context.variables = {}
    assert context.bind("next") == "$v1"


def test_values_are_json_safe_and_keep_precision():
    values = [
        True,
        2**80,
        Decimal("1.234567890123456789"),
        date(2026, 1, 2),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        float("inf"),
        float("-inf"),
        float("nan"),
        1.25,
    ]
    expr = fn.count(values)
    code, variables = expr.compile()
    assert json.loads(json.dumps(variables)) == {
        "v0": True,
        "v1": str(2**80),
        "v2": "1.234567890123456789",
        "v3": "2026-01-02",
        "v4": "2026-01-02T00:00:00+00:00",
        "v5": "INF",
        "v6": "-INF",
        "v7": "NaN",
        "v8": "1.25",
    }
    assert code.startswith('xquery version "1.0-ml";\n')
    assert "declare variable $v1 as xs:integer external;" in code
    assert "declare variable $v2 as xs:decimal external;" in code
    assert "declare variable $v3 as xs:date external;" in code
    assert "declare variable $v4 as xs:dateTime external;" in code


@pytest.mark.parametrize("value", [{}, {1}, iter([1]), object()])
def test_unsupported_values_are_rejected_when_building(value):
    with pytest.raises(TypeError, match="unsupported XQuery value"):
        fn.count(value)


def test_xpath_compiles_one_guarded_body_with_readable_diagnostics():
    code, variables = fn.count(xpath("/a")).compile()
    assert variables == {"v0": "/a", "v1": "fn:count(/a)"}
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
        '            return fn:concat("[", fn:string($path/@kind), ":",\n'
        '                fn:string($path/@binding), "] ", fn:string($path)),\n'
        '            "; ")),\n'
        "        $invalid-paths)"
    )


def test_count_string_is_bound_data_without_a_path_guard():
    assert fn.count("/a").compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "fn:count($v0)",
        {"v0": "/a"},
    )


def test_values_and_source_have_separate_trust_boundaries():
    attack = "(: (( :) /), cts:false-query()), 424242, (( (: )) :)"
    code, variables = cts.search(attack, cts.true_query()).compile()
    assert attack not in code
    assert attack in variables.values()
    assert "cts:valid-extract-path" in code
    code, variables = cts.word_query(attack).compile()
    assert attack not in code
    assert variables == {"v0": attack}
    source = (
        "/Q{https://monasticus.com/mlclient/examples/example}item "
        "(: a valid ) comment :)"
    )
    assert source in cts.search(xpath(source)).compile()[1].values()


@pytest.mark.parametrize(("source", "error"), [(1, TypeError), ("  ", ValueError)])
def test_xpath_rejects_invalid_source_inputs(source, error):
    with pytest.raises(error):
        xpath(source)


def test_sequence_snapshot_and_nested_casts():
    values = ["first", [1, 2]]
    expr = xs.string(fn.count(values))
    original = expr.compile()
    values[1].append(3)
    values.append("last")
    assert expr.compile() == original
    assert "xs:string(fn:count(($v0, ($v1, $v2))))" in original[0]
    with pytest.raises(FrozenInstanceError):
        expr.fn = "fn:empty"
    original[1]["v0"] = "changed"
    assert expr.compile()[1]["v0"] == "first"


@pytest.mark.parametrize(
    ("start", "end", "error"),
    [
        (True, 2, TypeError),
        (1, False, TypeError),
        (1.5, 2, TypeError),
        (1, "2", TypeError),
        (0, 1, ValueError),
        (3, 2, ValueError),
    ],
)
def test_range_rejects_invalid_positions(start, end, error):
    with pytest.raises(error):
        cts.search().range(start, end)


@pytest.mark.parametrize(
    "expression",
    [cts.search(), cts.search().index(1), cts.search().range(1, 10)],
)
@pytest.mark.parametrize("path", ["some/child", "/some-root/some/child", "/"])
def test_xpath_does_not_wrap_calls_selected_results_or_paths(expression, path):
    context = XqyCompilationContext()
    inner = expression.render(context)
    path_ref = f"$v{len(context.variables)}"
    context = XqyCompilationContext()

    rendered = expression.xpath(path).render(context)

    assert rendered == f"{inner} ! \0{path_ref}\0"
    assert context.variables[path_ref[1:]] == path


@pytest.mark.parametrize(
    ("path", "error"),
    [(None, TypeError), ("", ValueError), ("  ", ValueError)],
)
def test_result_xpath_rejects_invalid_input(path, error):
    with pytest.raises(error, match="xpath"):
        cts.search().xpath(path)


def test_xpath_groups_compound_source():
    class Conditional(XqyExpression):
        def render(self, _ctx):
            return "if (true()) then <a/> else <b/>"

    context = XqyCompilationContext()
    expression = Conditional()

    rendered = expression.xpath("*").render(context)

    assert rendered == "(if (true()) then <a/> else <b/>) ! \0$v0\0"


@pytest.mark.parametrize(
    ("expression", "grouped"),
    [
        (cts.uris(), False),
        (cts.search(), False),
        (cts.uris().index(1), False),
        (cts.uris().range(1, 5), False),
        (
            ModuleFunctionCall(
                "normalize",
                ["coffee"],
                namespace="https://monasticus.com/mlclient/examples/labels",
                module_path="/examples/labels.xqy",
            ),
            False,
        ),
        (xpath("/product/title"), True),
        (cts.search().xpath("product/title"), True),
    ],
)
@pytest.mark.parametrize("selection", ["index", "range"])
def test_position_predicates_group_paths_but_not_function_calls(
    expression,
    grouped,
    selection,
):
    inner = expression.render(XqyCompilationContext())
    if grouped:
        inner = f"({inner})"
    if selection == "index":
        selected = expression.index(fn.last())
        predicate = "[fn:last()]"
    else:
        selected = expression.range(fn.last(), fn.last())
        predicate = "[fn:last() to fn:last()]"

    assert selected.render(XqyCompilationContext()) == inner + predicate


def test_range_composes_inside_count_and_root_defaults_to_database():
    expr = fn.count(cts.search(query=cts.false_query()).range(2, 5))
    code, variables = expr.compile()
    assert "[$v0 to $v1]" in code
    assert variables == {"v0": "2", "v1": "5"}


@pytest.mark.parametrize("position", [True, 1.5, "1", fn.count([])])
def test_index_rejects_non_positions(position):
    with pytest.raises(TypeError, match="positions"):
        cts.uris().index(position)


def test_last_stays_inside_position_predicates():
    assert str(cts.uris().index(fn.last())).endswith("cts:uris()[fn:last()]")
    assert "to fn:last()]" in str(cts.uris().range(1, fn.last()))
    assert "[fn:last() to fn:last()]" in str(
        cts.uris().range(fn.last(), fn.last()),
    )
    with pytest.raises(ValueError, match="positive"):
        cts.uris().index(0)


def test_all_nested_path_literals_are_bound_and_guarded():
    paths = ["/p:one", '/two[fn:contains(., "quote"&")]', "/a", "/b"]
    expr = fn.count(
        [
            cts.search(paths[0]),
            cts.search(paths[1]),
            cts.uris(query=cts.path_range_query(paths[2:], "=", 3)),
        ],
    )
    source, variables = expr.compile(
        namespaces={"p": "https://monasticus.com/mlclient/examples/one"},
    )
    assert all(path in variables.values() for path in paths)
    assert all(path not in source for path in paths)
    assert source.count("cts:valid-extract-path(") == 1
    assert "cts:valid-index-path(" not in source
    assert "MLCLIENT-INVALID-PATH" in source
    assert source.index("fn:empty($invalid-paths)") < source.index("xdmp:value")


@pytest.mark.parametrize(
    "namespaces",
    [
        [],
        "p=https://monasticus.com/mlclient/examples/p",
        {1: "https://monasticus.com/mlclient/examples/p"},
        {"p": 1},
    ],
)
def test_namespace_binding_types(namespaces):
    with pytest.raises(TypeError, match="namespace"):
        cts.search("/p:item").compile(namespaces=namespaces)


@pytest.mark.parametrize("prefix", ["fn", "xs", "cts", "xdmp", "map", "xml", "xmlns"])
def test_compiler_namespaces_cannot_be_rebound(prefix):
    with pytest.raises(ValueError, match="reserved"):
        fn.count([]).compile(
            namespaces={prefix: "https://monasticus.com/mlclient/examples/override"},
        )


def test_namespace_snapshot_and_empty_uri():
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
    with pytest.raises(ValueError, match="empty"):
        namespace_bindings({"p": ""})


@pytest.mark.parametrize("prefix", ["p:x", "p; fn:error()", "two words", "1prefix"])
def test_invalid_namespace_prefix_cannot_enter_prolog(prefix):
    with pytest.raises(ValueError, match="NCName"):
        cts.search("/*").compile(
            namespaces={prefix: "https://monasticus.com/mlclient/examples/test"},
        )


def test_namespace_declarations_escape_literals_and_allow_default_and_unicode():
    uri = 'https://monasticus.com/mlclient/examples/"; fn:error(); (: &quoted;\r\n'
    source, _ = fn.count([]).compile(
        namespaces={
            "p": uri,
            "": "https://monasticus.com/mlclient/examples/default",
            "ż": "https://monasticus.com/mlclient/examples/z",
        },
    )
    expected = (
        'declare namespace p = "https://monasticus.com/mlclient/examples/""; '
        'fn:error(); (: &amp;quoted;&#13;&#10;";'
    )
    assert expected in source
    assert (
        'declare default element namespace "https://monasticus.com/mlclient/examples/default";'
        in source
    )
    assert (
        'declare namespace ż = "https://monasticus.com/mlclient/examples/z";' in source
    )
    assert "xdmp:value" not in source
    assert "xdmp:with-namespaces" not in source


@pytest.mark.parametrize(
    ("bindings", "expected"),
    [
        ({}, "map:new(())"),
        ({"p": "https://monasticus.com/mlclient/examples/p"}, "map:entry($v1, $v2)"),
        (
            {
                "p": "https://monasticus.com/mlclient/examples/p",
                "q": "https://monasticus.com/mlclient/examples/q",
            },
            "map:new((map:entry($v1, $v2), map:entry($v3, $v4)))",
        ),
    ],
)
def test_reference_namespace_map_uses_entry_directly_for_one_binding(
    bindings,
    expected,
):
    source, _ = cts.path_reference("/item", namespaces=bindings).compile()

    assert source.endswith(f"cts:path-reference($v0, (), {expected})")


def test_reference_namespace_map_is_snapshotted_without_code_path_validation():
    bindings = {"p": "https://monasticus.com/mlclient/examples/local"}
    expression = cts.path_reference("/p:item", namespaces=bindings)
    bindings["p"] = "changed"
    source, variables = expression.compile(
        namespaces={"p": "https://monasticus.com/mlclient/examples/global"},
    )
    assert (
        'declare namespace p = "https://monasticus.com/mlclient/examples/global";'
        in source
    )
    assert "https://monasticus.com/mlclient/examples/local" in variables.values()
    assert "changed" not in variables.values()
    assert "map:entry(" in source
    assert "map:new(" not in source
    assert "cts:valid-" not in source
    assert "xdmp:value" not in source
