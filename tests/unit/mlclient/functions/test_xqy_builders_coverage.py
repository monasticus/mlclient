from __future__ import annotations

import datetime

import pytest

from mlclient.functions import cts, fn, xs

_TRUE = cts.true_query()
_FALSE = cts.false_query()


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        (cts.or_query((_TRUE, _FALSE)),
         "cts:or-query((cts:true-query(), cts:false-query()))"),
        (cts.not_query(_TRUE), "cts:not-query(cts:true-query())"),
        (cts.document_query("/x"), "cts:document-query(($v0))"),
        (cts.collection_query("c"), "cts:collection-query(($v0))"),
        (cts.false_query(), "cts:false-query()"),
        (cts.uri_reference(), "cts:uri-reference()"),
        (cts.collection_reference(), "cts:collection-reference()"),
        (cts.uris(), "cts:uris(())"),
        (cts.estimate(_TRUE), "cts:estimate(cts:true-query())"),
        (fn.exists(_TRUE), "fn:exists(cts:true-query())"),
        (fn.empty(_TRUE), "fn:empty(cts:true-query())"),
    ],
)
def test_builder_compiles_to_expected_call(expr, expected):
    code, _ = expr.compile()
    assert expected in code


@pytest.mark.parametrize(
    ("expr", "fragment"),
    [
        (cts.near_query((_TRUE, _FALSE), distance=5), "cts:near-query(("),
        (cts.element_value_query(xs.qname("n"), "t"), "cts:element-value-query("),
        (cts.element_word_query(xs.qname("n"), "t"), "cts:element-word-query("),
        (cts.path_range_query("/p", ">=", 1), "cts:path-range-query("),
        (cts.json_property_value_query("name", "t"),
         "cts:json-property-value-query("),
        (cts.path_reference("/p"), "cts:path-reference("),
        (cts.json_property_reference("n"), "cts:json-property-reference("),
        (cts.field_reference("f"), "cts:field-reference("),
    ],
)
def test_builder_emits_its_function_name(expr, fragment):
    code, _ = expr.compile()
    assert fragment in code


@pytest.mark.parametrize(
    ("expr", "fragment"),
    [
        (xs.double(1.5), "xs:double($v0)"),
        (xs.decimal(3), "xs:decimal($v0)"),
        (xs.date_time("2020-01-01T00:00:00"), "xs:dateTime($v0)"),
        (xs.date("2020-01-01"), "xs:date($v0)"),
        (xs.string("x"), "xs:string($v0)"),
    ],
)
def test_xs_constructor_wraps_value_in_its_type(expr, fragment):
    code, _ = expr.compile()
    assert fragment in code


def test_and_query_ordered_flag_inlines_the_keyword():
    assert cts.and_query((_TRUE,), ordered=True).compile()[0].endswith('), "ordered")')
    assert (
        cts.and_query((_TRUE,), ordered=False).compile()[0].endswith('), "unordered")')
    )


def test_directory_query_rejects_an_unknown_depth():
    with pytest.raises(ValueError, match="directory depth"):
        cts.directory_query("/x", "2")


def test_search_without_a_query_is_rejected():
    with pytest.raises(ValueError, match="requires a query"):
        cts.search("/x")


def test_search_path_allows_doubled_quotes_inside_a_string_literal():
    code, _ = cts.search("/a[@x = 'it''s']", _TRUE).compile()
    assert code == "cts:search((/a[@x = 'it''s']), cts:true-query())"


def test_str_renders_the_compiled_body():
    assert str(_TRUE) == "cts:true-query()"


def test_inferred_casts_cover_every_scalar_type():
    code, _ = cts.element_range_query(
        xs.qname("n"), "=", (True, 1, 1.5, datetime.date(2020, 1, 1)),
    ).compile()
    assert "xs:boolean($v1)" in code
    assert "xs:integer($v2)" in code
    assert "xs:double($v3)" in code
    assert "xs:date($v4)" in code
