from dataclasses import FrozenInstanceError

import pytest

from mlclient.functions.xqy import fn, xs


def test_sequence_snapshots_nested_values():
    values = ["first", [1, 2]]
    expression = xs.string(fn.count(values))
    values[1].append(3)
    values.append("last")

    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:integer external;\n"
        "declare variable $v2 as xs:integer external;\n"
        "xs:string(fn:count(($v0, ($v1, $v2))))"
    )
    assert variables == {"v0": "first", "v1": "1", "v2": "2"}


def test_existing_cast_is_preserved():
    expression = xs.string(fn.count([]))

    assert xs.string(expression) is expression


def test_sequence_bindings_are_independent():
    expression = xs.string(fn.count(["first", [1, 2]]))
    _, variables = expression.compile()
    variables["v0"] = "changed"

    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:integer external;\n"
        "declare variable $v2 as xs:integer external;\n"
        "xs:string(fn:count(($v0, ($v1, $v2))))"
    )
    assert variables == {"v0": "first", "v1": "1", "v2": "2"}


def test_function_call_is_frozen():
    expression = xs.string(fn.count([]))

    with pytest.raises(FrozenInstanceError) as error:
        expression.fn = "fn:empty"

    assert str(error.value) == "cannot assign to field 'fn'"
