from __future__ import annotations

import pytest

from mlclient.functions.xqy import cts, fn, xpath, xs
from mlclient.functions.xqy._expr import _CompileContext


@pytest.mark.parametrize(
    ("expr", "native", "bindings"),
    [
        (cts.directory_query("/x/"), "cts:directory-query", ["/x/", "1"]),
        (cts.and_query([], options="ordered"), "cts:and-query", ["ordered"]),
        (cts.or_query([], options="synonym"), "cts:or-query", ["synonym"]),
        (cts.not_query(cts.false_query()), "cts:not-query", []),
        (
            cts.near_query([], distance=2, distance_weight=0.5),
            "cts:near-query",
            ["2", "0.5"],
        ),
        (
            cts.directory_query("/x/", xs.string("infinity")),
            "cts:directory-query",
            ["/x/", "infinity"],
        ),
        (cts.document_query("/x"), "cts:document-query", ["/x"]),
        (cts.collection_query("x"), "cts:collection-query", ["x"]),
        (cts.document_root_query("x"), "cts:document-root-query", ["x"]),
        (cts.element_value_query("x"), "cts:element-value-query", ["x"]),
        (
            cts.element_word_query(["a", "b"], "x"),
            "cts:element-word-query",
            ["a", "b", "x"],
        ),
        (
            cts.element_range_query("a", xs.string(">"), 3),
            "cts:element-range-query",
            ["a", ">", "3"],
        ),
        (cts.path_range_query("/a", "=", 3), "cts:path-range-query", ["/a", "=", "3"]),
        (
            cts.json_property_value_query("x", True),
            "cts:json-property-value-query",
            ["x", True],
        ),
        (
            cts.path_reference("/p:x", namespaces=xpath("map:map()")),
            "cts:path-reference",
            ["/p:x"],
        ),
        (cts.json_property_reference("x"), "cts:json-property-reference", ["x"]),
        (cts.field_reference("x"), "cts:field-reference", ["x"]),
        (cts.collection_reference(), "cts:collection-reference", []),
        (cts.uri_reference(), "cts:uri-reference", []),
        (cts.search(quality_weight=0, forest_ids=[123]), "cts:search", ["0", "123"]),
        (
            cts.uris(start="a", quality_weight=0, forest_ids=[123]),
            "cts:uris",
            ["a", "0", "123"],
        ),
        (
            cts.values(
                cts.uri_reference(),
                start="a",
                quality_weight=0,
                forest_ids=[123],
            ),
            "cts:values",
            ["a", "0", "123"],
        ),
        (
            cts.estimate(maximum=20, quality_weight=0, forest_ids=[123]),
            "cts:estimate",
            ["0", "123", "20"],
        ),
        (fn.count([1], maximum=1), "fn:count", ["1", "1"]),
        (fn.exists([]), "fn:exists", []),
        (fn.empty([]), "fn:empty", []),
        (xs.integer("1"), "xs:integer", ["1"]),
        (xs.date("2026-01-01"), "xs:date", ["2026-01-01"]),
        (xs.date_time("2026-01-01T00:00:00"), "xs:dateTime", ["2026-01-01T00:00:00"]),
    ],
)
def test_existing_builders_preserve_native_arguments(expr, native, bindings):
    context = _CompileContext()
    code = expr.render(context)
    variables = context.variables
    assert native + "(" in code
    assert list(variables.values()) == bindings


def test_late_arguments_keep_native_position():
    assert str(cts.estimate(maximum=5)).endswith(
        "cts:estimate((), (), (), (), xs:double(xs:integer($v0)))",
    )
    assert str(cts.near_query([], distance_weight=1.5)).endswith(
        "cts:near-query((), (), (), xs:double($v0))",
    )
    assert cts.path_reference("/x", namespaces=xpath("map:map()")).render(
        _CompileContext(),
    ).endswith(
        "cts:path-reference($v0, (), (map:map()))",
    )
