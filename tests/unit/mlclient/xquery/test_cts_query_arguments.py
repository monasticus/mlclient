"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import datetime
import json

import pytest

from mlclient.xquery import FunctionCall, cts, fn, xs


def test_prefixed_qname_requires_compilation_bindings():
    with pytest.raises(TypeError) as error:
        cts.element_word_query("t:title", "blue").serialize()

    assert str(error.value) == (
        "cts:element-word-query: element: Prefixed CTS QNames require compilation "
        "namespace bindings; use fn.qname(uri, name) for local serialization."
    )


def test_computed_qname_requires_server_evaluation():
    with pytest.raises(TypeError) as error:
        cts.element_word_query(fn.node_name(fn.doc("/a.xml")), "blue").serialize()

    assert str(error.value) == (
        "cts:element-word-query: element: CTS QName argument requires server "
        "evaluation, got fn:node-name(fn:doc('/a.xml'))."
    )


def test_computed_value_requires_server_evaluation():
    with pytest.raises(TypeError) as error:
        cts.element_range_query("price", ">", fn.count(fn.doc())).serialize()

    assert str(error.value) == (
        "cts:element-range-query: value: CTS value argument requires server "
        "evaluation, got fn:count(fn:doc())."
    )


def test_unsupported_json_property_value_type():
    query = cts.json_property_value_query("day", datetime.date(2026, 1, 1))

    with pytest.raises(ValueError, match="Unsupported local JSON") as error:
        query.serialize()

    assert str(error.value) == (

        "cts:json-property-value-query: value: Unsupported local JSON property "
        "value type: xs:date"

    )


def test_single_value_argument_rejects_sequences():
    with pytest.raises(ValueError, match="exactly one value") as error:
        cts.document_format_query(["json", "xml"]).serialize()

    assert str(error.value) == (
        "cts:document-format-query: format: CTS argument requires exactly one "
        "value for local serialization."
    )


def test_unsupported_region_requires_server_evaluation():
    query = cts.element_geospatial_query(
        "origin",
        cts.linestring([cts.point(0, 0), cts.point(1, 1)]),
    )

    with pytest.raises(TypeError) as error:
        query.serialize()

    assert str(error.value) == (
        "cts:element-geospatial-query: region: CTS region argument requires server "
        "evaluation, got cts:linestring([Point(latitude_or_wkt=0, longitude=0), "
        "Point(latitude_or_wkt=1, longitude=1)])."
    )


def test_point_text_requires_server_evaluation():
    with pytest.raises(TypeError) as error:
        cts.element_geospatial_query("origin", cts.point("10,20")).serialize()

    assert str(error.value) == (
        "cts:element-geospatial-query: region: CTS point given as WKT text "
        "requires server evaluation."
    )


def test_nonfinite_coordinate():
    with pytest.raises(ValueError, match="must be finite") as error:
        cts.element_geospatial_query(
            "origin",
            cts.point(float("nan"), 0),
        ).serialize()

    assert str(error.value) == (
        "cts:element-geospatial-query: region: CTS numbers must be finite for "
        "local serialization."
    )


def test_computed_period_requires_server_evaluation():
    query = cts.period_range_query("valid", "aln_before", period=fn.doc("/p.xml"))

    with pytest.raises(TypeError) as error:
        query.serialize()

    assert str(error.value) == (
        "cts:period-range-query: period: CTS period argument requires server "
        "evaluation, got fn:doc('/p.xml')."
    )


def test_nested_error_names_every_enclosing_query_and_the_argument():
    query = cts.and_query(
        [cts.word_query("blue"), cts.not_query(cts.word_query(fn.string("x")))],
    )

    with pytest.raises(TypeError) as error:
        query.to_xml()

    assert str(error.value) == (

        "cts:and-query: queries: cts:not-query: query: cts:word-query: text: CTS "
        "string argument requires server evaluation, got fn:string('x')."

    )


def test_error_subclass_is_reported_with_its_context():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ("{not json",)))

    with pytest.raises(
        ValueError,
        match=r"^cts:reverse-query: nodes: Expecting",
    ) as error:
        query.to_json()

    argument_error = error.value.__cause__
    assert isinstance(argument_error.__cause__, json.JSONDecodeError)


def test_malformed_literal_xml_is_reported_with_its_context():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ("<a><b></a>",)))

    with pytest.raises(ValueError, match="not well-formed") as error:
        query.to_xml()

    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS literal XML is not well-formed: "
        "mismatched tag: line 1, column 8"
    )


@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            cts.and_query([], options=xs.string("bogus")),
            "cts:and-query: options ['bogus'] are not and-query options; "
            "use at most one of ordered, unordered",
        ),
        (
            cts.or_query([], options=xs.string("ordered")),
            "cts:or-query: options ['ordered'] are not or-query options; "
            "use at most one of synonym",
        ),
    ],
)
def test_options_resolved_from_expressions_are_checked_when_serialized(
    query,
    message,
):
    with pytest.raises(ValueError, match="are not") as error:
        query.to_json()

    assert str(error.value) == message


@pytest.mark.parametrize(
    "build",
    [
        lambda: cts.period_compare_query("system", "bogus", "valid"),
        lambda: cts.period_range_query("valid", "bogus"),
    ],
)
def test_unsupported_literal_temporal_operator_is_rejected(build):
    with pytest.raises(ValueError, match="temporal operator") as error:
        build()

    assert str(error.value) == "unsupported temporal operator: 'bogus'"


@pytest.mark.parametrize("method", ["to_json", "to_xml", "to_combined_query"])
@pytest.mark.parametrize(
    "value",
    [
        xs.integer(1.9),
        xs.date("2026-01-01"),
        FunctionCall("xs:double", (1.5,)),
        FunctionCall("xs:boolean", ("1",)),
        FunctionCall("xs:boolean", ("0",)),
        cts.uris(),
    ],
)
def test_function_values_compile_but_cannot_serialize(method, value):
    query = cts.element_range_query("value", "=", value)
    code, _ = query.compile()
    assert value.fn + "(" in code

    with pytest.raises(TypeError, match="value argument requires server evaluation"):
        getattr(query, method)()


@pytest.mark.parametrize("method", ["to_json", "to_xml", "to_combined_query"])
@pytest.mark.parametrize("value", ["1", "0"])
def test_json_property_boolean_cast_requires_server_evaluation(method, value):
    query = cts.json_property_value_query("v", FunctionCall("xs:boolean", (value,)))

    with pytest.raises(TypeError, match="value argument requires server evaluation"):
        getattr(query, method)()
