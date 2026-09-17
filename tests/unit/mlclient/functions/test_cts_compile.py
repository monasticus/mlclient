from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from mlclient.calls import EvalCall
from mlclient.functions import cts, fn, xpath, xs


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
    body = EvalCall(xquery=code, variables=variables).body
    assert json.loads(body["vars"]) == {
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
    assert "xs:integer($v1)" in code
    assert "xs:decimal($v2)" in code
    assert "xs:date($v3)" in code
    assert "xs:dateTime($v4)" in code


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity")])
def test_nonfinite_decimals_are_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        xs.decimal(value)


@pytest.mark.parametrize("value", [{}, {1}, iter([1]), object()])
def test_unsupported_values_are_rejected_when_building(value):
    with pytest.raises(TypeError, match="unsupported XQuery value"):
        fn.count(value)


def test_values_and_source_have_separate_trust_boundaries():
    attack = "(: (( :) /), cts:false-query()), 424242, (( (: )) :)"
    with pytest.raises(TypeError, match="xpath"):
        cts.search(attack, cts.true_query())
    code, variables = cts.word_query(attack).compile()
    assert attack not in code
    assert variables == {"v0": attack}
    source = "/Q{urn:example}item (: a valid ) comment :)"
    assert source in cts.search(xpath(source)).compile()[0]


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
    assert (
        "xs:string(fn:count(($v0, (xs:integer($v1), xs:integer($v2)))))" in original[0]
    )
    with pytest.raises(FrozenInstanceError):
        expr.fn = "fn:empty"
    original[1]["v0"] = "changed"
    assert expr.compile()[1]["v0"] == "first"


@pytest.mark.parametrize(
    "options",
    ["unstemmed", ["unstemmed"], ("unstemmed",), xs.string("unstemmed")],
)
def test_options_never_split_strings_into_characters(options):
    _, variables = cts.word_query("needle", options=options).compile()
    assert list(variables.values()) == ["needle", "unstemmed"]


def test_qname_sequences_and_namespaced_nested_arguments():
    expr = cts.element_value_query(
        ["a", xs.qname(xs.string("b"), uri=xs.string("urn:x"))],
        ["one", "two"],
    )
    code, variables = expr.compile()
    assert "(xs:QName($v0), fn:QName(xs:string($v1), xs:string($v2)))" in code
    assert list(variables.values()) == ["a", "urn:x", "b", "one", "two"]


def test_point_uses_wkt_as_text_and_numeric_coordinates_as_floats():
    wkt_code, wkt_variables = cts.point("POINT (20 10)").compile()
    point_code, point_variables = cts.point(10, 20).compile()

    assert wkt_code.endswith("cts:point($v0)")
    assert wkt_variables == {"v0": "POINT (20 10)"}
    assert point_code.endswith(
        "cts:point(xs:float(xs:integer($v0)), xs:float(xs:integer($v1)))",
    )
    assert point_variables == {"v0": "10", "v1": "20"}


def test_point_accepts_composable_coordinate_expressions():
    code, _ = cts.point(xs.double(10), xs.double(20)).compile()

    assert code.endswith(
        "cts:point(xs:double(xs:integer($v0)), xs:double(xs:integer($v1)))",
    )


def test_double_sequences_are_not_cast_as_singletons():
    code, variables = cts.percentile([1, 2], [0.25, 0.75]).compile()

    assert code.endswith(
        "cts:percentile((xs:integer($v0), xs:integer($v1)), "
        "(xs:double($v2), xs:double($v3)))",
    )
    assert list(variables.values()) == ["1", "2", "0.25", "0.75"]


def test_optional_range_operator_is_validated_when_present():
    with pytest.raises(ValueError, match="unsupported range operator"):
        cts.column_range_query("s", "v", "c", 1, operator="contains")

    code, _ = cts.column_range_query("s", "v", "c", 1, operator=">=").compile()
    assert "xs:string($v4)" in code


@pytest.mark.parametrize("operator", ["sameTerm", ["=", "=", "<"], (), []])
def test_triple_operators_preserve_native_sequences(operator):
    expr = cts.triple_range_query([], [], 1, operator=operator)
    code, variables = expr.compile()
    assert list(variables.values()) == [
        "1",
        *([operator] if isinstance(operator, str) else operator),
    ]
    assert "cts:triple-range-query((), (), xs:integer($v0), " in code


def test_geospatial_co_occurrences_keeps_required_native_slots():
    code, variables = cts.geospatial_co_occurrences("first", "second").compile()
    assert code.endswith(
        "cts:geospatial-co-occurrences(xs:QName($v0), xs:QName(()), "
        "xs:QName(()), xs:QName($v1))",
    )
    assert list(variables.values()) == ["first", "second"]


def test_omitted_optional_slots_are_distinct_from_empty_sequences():
    assert str(cts.estimate()).endswith("cts:estimate(())")
    assert str(cts.uris()).endswith("cts:uris()")
    assert str(cts.word_query("x")).endswith("cts:word-query($v0)")
    assert str(cts.word_query("x", options=[])).endswith("cts:word-query($v0, ())")
    assert str(cts.word_query("x", weight=xs.double(2))).endswith(
        "cts:word-query($v0, (), xs:double(xs:double(xs:integer($v1))))",
    )


@pytest.mark.parametrize(
    ("lo", "hi", "error"),
    [
        (True, 2, TypeError),
        (1, False, TypeError),
        (1.5, 2, TypeError),
        (1, "2", TypeError),
        (0, 1, ValueError),
        (3, 2, ValueError),
    ],
)
def test_window_rejects_invalid_positions(lo, hi, error):
    with pytest.raises(error):
        cts.search().window(lo, hi)


def test_window_composes_inside_count_and_root_defaults_to_database():
    expr = fn.count(cts.search(query=cts.false_query()).window(2, 5))
    assert str(expr).endswith("fn:count((cts:search((/), cts:false-query()))[2 to 5])")


@pytest.mark.parametrize("operator", ["=<", "bad"])
def test_invalid_range_operators(operator):
    with pytest.raises(ValueError, match="range operator"):
        cts.element_range_query("price", operator, 1)


def test_invalid_directory_depth():
    with pytest.raises(ValueError, match="directory depth"):
        cts.directory_query("/test/", "2")
