from __future__ import annotations

from decimal import Decimal

import pytest

from mlclient.xquery import ModuleFunctionCall, fn


@pytest.mark.parametrize(
    ("args", "optionals", "suffix", "values"),
    [
        ((), (), ")", []),
        ((None,), (), ", ())", []),
        ((["a", "b"],), (), ", ($v3, $v4))", ["a", "b"]),
        ((("a", "b"),), (), ", ($v3, $v4))", ["a", "b"]),
        ((["a", ("b", None)],), (), ", ($v3, ($v4, ())))", ["a", "b"]),
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

    with pytest.raises(error) as raised:
        ModuleFunctionCall(**arguments)

    suffix = "must not be blank" if error is ValueError else "must be a string"
    assert str(raised.value) == f"{field} {suffix}"


@pytest.mark.parametrize("name", ["label:normalize", "1name", "normalize()", "a b"])
def test_module_call_requires_a_local_function_name(name):
    with pytest.raises(
        ValueError,
        match=r"^function name must be an XML NCName without a prefix$",
    ) as error:
        ModuleFunctionCall(
            name,
            namespace="https://monasticus.com/mlclient/examples/labels",
            module_path="/ext/labels.xqy",
        )

    assert str(error.value) == "function name must be an XML NCName without a prefix"


def test_module_call_snapshots_arguments():
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
    values.clear()
    args.clear()
    optionals.clear()

    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "declare variable $v3 as xs:boolean external;\n"
        "declare variable $v4 as xs:decimal external;\n"
        "declare variable $v5 as xs:string external;\n"
        "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), ($v3, "
        "$v4), fn:string-length($v5))"
    )
    assert variables == {
        "v0": "https://monasticus.com/mlclient/examples/math",
        "v1": "calculate",
        "v2": "/ext/math.xqy",
        "v3": True,
        "v4": "1.25",
        "v5": "abc",
    }


def test_module_call_preserves_argument_types():
    expression = ModuleFunctionCall(
        "calculate",
        [[True, Decimal("1.25")]],
        [fn.string_length("abc")],
        namespace="https://monasticus.com/mlclient/examples/math",
        module_path="/ext/math.xqy",
    )
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "declare variable $v3 as xs:boolean external;\n"
        "declare variable $v4 as xs:decimal external;\n"
        "declare variable $v5 as xs:string external;\n"
        "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), ($v3, "
        "$v4), fn:string-length($v5))"
    )
    assert variables == {
        "v0": "https://monasticus.com/mlclient/examples/math",
        "v1": "calculate",
        "v2": "/ext/math.xqy",
        "v3": True,
        "v4": "1.25",
        "v5": "abc",
    }


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

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "declare variable $v3 as xs:string external;\n"
        "declare variable $v4 as xs:string external;\n"
        "declare variable $v5 as xs:string external;\n"
        "declare variable $v6 as xs:string external;\n"
        "xdmp:apply(xdmp:function(fn:QName($v0, $v1), $v2), "
        "xdmp:apply(xdmp:function(fn:QName($v3, $v4), $v5), $v6))"
    )
    assert variables == {
        "v0": "https://monasticus.com/mlclient/examples/outer",
        "v1": "normalize",
        "v2": "/ext/outer.xqy",
        "v3": 'https://monasticus.com/mlclient/examples/"; fn:error(); (: &',
        "v4": "normalize",
        "v5": '/ext/"; fn:error(); (: .xqy',
        "v6": '"quoted"',
    }
