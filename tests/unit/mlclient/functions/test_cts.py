from __future__ import annotations

import pytest

from mlclient.functions.xqy import XqyCompilationContext, cts, fn, xs
from tests.utils.expressions import StaticExpression


@pytest.mark.parametrize(
    "options",
    ["unstemmed", ["unstemmed"], ("unstemmed",), xs.string("unstemmed")],
)
def test_options_never_split_strings_into_characters(options):
    _, variables = cts.word_query("needle", options=options).compile()
    assert list(variables.values()) == ["needle", "unstemmed"]


def test_qname_sequences_and_namespaced_nested_arguments():
    expr = cts.element_value_query(
        [
            "a",
            fn.qname(
                xs.string("https://monasticus.com/mlclient/examples/x"),
                xs.string("b"),
            ),
        ],
        ["one", "two"],
    )
    code, variables = expr.compile()
    assert "(xs:QName($v0), fn:QName(xs:string($v1), xs:string($v2)))" in code
    assert list(variables.values()) == [
        "a",
        "https://monasticus.com/mlclient/examples/x",
        "b",
        "one",
        "two",
    ]


def test_point_preserves_wkt_and_uses_typed_numeric_coordinates():
    wkt_code, wkt_variables = cts.point("POINT (20 10)").compile()
    point_code, point_variables = cts.point(10, 20).compile()

    assert wkt_code.endswith("cts:point($v0)")
    assert wkt_variables == {"v0": "POINT (20 10)"}
    assert point_code.endswith(
        "cts:point($v0, $v1)",
    )
    assert point_variables == {"v0": "10", "v1": "20"}


def test_point_accepts_composable_coordinate_expressions():
    code, _ = cts.point(xs.double(10), xs.double(20)).compile()

    assert code.endswith(
        "cts:point(xs:double($v0), xs:double($v1))",
    )


def test_double_sequences_are_not_cast_as_singletons():
    code, variables = cts.percentile([1, 2], [0.25, 0.75]).compile()

    assert code.endswith(
        "cts:percentile(($v0, $v1), ($v2, $v3))",
    )
    assert list(variables.values()) == ["1", "2", "0.25", "0.75"]


def test_optional_range_operator_is_validated_when_present():
    with pytest.raises(ValueError, match="unsupported range operator"):
        cts.column_range_query("s", "v", "c", 1, operator="contains")

    code, _ = cts.column_range_query("s", "v", "c", 1, operator=">=").compile()
    assert "xs:string($v4)" in code


def test_optional_operator_none_preserves_native_argument_slots():
    omitted = cts.column_range_query("s", "v", "c", 1)
    explicit = cts.column_range_query("s", "v", "c", 1, operator=None)
    assert explicit.compile() == omitted.compile()
    assert str(explicit).endswith("cts:column-range-query($v0, $v1, $v2, $v3)")
    code, variables = cts.column_range_query(
        "s",
        "v",
        "c",
        1,
        operator=None,
        options="cached",
    ).compile()
    assert code.endswith("cts:column-range-query($v0, $v1, $v2, $v3, (), $v4)")
    assert variables["v4"] == "cached"


def test_required_operator_none_is_rejected():
    with pytest.raises(ValueError, match="unsupported range operator: None"):
        cts.path_range_query("/price", None, 10)


@pytest.mark.parametrize("operator", ["sameTerm", ["=", "=", "<"], (), []])
def test_triple_operators_preserve_native_sequences(operator):
    expr = cts.triple_range_query([], [], 1, operator=operator)
    code, variables = expr.compile()
    assert list(variables.values()) == [
        "1",
        *([operator] if isinstance(operator, str) else operator),
    ]
    assert "cts:triple-range-query((), (), $v0, " in code


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
        "cts:word-query($v0, (), xs:double($v1))",
    )


@pytest.mark.parametrize("operator", ["=<", "bad"])
def test_invalid_range_operators(operator):
    with pytest.raises(ValueError, match="range operator"):
        cts.element_range_query("price", operator, 1)


def test_invalid_directory_depth():
    with pytest.raises(ValueError, match="directory depth"):
        cts.directory_query("/test/", "2")


@pytest.mark.parametrize(
    ("expression", "expected", "variables"),
    [
        (
            cts.directory_query("/x/"),
            "cts:directory-query($v0, xs:string($v1))",
            {"v0": "/x/", "v1": "1"},
        ),
        (
            cts.and_query([], options="ordered"),
            "cts:and-query((), $v0)",
            {"v0": "ordered"},
        ),
        (
            cts.or_query([], options="synonym"),
            "cts:or-query((), $v0)",
            {"v0": "synonym"},
        ),
        (cts.not_query(cts.false_query()), "cts:not-query(cts:false-query())", {}),
        (
            cts.near_query([], distance=2, distance_weight=0.5),
            "cts:near-query((), xs:double($v0), (), $v1)",
            {"v0": "2", "v1": "0.5"},
        ),
        (
            cts.directory_query("/x/", xs.string("infinity")),
            "cts:directory-query($v0, xs:string($v1))",
            {"v0": "/x/", "v1": "infinity"},
        ),
        (cts.document_query("/x"), "cts:document-query($v0)", {"v0": "/x"}),
        (cts.collection_query("x"), "cts:collection-query($v0)", {"v0": "x"}),
        (
            cts.document_root_query("x"),
            "cts:document-root-query(xs:QName($v0))",
            {"v0": "x"},
        ),
        (
            cts.element_value_query("x"),
            "cts:element-value-query(xs:QName($v0))",
            {"v0": "x"},
        ),
        (
            cts.element_word_query(["a", "b"], "x"),
            "cts:element-word-query((xs:QName($v0), xs:QName($v1)), $v2)",
            {"v0": "a", "v1": "b", "v2": "x"},
        ),
        (
            cts.element_range_query("a", xs.string(">"), 3),
            "cts:element-range-query(xs:QName($v0), xs:string($v1), $v2)",
            {"v0": "a", "v1": ">", "v2": "3"},
        ),
        (
            cts.path_range_query("/a", "=", 3),
            "cts:path-range-query($v0, xs:string($v1), $v2)",
            {"v0": "/a", "v1": "=", "v2": "3"},
        ),
        (
            cts.json_property_value_query("x", True),
            "cts:json-property-value-query($v0, $v1)",
            {"v0": "x", "v1": True},
        ),
        (
            cts.path_reference("/p:x", namespaces=StaticExpression("map:map()")),
            "cts:path-reference($v0, (), (map:map()))",
            {"v0": "/p:x"},
        ),
        (
            cts.json_property_reference("x"),
            "cts:json-property-reference($v0)",
            {"v0": "x"},
        ),
        (cts.field_reference("x"), "cts:field-reference($v0)", {"v0": "x"}),
        (cts.collection_reference(), "cts:collection-reference()", {}),
        (cts.uri_reference(), "cts:uri-reference()", {}),
        (
            cts.search(quality_weight=0, forest_ids=[123]),
            "cts:search(/, (), (), xs:double($v0), ($v1))",
            {"v0": "0", "v1": "123"},
        ),
        (
            cts.uris(start="a", quality_weight=0, forest_ids=[123]),
            "cts:uris($v0, (), (), xs:double($v1), ($v2))",
            {"v0": "a", "v1": "0", "v2": "123"},
        ),
        (
            cts.values(
                cts.uri_reference(),
                start="a",
                quality_weight=0,
                forest_ids=[123],
            ),
            "cts:values(cts:uri-reference(), $v0, (), (), xs:double($v1), ($v2))",
            {"v0": "a", "v1": "0", "v2": "123"},
        ),
        (
            cts.estimate(maximum=20, quality_weight=0, forest_ids=[123]),
            "cts:estimate((), (), xs:double($v0), ($v1), xs:double($v2))",
            {"v0": "0", "v1": "123", "v2": "20"},
        ),
    ],
)
def test_render_literal_arguments(expression, expected, variables):
    context = XqyCompilationContext()
    assert expression.render(context) == expected
    assert context.variables == variables


@pytest.mark.parametrize(
    "expression",
    [
        cts.geospatial_path_reference("/a"),
        cts.geospatial_region_path_reference("/a"),
        cts.path_geospatial_query("/a", cts.point(10, 20)),
        cts.path_range_query(["/a", "/b"], "=", 1),
        cts.path_reference("/a"),
        cts.estimate(cts.path_range_query("/a", "=", 1)),
    ],
)
def test_native_string_paths_are_bound_without_code_validation(expression):
    code, variables = expression.compile()
    assert "/a" in variables.values()
    assert "/a" not in code
    assert "cts:valid-" not in code
    assert "xdmp:value" not in code


def test_late_arguments_keep_native_position():
    assert str(cts.estimate(maximum=5)).endswith(
        "cts:estimate((), (), (), (), xs:double($v0))",
    )
    assert str(cts.near_query([], distance_weight=1.5)).endswith(
        "cts:near-query((), (), (), $v0)",
    )
    assert (
        cts.path_reference("/x", namespaces=StaticExpression("map:map()"))
        .render(
            XqyCompilationContext(),
        )
        .endswith(
            "cts:path-reference($v0, (), (map:map()))",
        )
    )


@pytest.mark.parametrize(
    ("expression", "body", "variables"),
    [
        pytest.param(
            cts.after_query(timestamp=xs.string("timestamp")),
            "cts:after-query(xs:string($v0))",
            {"v0": "timestamp"},
            id="after_query",
        ),
        pytest.param(
            cts.aggregate(
                native_plugin=xs.string("native_plugin"),
                aggregate_name=xs.string("aggregate_name"),
                range_indexes=xs.string("range_indexes"),
                argument=xs.string("argument"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:aggregate(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4), xs:string($v5), xs:string($v6))"
            ),
            {
                "v0": "native_plugin",
                "v1": "aggregate_name",
                "v2": "range_indexes",
                "v3": "argument",
                "v4": "options",
                "v5": "query",
                "v6": "forest_ids",
            },
            id="aggregate",
        ),
        pytest.param(
            cts.and_not_query(
                positive_query=xs.string("positive_query"),
                negative_query=xs.string("negative_query"),
            ),
            "cts:and-not-query(xs:string($v0), xs:string($v1))",
            {"v0": "positive_query", "v1": "negative_query"},
            id="and_not_query",
        ),
        pytest.param(
            cts.and_query(queries=xs.string("queries"), options=xs.string("options")),
            "cts:and-query(xs:string($v0), xs:string($v1))",
            {"v0": "queries", "v1": "options"},
            id="and_query",
        ),
        pytest.param(
            cts.avg_aggregate(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:avg-aggregate(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="avg_aggregate",
        ),
        pytest.param(
            cts.before_query(timestamp=xs.string("timestamp")),
            "cts:before-query(xs:string($v0))",
            {"v0": "timestamp"},
            id="before_query",
        ),
        pytest.param(
            cts.boost_query(
                matching_query=xs.string("matching_query"),
                boosting_query=xs.string("boosting_query"),
            ),
            "cts:boost-query(xs:string($v0), xs:string($v1))",
            {"v0": "matching_query", "v1": "boosting_query"},
            id="boost_query",
        ),
        pytest.param(
            cts.box(
                south=xs.string("south"),
                west=xs.string("west"),
                north=xs.string("north"),
                east=xs.string("east"),
            ),
            (
                "cts:box(xs:float(xs:string($v0)), xs:float(xs:string($v1)), "
                "xs:float(xs:string($v2)), xs:float(xs:string($v3)))"
            ),
            {"v0": "south", "v1": "west", "v2": "north", "v3": "east"},
            id="box",
        ),
        pytest.param(
            cts.circle(radius=xs.string("radius"), center=xs.string("center")),
            "cts:circle(xs:double(xs:string($v0)), xs:string($v1))",
            {"v0": "radius", "v1": "center"},
            id="circle",
        ),
        pytest.param(
            cts.classify(
                data_nodes=xs.string("data_nodes"),
                classifier=xs.string("classifier"),
                options=xs.string("options"),
                training_nodes=xs.string("training_nodes"),
            ),
            (
                "cts:classify(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {
                "v0": "data_nodes",
                "v1": "classifier",
                "v2": "options",
                "v3": "training_nodes",
            },
            id="classify",
        ),
        pytest.param(
            cts.cluster(nodes=xs.string("nodes"), options=xs.string("options")),
            "cts:cluster(xs:string($v0), xs:string($v1))",
            {"v0": "nodes", "v1": "options"},
            id="cluster",
        ),
        pytest.param(
            cts.collection_match(
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:collection-match(xs:string($v0), xs:string($v1), xs:string($v2),"
                " xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "pattern",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="collection_match",
        ),
        pytest.param(
            cts.collection_query(uris=xs.string("uris")),
            "cts:collection-query(xs:string($v0))",
            {"v0": "uris"},
            id="collection_query",
        ),
        pytest.param(
            cts.collection_reference(options=xs.string("options")),
            "cts:collection-reference(xs:string($v0))",
            {"v0": "options"},
            id="collection_reference",
        ),
        pytest.param(
            cts.collections(
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:collections(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "start",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="collections",
        ),
        pytest.param(
            cts.column_range_query(
                schema=xs.string("schema"),
                view=xs.string("view"),
                column=xs.string("column"),
                value=xs.string("value"),
                operator=xs.string("operator"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:column-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), xs:string($v5), "
                "xs:double(xs:string($v6)))"
            ),
            {
                "v0": "schema",
                "v1": "view",
                "v2": "column",
                "v3": "value",
                "v4": "operator",
                "v5": "options",
                "v6": "weight",
            },
            id="column_range_query",
        ),
        pytest.param(
            cts.complex_polygon(outer=xs.string("outer"), inner=xs.string("inner")),
            "cts:complex-polygon(xs:string($v0), xs:string($v1))",
            {"v0": "outer", "v1": "inner"},
            id="complex_polygon",
        ),
        pytest.param(
            cts.confidence(node=xs.string("node")),
            "cts:confidence(xs:string($v0))",
            {"v0": "node"},
            id="confidence",
        ),
        pytest.param(
            cts.confidence_order(options=xs.string("options")),
            "cts:confidence-order(xs:string($v0))",
            {"v0": "options"},
            id="confidence_order",
        ),
        pytest.param(
            cts.contains(nodes=xs.string("nodes"), query=xs.string("query")),
            "cts:contains(xs:string($v0), xs:string($v1))",
            {"v0": "nodes", "v1": "query"},
            id="contains",
        ),
        pytest.param(
            cts.correlation(
                value1=xs.string("value1"),
                value2=xs.string("value2"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:correlation(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4))"
            ),
            {
                "v0": "value1",
                "v1": "value2",
                "v2": "options",
                "v3": "query",
                "v4": "forest_ids",
            },
            id="correlation",
        ),
        pytest.param(
            cts.count_aggregate(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:count-aggregate(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="count_aggregate",
        ),
        pytest.param(
            cts.covariance(
                value1=xs.string("value1"),
                value2=xs.string("value2"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:covariance(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4))"
            ),
            {
                "v0": "value1",
                "v1": "value2",
                "v2": "options",
                "v3": "query",
                "v4": "forest_ids",
            },
            id="covariance",
        ),
        pytest.param(
            cts.covariance_p(
                value1=xs.string("value1"),
                value2=xs.string("value2"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:covariance-p(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4))"
            ),
            {
                "v0": "value1",
                "v1": "value2",
                "v2": "options",
                "v3": "query",
                "v4": "forest_ids",
            },
            id="covariance_p",
        ),
        pytest.param(
            cts.deregister(id=xs.string("id")),
            "cts:deregister(xs:string($v0))",
            {"v0": "id"},
            id="deregister",
        ),
        pytest.param(
            cts.directory_query(uris=xs.string("uris"), depth=xs.string("depth")),
            "cts:directory-query(xs:string($v0), xs:string($v1))",
            {"v0": "uris", "v1": "depth"},
            id="directory_query",
        ),
        pytest.param(
            cts.distinctive_terms(
                nodes=xs.string("nodes"),
                options=xs.string("options"),
            ),
            "cts:distinctive-terms(xs:string($v0), xs:string($v1))",
            {"v0": "nodes", "v1": "options"},
            id="distinctive_terms",
        ),
        pytest.param(
            cts.document_format_query(format=xs.string("format")),
            "cts:document-format-query(xs:string($v0))",
            {"v0": "format"},
            id="document_format_query",
        ),
        pytest.param(
            cts.document_fragment_query(query=xs.string("query")),
            "cts:document-fragment-query(xs:string($v0))",
            {"v0": "query"},
            id="document_fragment_query",
        ),
        pytest.param(
            cts.document_order(options=xs.string("options")),
            "cts:document-order(xs:string($v0))",
            {"v0": "options"},
            id="document_order",
        ),
        pytest.param(
            cts.document_permission_query(
                role=xs.string("role"),
                capability=xs.string("capability"),
            ),
            "cts:document-permission-query(xs:string($v0), xs:string($v1))",
            {"v0": "role", "v1": "capability"},
            id="document_permission_query",
        ),
        pytest.param(
            cts.document_query(uris=xs.string("uris")),
            "cts:document-query(xs:string($v0))",
            {"v0": "uris"},
            id="document_query",
        ),
        pytest.param(
            cts.document_root_query(root=xs.string("root")),
            "cts:document-root-query(xs:string($v0))",
            {"v0": "root"},
            id="document_root_query",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_boxes(
                parent_element_names=xs.string("parent_element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                latitude_bounds=xs.string("latitude_bounds"),
                longitude_bounds=xs.string("longitude_bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-pair-geospatial-boxes(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:string($v6), xs:double(xs:string($v7)), "
                "xs:string($v8))"
            ),
            {
                "v0": "parent_element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "latitude_bounds",
                "v4": "longitude_bounds",
                "v5": "options",
                "v6": "query",
                "v7": "quality_weight",
                "v8": "forest_ids",
            },
            id="element_attribute_pair_geospatial_boxes",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_query(
                element_name=xs.string("element_name"),
                latitude_attribute_names=xs.string("latitude_attribute_names"),
                longitude_attribute_names=xs.string("longitude_attribute_names"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-attribute-pair-geospatial-query(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)))"
            ),
            {
                "v0": "element_name",
                "v1": "latitude_attribute_names",
                "v2": "longitude_attribute_names",
                "v3": "regions",
                "v4": "options",
                "v5": "weight",
            },
            id="element_attribute_pair_geospatial_query",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_value_match(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-pair-geospatial-value-match(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "pattern",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_attribute_pair_geospatial_value_match",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_values(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-pair-geospatial-values(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "start",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_attribute_pair_geospatial_values",
        ),
        pytest.param(
            cts.element_attribute_range_query(
                element_name=xs.string("element_name"),
                attribute_name=xs.string("attribute_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-attribute-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)))"
            ),
            {
                "v0": "element_name",
                "v1": "attribute_name",
                "v2": "operator",
                "v3": "value",
                "v4": "options",
                "v5": "weight",
            },
            id="element_attribute_range_query",
        ),
        pytest.param(
            cts.element_attribute_reference(
                element=xs.string("element"),
                attribute=xs.string("attribute"),
                options=xs.string("options"),
            ),
            (
                "cts:element-attribute-reference(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "element", "v1": "attribute", "v2": "options"},
            id="element_attribute_reference",
        ),
        pytest.param(
            cts.element_attribute_value_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                attribute_name_1=xs.string("attribute_name_1"),
                element_name_2=xs.string("element_name_2"),
                attribute_name_2=xs.string("attribute_name_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-value-co-occurrences(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "element_name_1",
                "v1": "attribute_name_1",
                "v2": "element_name_2",
                "v3": "attribute_name_2",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_attribute_value_co_occurrences",
        ),
        pytest.param(
            cts.element_attribute_value_geospatial_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                attribute_name_1=xs.string("attribute_name_1"),
                geo_element_name=xs.string("geo_element_name"),
                coord_child_name_1=xs.string("coord_child_name_1"),
                coord_child_name_2=xs.string("coord_child_name_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-value-geospatial-co-occurrences(xs:string($v0),"
                " xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:string($v6), xs:double(xs:string($v7)), "
                "xs:string($v8))"
            ),
            {
                "v0": "element_name_1",
                "v1": "attribute_name_1",
                "v2": "geo_element_name",
                "v3": "coord_child_name_1",
                "v4": "coord_child_name_2",
                "v5": "options",
                "v6": "query",
                "v7": "quality_weight",
                "v8": "forest_ids",
            },
            id="element_attribute_value_geospatial_co_occurrences",
        ),
        pytest.param(
            cts.element_attribute_value_match(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-value-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "attribute_names",
                "v2": "pattern",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_attribute_value_match",
        ),
        pytest.param(
            cts.element_attribute_value_query(
                element_name=xs.string("element_name"),
                attribute_name=xs.string("attribute_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-attribute-value-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "element_name",
                "v1": "attribute_name",
                "v2": "text",
                "v3": "options",
                "v4": "weight",
            },
            id="element_attribute_value_query",
        ),
        pytest.param(
            cts.element_attribute_value_ranges(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                bounds=xs.string("bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-value-ranges(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "attribute_names",
                "v2": "bounds",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_attribute_value_ranges",
        ),
        pytest.param(
            cts.element_attribute_values(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-values(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "attribute_names",
                "v2": "start",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_attribute_values",
        ),
        pytest.param(
            cts.element_attribute_word_match(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-word-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "attribute_names",
                "v2": "pattern",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_attribute_word_match",
        ),
        pytest.param(
            cts.element_attribute_word_query(
                element_name=xs.string("element_name"),
                attribute_name=xs.string("attribute_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-attribute-word-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "element_name",
                "v1": "attribute_name",
                "v2": "text",
                "v3": "options",
                "v4": "weight",
            },
            id="element_attribute_word_query",
        ),
        pytest.param(
            cts.element_attribute_words(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-attribute-words(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "attribute_names",
                "v2": "start",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_attribute_words",
        ),
        pytest.param(
            cts.element_child_geospatial_boxes(
                parent_element_names=xs.string("parent_element_names"),
                child_element_names=xs.string("child_element_names"),
                latitude_bounds=xs.string("latitude_bounds"),
                longitude_bounds=xs.string("longitude_bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-child-geospatial-boxes(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), xs:string($v5), "
                "xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "parent_element_names",
                "v1": "child_element_names",
                "v2": "latitude_bounds",
                "v3": "longitude_bounds",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_child_geospatial_boxes",
        ),
        pytest.param(
            cts.element_child_geospatial_query(
                parent_element_name=xs.string("parent_element_name"),
                child_element_names=xs.string("child_element_names"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-child-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "parent_element_name",
                "v1": "child_element_names",
                "v2": "regions",
                "v3": "options",
                "v4": "weight",
            },
            id="element_child_geospatial_query",
        ),
        pytest.param(
            cts.element_child_geospatial_value_match(
                element_names=xs.string("element_names"),
                child_names=xs.string("child_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-child-geospatial-value-match(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "child_names",
                "v2": "pattern",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_child_geospatial_value_match",
        ),
        pytest.param(
            cts.element_child_geospatial_values(
                element_names=xs.string("element_names"),
                child_names=xs.string("child_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-child-geospatial-values(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "child_names",
                "v2": "start",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_child_geospatial_values",
        ),
        pytest.param(
            cts.element_geospatial_boxes(
                element_names=xs.string("element_names"),
                latitude_bounds=xs.string("latitude_bounds"),
                longitude_bounds=xs.string("longitude_bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-geospatial-boxes(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)), xs:string($v6))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_bounds",
                "v2": "longitude_bounds",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="element_geospatial_boxes",
        ),
        pytest.param(
            cts.element_geospatial_query(
                element_name=xs.string("element_name"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "element_name", "v1": "regions", "v2": "options", "v3": "weight"},
            id="element_geospatial_query",
        ),
        pytest.param(
            cts.element_geospatial_value_match(
                element_names=xs.string("element_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-geospatial-value-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_geospatial_value_match",
        ),
        pytest.param(
            cts.element_geospatial_values(
                element_names=xs.string("element_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-geospatial-values(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_geospatial_values",
        ),
        pytest.param(
            cts.element_pair_geospatial_boxes(
                parent_element_names=xs.string("parent_element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                latitude_bounds=xs.string("latitude_bounds"),
                longitude_bounds=xs.string("longitude_bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-pair-geospatial-boxes(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), xs:string($v5), "
                "xs:string($v6), xs:double(xs:string($v7)), xs:string($v8))"
            ),
            {
                "v0": "parent_element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "latitude_bounds",
                "v4": "longitude_bounds",
                "v5": "options",
                "v6": "query",
                "v7": "quality_weight",
                "v8": "forest_ids",
            },
            id="element_pair_geospatial_boxes",
        ),
        pytest.param(
            cts.element_pair_geospatial_query(
                element_name=xs.string("element_name"),
                latitude_element_names=xs.string("latitude_element_names"),
                longitude_element_names=xs.string("longitude_element_names"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-pair-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)))"
            ),
            {
                "v0": "element_name",
                "v1": "latitude_element_names",
                "v2": "longitude_element_names",
                "v3": "regions",
                "v4": "options",
                "v5": "weight",
            },
            id="element_pair_geospatial_query",
        ),
        pytest.param(
            cts.element_pair_geospatial_value_match(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-pair-geospatial-value-match(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "pattern",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_pair_geospatial_value_match",
        ),
        pytest.param(
            cts.element_pair_geospatial_values(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-pair-geospatial-values(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), xs:string($v5), "
                "xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "start",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_pair_geospatial_values",
        ),
        pytest.param(
            cts.element_query(
                element_name=xs.string("element_name"),
                query=xs.string("query"),
            ),
            "cts:element-query(xs:string($v0), xs:string($v1))",
            {"v0": "element_name", "v1": "query"},
            id="element_query",
        ),
        pytest.param(
            cts.element_range_query(
                element_name=xs.string("element_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "element_name",
                "v1": "operator",
                "v2": "value",
                "v3": "options",
                "v4": "weight",
            },
            id="element_range_query",
        ),
        pytest.param(
            cts.element_reference(
                element=xs.string("element"),
                options=xs.string("options"),
            ),
            "cts:element-reference(xs:string($v0), xs:string($v1))",
            {"v0": "element", "v1": "options"},
            id="element_reference",
        ),
        pytest.param(
            cts.element_value_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                element_name_2=xs.string("element_name_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-value-co-occurrences(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "element_name_1",
                "v1": "element_name_2",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_value_co_occurrences",
        ),
        pytest.param(
            cts.element_value_geospatial_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                geo_element_name=xs.string("geo_element_name"),
                coord_child_name_1=xs.string("coord_child_name_1"),
                coord_child_name_2=xs.string("coord_child_name_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-value-geospatial-co-occurrences(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:string($v5), xs:double(xs:string($v6)), xs:string($v7))"
            ),
            {
                "v0": "element_name_1",
                "v1": "geo_element_name",
                "v2": "coord_child_name_1",
                "v3": "coord_child_name_2",
                "v4": "options",
                "v5": "query",
                "v6": "quality_weight",
                "v7": "forest_ids",
            },
            id="element_value_geospatial_co_occurrences",
        ),
        pytest.param(
            cts.element_value_match(
                element_names=xs.string("element_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-value-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_value_match",
        ),
        pytest.param(
            cts.element_value_query(
                element_name=xs.string("element_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-value-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "element_name", "v1": "text", "v2": "options", "v3": "weight"},
            id="element_value_query",
        ),
        pytest.param(
            cts.element_value_ranges(
                element_names=xs.string("element_names"),
                bounds=xs.string("bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-value-ranges(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "bounds",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_value_ranges",
        ),
        pytest.param(
            cts.element_values(
                element_names=xs.string("element_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-values(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_values",
        ),
        pytest.param(
            cts.element_walk(
                node=xs.string("node"),
                element=xs.string("element"),
                expr=xs.string("expr"),
            ),
            "cts:element-walk(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "node", "v1": "element", "v2": "expr"},
            id="element_walk",
        ),
        pytest.param(
            cts.element_word_match(
                element_names=xs.string("element_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-word-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_word_match",
        ),
        pytest.param(
            cts.element_word_query(
                element_name=xs.string("element_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:element-word-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "element_name", "v1": "text", "v2": "options", "v3": "weight"},
            id="element_word_query",
        ),
        pytest.param(
            cts.element_words(
                element_names=xs.string("element_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:element-words(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "element_names",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="element_words",
        ),
        pytest.param(
            cts.entity(
                id=xs.string("id"),
                normalized_text=xs.string("normalized_text"),
                text=xs.string("text"),
                type=xs.string("type"),
            ),
            (
                "cts:entity(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "id", "v1": "normalized_text", "v2": "text", "v3": "type"},
            id="entity",
        ),
        pytest.param(
            cts.entity_dictionary(
                entities=xs.string("entities"),
                options=xs.string("options"),
            ),
            "cts:entity-dictionary(xs:string($v0), xs:string($v1))",
            {"v0": "entities", "v1": "options"},
            id="entity_dictionary",
        ),
        pytest.param(
            cts.entity_dictionary_get(uri=xs.string("uri")),
            "cts:entity-dictionary-get(xs:string($v0))",
            {"v0": "uri"},
            id="entity_dictionary_get",
        ),
        pytest.param(
            cts.entity_dictionary_parse(
                contents=xs.string("contents"),
                options=xs.string("options"),
            ),
            "cts:entity-dictionary-parse(xs:string($v0), xs:string($v1))",
            {"v0": "contents", "v1": "options"},
            id="entity_dictionary_parse",
        ),
        pytest.param(
            cts.entity_highlight(
                node=xs.string("node"),
                expr=xs.string("expr"),
                dict=xs.string("dict"),
            ),
            "cts:entity-highlight(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "node", "v1": "expr", "v2": "dict"},
            id="entity_highlight",
        ),
        pytest.param(
            cts.entity_walk(
                node=xs.string("node"),
                expr=xs.string("expr"),
                dict=xs.string("dict"),
            ),
            "cts:entity-walk(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "node", "v1": "expr", "v2": "dict"},
            id="entity_walk",
        ),
        pytest.param(
            cts.estimate(
                query=xs.string("query"),
                options=xs.string("options"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
                maximum=xs.string("maximum"),
            ),
            (
                "cts:estimate(xs:string($v0), xs:string($v1), "
                "xs:double(xs:string($v2)), xs:string($v3), "
                "xs:double(xs:string($v4)))"
            ),
            {
                "v0": "query",
                "v1": "options",
                "v2": "quality_weight",
                "v3": "forest_ids",
                "v4": "maximum",
            },
            id="estimate",
        ),
        pytest.param(cts.false_query(), "cts:false-query()", {}, id="false_query"),
        pytest.param(
            cts.field_range_query(
                field_name=xs.string("field_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:field-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "field_name",
                "v1": "operator",
                "v2": "value",
                "v3": "options",
                "v4": "weight",
            },
            id="field_range_query",
        ),
        pytest.param(
            cts.field_reference(field=xs.string("field"), options=xs.string("options")),
            "cts:field-reference(xs:string($v0), xs:string($v1))",
            {"v0": "field", "v1": "options"},
            id="field_reference",
        ),
        pytest.param(
            cts.field_value_co_occurrences(
                field_name_1=xs.string("field_name_1"),
                field_name_2=xs.string("field_name_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:field-value-co-occurrences(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "field_name_1",
                "v1": "field_name_2",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="field_value_co_occurrences",
        ),
        pytest.param(
            cts.field_value_match(
                field_names=xs.string("field_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:field-value-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "field_names",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="field_value_match",
        ),
        pytest.param(
            cts.field_value_query(
                field_name=xs.string("field_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:field-value-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "field_name", "v1": "text", "v2": "options", "v3": "weight"},
            id="field_value_query",
        ),
        pytest.param(
            cts.field_value_ranges(
                field_names=xs.string("field_names"),
                bounds=xs.string("bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:field-value-ranges(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "field_names",
                "v1": "bounds",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="field_value_ranges",
        ),
        pytest.param(
            cts.field_values(
                field_names=xs.string("field_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:field-values(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "field_names",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="field_values",
        ),
        pytest.param(
            cts.field_word_match(
                field_names=xs.string("field_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:field-word-match(xs:string($v0), xs:string($v1), xs:string($v2),"
                " xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "field_names",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="field_word_match",
        ),
        pytest.param(
            cts.field_word_query(
                field_name=xs.string("field_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:field-word-query(xs:string($v0), xs:string($v1), xs:string($v2),"
                " xs:double(xs:string($v3)))"
            ),
            {"v0": "field_name", "v1": "text", "v2": "options", "v3": "weight"},
            id="field_word_query",
        ),
        pytest.param(
            cts.field_words(
                field_names=xs.string("field_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:field-words(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "field_names",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="field_words",
        ),
        pytest.param(
            cts.fitness(node=xs.string("node")),
            "cts:fitness(xs:string($v0))",
            {"v0": "node"},
            id="fitness",
        ),
        pytest.param(
            cts.fitness_order(options=xs.string("options")),
            "cts:fitness-order(xs:string($v0))",
            {"v0": "options"},
            id="fitness_order",
        ),
        pytest.param(
            cts.frequency(value=xs.string("value")),
            "cts:frequency(xs:string($v0))",
            {"v0": "value"},
            id="frequency",
        ),
        pytest.param(
            cts.geospatial_attribute_pair_reference(
                element=xs.string("element"),
                lat=xs.string("lat"),
                long=xs.string("long"),
                options=xs.string("options"),
            ),
            (
                "cts:geospatial-attribute-pair-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {"v0": "element", "v1": "lat", "v2": "long", "v3": "options"},
            id="geospatial_attribute_pair_reference",
        ),
        pytest.param(
            cts.geospatial_boxes(
                geo_indexes=xs.string("geo_indexes"),
                latitude_bounds=xs.string("latitude_bounds"),
                longitude_bounds=xs.string("longitude_bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:geospatial-boxes(xs:string($v0), xs:string($v1), xs:string($v2),"
                " xs:string($v3), xs:string($v4), xs:double(xs:string($v5)), "
                "xs:string($v6))"
            ),
            {
                "v0": "geo_indexes",
                "v1": "latitude_bounds",
                "v2": "longitude_bounds",
                "v3": "options",
                "v4": "query",
                "v5": "quality_weight",
                "v6": "forest_ids",
            },
            id="geospatial_boxes",
        ),
        pytest.param(
            cts.geospatial_co_occurrences(
                geo_element_name_1=xs.string("geo_element_name_1"),
                geo_element_name_2=xs.string("geo_element_name_2"),
                child_1_name_1=xs.string("child_1_name_1"),
                child_1_name_2=xs.string("child_1_name_2"),
                child_2_name_1=xs.string("child_2_name_1"),
                child_2_name_2=xs.string("child_2_name_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:geospatial-co-occurrences(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), xs:string($v5), "
                "xs:string($v6), xs:string($v7), xs:double(xs:string($v8)), "
                "xs:string($v9))"
            ),
            {
                "v0": "geo_element_name_1",
                "v1": "child_1_name_1",
                "v2": "child_1_name_2",
                "v3": "geo_element_name_2",
                "v4": "child_2_name_1",
                "v5": "child_2_name_2",
                "v6": "options",
                "v7": "query",
                "v8": "quality_weight",
                "v9": "forest_ids",
            },
            id="geospatial_co_occurrences",
        ),
        pytest.param(
            cts.geospatial_element_child_reference(
                element=xs.string("element"),
                child=xs.string("child"),
                options=xs.string("options"),
            ),
            (
                "cts:geospatial-element-child-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "element", "v1": "child", "v2": "options"},
            id="geospatial_element_child_reference",
        ),
        pytest.param(
            cts.geospatial_element_pair_reference(
                element=xs.string("element"),
                lat=xs.string("lat"),
                long=xs.string("long"),
                options=xs.string("options"),
            ),
            (
                "cts:geospatial-element-pair-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {"v0": "element", "v1": "lat", "v2": "long", "v3": "options"},
            id="geospatial_element_pair_reference",
        ),
        pytest.param(
            cts.geospatial_element_reference(
                element=xs.string("element"),
                options=xs.string("options"),
            ),
            "cts:geospatial-element-reference(xs:string($v0), xs:string($v1))",
            {"v0": "element", "v1": "options"},
            id="geospatial_element_reference",
        ),
        pytest.param(
            cts.geospatial_json_property_child_reference(
                property=xs.string("property"),
                child=xs.string("child"),
                options=xs.string("options"),
            ),
            (
                "cts:geospatial-json-property-child-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "property", "v1": "child", "v2": "options"},
            id="geospatial_json_property_child_reference",
        ),
        pytest.param(
            cts.geospatial_json_property_pair_reference(
                property=xs.string("property"),
                lat=xs.string("lat"),
                long=xs.string("long"),
                options=xs.string("options"),
            ),
            (
                "cts:geospatial-json-property-pair-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {"v0": "property", "v1": "lat", "v2": "long", "v3": "options"},
            id="geospatial_json_property_pair_reference",
        ),
        pytest.param(
            cts.geospatial_json_property_reference(
                property=xs.string("property"),
                options=xs.string("options"),
            ),
            "cts:geospatial-json-property-reference(xs:string($v0), xs:string($v1))",
            {"v0": "property", "v1": "options"},
            id="geospatial_json_property_reference",
        ),
        pytest.param(
            cts.geospatial_path_reference(
                path_expression=xs.string("path_expression"),
                options=xs.string("options"),
                map=xs.string("map"),
            ),
            (
                "cts:geospatial-path-reference(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "path_expression", "v1": "options", "v2": "map"},
            id="geospatial_path_reference",
        ),
        pytest.param(
            cts.geospatial_region_path_reference(
                path_expression=xs.string("path_expression"),
                options=xs.string("options"),
                namespaces=xs.string("namespaces"),
                geohash_precision=xs.string("geohash_precision"),
                units=xs.string("units"),
                invalid_values=xs.string("invalid_values"),
            ),
            (
                "cts:geospatial-region-path-reference(xs:string($v0), xs:string($v1),"
                " xs:string($v2), xs:string($v3), xs:string($v4), xs:string($v5))"
            ),
            {
                "v0": "path_expression",
                "v1": "options",
                "v2": "namespaces",
                "v3": "geohash_precision",
                "v4": "units",
                "v5": "invalid_values",
            },
            id="geospatial_region_path_reference",
        ),
        pytest.param(
            cts.geospatial_region_query(
                geospatial_region_reference=xs.string("geospatial_region_reference"),
                operation=xs.string("operation"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:geospatial-region-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "geospatial_region_reference",
                "v1": "operation",
                "v2": "regions",
                "v3": "options",
                "v4": "weight",
            },
            id="geospatial_region_query",
        ),
        pytest.param(
            cts.highlight(
                node=xs.string("node"),
                query=xs.string("query"),
                expr=xs.string("expr"),
            ),
            "cts:highlight(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "node", "v1": "query", "v2": "expr"},
            id="highlight",
        ),
        pytest.param(
            cts.index_order(index=xs.string("index"), options=xs.string("options")),
            "cts:index-order(xs:string($v0), xs:string($v1))",
            {"v0": "index", "v1": "options"},
            id="index_order",
        ),
        pytest.param(
            cts.iri_reference(),
            "cts:iri-reference()",
            {},
            id="iri_reference",
        ),
        pytest.param(
            cts.json_property_child_geospatial_query(
                parent_property_name=xs.string("parent_property_name"),
                child_property_names=xs.string("child_property_names"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:json-property-child-geospatial-query(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), "
                "xs:double(xs:string($v4)))"
            ),
            {
                "v0": "parent_property_name",
                "v1": "child_property_names",
                "v2": "regions",
                "v3": "options",
                "v4": "weight",
            },
            id="json_property_child_geospatial_query",
        ),
        pytest.param(
            cts.json_property_geospatial_query(
                property_name=xs.string("property_name"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:json-property-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "property_name", "v1": "regions", "v2": "options", "v3": "weight"},
            id="json_property_geospatial_query",
        ),
        pytest.param(
            cts.json_property_pair_geospatial_query(
                property_name=xs.string("property_name"),
                latitude_property_names=xs.string("latitude_property_names"),
                longitude_property_names=xs.string("longitude_property_names"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:json-property-pair-geospatial-query(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)))"
            ),
            {
                "v0": "property_name",
                "v1": "latitude_property_names",
                "v2": "longitude_property_names",
                "v3": "regions",
                "v4": "options",
                "v5": "weight",
            },
            id="json_property_pair_geospatial_query",
        ),
        pytest.param(
            cts.json_property_range_query(
                property_name=xs.string("property_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:json-property-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "property_name",
                "v1": "operator",
                "v2": "value",
                "v3": "options",
                "v4": "weight",
            },
            id="json_property_range_query",
        ),
        pytest.param(
            cts.json_property_reference(
                property=xs.string("property"),
                options=xs.string("options"),
            ),
            "cts:json-property-reference(xs:string($v0), xs:string($v1))",
            {"v0": "property", "v1": "options"},
            id="json_property_reference",
        ),
        pytest.param(
            cts.json_property_scope_query(
                property_name=xs.string("property_name"),
                query=xs.string("query"),
            ),
            "cts:json-property-scope-query(xs:string($v0), xs:string($v1))",
            {"v0": "property_name", "v1": "query"},
            id="json_property_scope_query",
        ),
        pytest.param(
            cts.json_property_value_query(
                property_name=xs.string("property_name"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:json-property-value-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "property_name", "v1": "value", "v2": "options", "v3": "weight"},
            id="json_property_value_query",
        ),
        pytest.param(
            cts.json_property_word_match(
                property_names=xs.string("property_names"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:json-property-word-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "property_names",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="json_property_word_match",
        ),
        pytest.param(
            cts.json_property_word_query(
                property_name=xs.string("property_name"),
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:json-property-word-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "property_name", "v1": "text", "v2": "options", "v3": "weight"},
            id="json_property_word_query",
        ),
        pytest.param(
            cts.json_property_words(
                property_names=xs.string("property_names"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:json-property-words(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "property_names",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="json_property_words",
        ),
        pytest.param(
            cts.linear_model(
                values=xs.string("values"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:linear-model(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "values", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="linear_model",
        ),
        pytest.param(
            cts.linestring(vertices=xs.string("vertices")),
            "cts:linestring(xs:string($v0))",
            {"v0": "vertices"},
            id="linestring",
        ),
        pytest.param(
            cts.locks_fragment_query(query=xs.string("query")),
            "cts:locks-fragment-query(xs:string($v0))",
            {"v0": "query"},
            id="locks_fragment_query",
        ),
        pytest.param(
            cts.lsqt_query(
                temporal_collection=xs.string("temporal_collection"),
                timestamp=xs.string("timestamp"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:lsqt-query(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)))"
            ),
            {
                "v0": "temporal_collection",
                "v1": "timestamp",
                "v2": "options",
                "v3": "weight",
            },
            id="lsqt_query",
        ),
        pytest.param(
            cts.match_regions(
                range_indexes=xs.string("range_indexes"),
                operation=xs.string("operation"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:match-regions(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4), xs:string($v5))"
            ),
            {
                "v0": "range_indexes",
                "v1": "operation",
                "v2": "regions",
                "v3": "options",
                "v4": "query",
                "v5": "forest_ids",
            },
            id="match_regions",
        ),
        pytest.param(
            cts.max(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            "cts:max(xs:string($v0), xs:string($v1), xs:string($v2), xs:string($v3))",
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="max",
        ),
        pytest.param(
            cts.median(arg=xs.string("arg")),
            "cts:median(xs:string($v0))",
            {"v0": "arg"},
            id="median",
        ),
        pytest.param(
            cts.min(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            "cts:min(xs:string($v0), xs:string($v1), xs:string($v2), xs:string($v3))",
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="min",
        ),
        pytest.param(
            cts.near_query(
                queries=xs.string("queries"),
                distance=xs.string("distance"),
                options=xs.string("options"),
                distance_weight=xs.string("distance_weight"),
            ),
            (
                "cts:near-query(xs:string($v0), xs:double(xs:string($v1)), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {
                "v0": "queries",
                "v1": "distance",
                "v2": "options",
                "v3": "distance_weight",
            },
            id="near_query",
        ),
        pytest.param(
            cts.not_in_query(
                positive_query=xs.string("positive_query"),
                negative_query=xs.string("negative_query"),
            ),
            "cts:not-in-query(xs:string($v0), xs:string($v1))",
            {"v0": "positive_query", "v1": "negative_query"},
            id="not_in_query",
        ),
        pytest.param(
            cts.not_query(query=xs.string("query")),
            "cts:not-query(xs:string($v0))",
            {"v0": "query"},
            id="not_query",
        ),
        pytest.param(
            cts.or_query(queries=xs.string("queries"), options=xs.string("options")),
            "cts:or-query(xs:string($v0), xs:string($v1))",
            {"v0": "queries", "v1": "options"},
            id="or_query",
        ),
        pytest.param(
            cts.parse(query=xs.string("query"), bindings=xs.string("bindings")),
            "cts:parse(xs:string($v0), xs:string($v1))",
            {"v0": "query", "v1": "bindings"},
            id="parse",
        ),
        pytest.param(
            cts.part_of_speech(token=xs.string("token")),
            "cts:part-of-speech(xs:string($v0))",
            {"v0": "token"},
            id="part_of_speech",
        ),
        pytest.param(
            cts.path_geospatial_query(
                path_expression=xs.string("path_expression"),
                regions=xs.string("regions"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:path-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:double(xs:string($v3)))"
            ),
            {"v0": "path_expression", "v1": "regions", "v2": "options", "v3": "weight"},
            id="path_geospatial_query",
        ),
        pytest.param(
            cts.path_range_query(
                path_expression=xs.string("path_expression"),
                operator=xs.string("operator"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:path-range-query(xs:string($v0), xs:string($v1), xs:string($v2),"
                " xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "path_expression",
                "v1": "operator",
                "v2": "value",
                "v3": "options",
                "v4": "weight",
            },
            id="path_range_query",
        ),
        pytest.param(
            cts.path_reference(
                path_expression=xs.string("path_expression"),
                options=xs.string("options"),
                namespaces=xs.string("namespaces"),
            ),
            "cts:path-reference(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "path_expression", "v1": "options", "v2": "namespaces"},
            id="path_reference",
        ),
        pytest.param(
            cts.percent_rank(
                arg=xs.string("arg"),
                value=xs.string("value"),
                options=xs.string("options"),
            ),
            "cts:percent-rank(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "arg", "v1": "value", "v2": "options"},
            id="percent_rank",
        ),
        pytest.param(
            cts.percentile(arg=xs.string("arg"), p=xs.string("p")),
            "cts:percentile(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "p"},
            id="percentile",
        ),
        pytest.param(
            cts.period(start=xs.string("start"), end=xs.string("end")),
            "cts:period(xs:string($v0), xs:string($v1))",
            {"v0": "start", "v1": "end"},
            id="period",
        ),
        pytest.param(
            cts.period_compare(
                period_1=xs.string("period_1"),
                operator=xs.string("operator"),
                period_2=xs.string("period_2"),
            ),
            "cts:period-compare(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "period_1", "v1": "operator", "v2": "period_2"},
            id="period_compare",
        ),
        pytest.param(
            cts.period_compare_query(
                axis_1=xs.string("axis_1"),
                operator=xs.string("operator"),
                axis_2=xs.string("axis_2"),
                options=xs.string("options"),
            ),
            (
                "cts:period-compare-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3))"
            ),
            {"v0": "axis_1", "v1": "operator", "v2": "axis_2", "v3": "options"},
            id="period_compare_query",
        ),
        pytest.param(
            cts.period_range_query(
                axis_name=xs.string("axis_name"),
                operator=xs.string("operator"),
                period=xs.string("period"),
                options=xs.string("options"),
            ),
            (
                "cts:period-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3))"
            ),
            {"v0": "axis_name", "v1": "operator", "v2": "period", "v3": "options"},
            id="period_range_query",
        ),
        pytest.param(
            cts.point(
                latitude_or_wkt=xs.string("latitude_or_wkt"),
                longitude=xs.string("longitude"),
            ),
            "cts:point(xs:string($v0), xs:string($v1))",
            {"v0": "latitude_or_wkt", "v1": "longitude"},
            id="point",
        ),
        pytest.param(
            cts.polygon(vertices=xs.string("vertices")),
            "cts:polygon(xs:string($v0))",
            {"v0": "vertices"},
            id="polygon",
        ),
        pytest.param(
            cts.properties_fragment_query(query=xs.string("query")),
            "cts:properties-fragment-query(xs:string($v0))",
            {"v0": "query"},
            id="properties_fragment_query",
        ),
        pytest.param(
            cts.quality(node=xs.string("node")),
            "cts:quality(xs:string($v0))",
            {"v0": "node"},
            id="quality",
        ),
        pytest.param(
            cts.quality_order(options=xs.string("options")),
            "cts:quality-order(xs:string($v0))",
            {"v0": "options"},
            id="quality_order",
        ),
        pytest.param(
            cts.query(query=xs.string("query")),
            "cts:query(xs:string($v0))",
            {"v0": "query"},
            id="query",
        ),
        pytest.param(
            cts.range_query(
                index=xs.string("index"),
                operator=xs.string("operator"),
                value=xs.string("value"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:range-query(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)))"
            ),
            {
                "v0": "index",
                "v1": "operator",
                "v2": "value",
                "v3": "options",
                "v4": "weight",
            },
            id="range_query",
        ),
        pytest.param(
            cts.rank(
                arg=xs.string("arg"),
                value=xs.string("value"),
                options=xs.string("options"),
            ),
            "cts:rank(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "arg", "v1": "value", "v2": "options"},
            id="rank",
        ),
        pytest.param(
            cts.reference_parse(reference=xs.string("reference")),
            "cts:reference-parse(xs:string($v0))",
            {"v0": "reference"},
            id="reference_parse",
        ),
        pytest.param(
            cts.register(query=xs.string("query")),
            "cts:register(xs:string($v0))",
            {"v0": "query"},
            id="register",
        ),
        pytest.param(
            cts.registered_query(
                ids=xs.string("ids"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:registered-query(xs:string($v0), xs:string($v1), "
                "xs:double(xs:string($v2)))"
            ),
            {"v0": "ids", "v1": "options", "v2": "weight"},
            id="registered_query",
        ),
        pytest.param(
            cts.relevance_info(
                node=xs.string("node"),
                output_kind=xs.string("output_kind"),
            ),
            "cts:relevance-info(xs:string($v0), xs:string($v1))",
            {"v0": "node", "v1": "output_kind"},
            id="relevance_info",
        ),
        pytest.param(
            cts.remainder(node=xs.string("node")),
            "cts:remainder(xs:string($v0))",
            {"v0": "node"},
            id="remainder",
        ),
        pytest.param(
            cts.reverse_query(nodes=xs.string("nodes"), weight=xs.string("weight")),
            "cts:reverse-query(xs:string($v0), xs:double(xs:string($v1)))",
            {"v0": "nodes", "v1": "weight"},
            id="reverse_query",
        ),
        pytest.param(
            cts.score(node=xs.string("node")),
            "cts:score(xs:string($v0))",
            {"v0": "node"},
            id="score",
        ),
        pytest.param(
            cts.score_order(options=xs.string("options")),
            "cts:score-order(xs:string($v0))",
            {"v0": "options"},
            id="score_order",
        ),
        pytest.param(
            cts.search(
                expression=xs.string("expression"),
                query=xs.string("query"),
                options=xs.string("options"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:search(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "expression",
                "v1": "query",
                "v2": "options",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="search",
        ),
        pytest.param(
            cts.similar_query(
                nodes=xs.string("nodes"),
                weight=xs.string("weight"),
                options=xs.string("options"),
            ),
            (
                "cts:similar-query(xs:string($v0), xs:double(xs:string($v1)), "
                "xs:string($v2))"
            ),
            {"v0": "nodes", "v1": "weight", "v2": "options"},
            id="similar_query",
        ),
        pytest.param(
            cts.stddev(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:stddev(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="stddev",
        ),
        pytest.param(
            cts.stddev_p(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:stddev-p(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="stddev_p",
        ),
        pytest.param(
            cts.stem(
                text=xs.string("text"),
                language=xs.string("language"),
                part_of_speech=xs.string("part_of_speech"),
            ),
            "cts:stem(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "text", "v1": "language", "v2": "part_of_speech"},
            id="stem",
        ),
        pytest.param(
            cts.sum_aggregate(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:sum-aggregate(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="sum_aggregate",
        ),
        pytest.param(
            cts.thresholds(
                computed_labels=xs.string("computed_labels"),
                known_labels=xs.string("known_labels"),
                recall_weight=xs.string("recall_weight"),
            ),
            "cts:thresholds(xs:string($v0), xs:string($v1), xs:double(xs:string($v2)))",
            {"v0": "computed_labels", "v1": "known_labels", "v2": "recall_weight"},
            id="thresholds",
        ),
        pytest.param(
            cts.tokenize(
                text=xs.string("text"),
                language=xs.string("language"),
                field=xs.string("field"),
            ),
            "cts:tokenize(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "text", "v1": "language", "v2": "field"},
            id="tokenize",
        ),
        pytest.param(
            cts.train(
                training_nodes=xs.string("training_nodes"),
                labels=xs.string("labels"),
                options=xs.string("options"),
            ),
            "cts:train(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "training_nodes", "v1": "labels", "v2": "options"},
            id="train",
        ),
        pytest.param(
            cts.triple_range_query(
                subject=xs.string("subject"),
                predicate=xs.string("predicate"),
                object=xs.string("object"),
                operator=xs.string("operator"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            (
                "cts:triple-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:string($v4), "
                "xs:double(xs:string($v5)))"
            ),
            {
                "v0": "subject",
                "v1": "predicate",
                "v2": "object",
                "v3": "operator",
                "v4": "options",
                "v5": "weight",
            },
            id="triple_range_query",
        ),
        pytest.param(
            cts.triple_value_statistics(
                values=xs.string("values"),
                forest_ids=xs.string("forest_ids"),
            ),
            "cts:triple-value-statistics(xs:string($v0), xs:string($v1))",
            {"v0": "values", "v1": "forest_ids"},
            id="triple_value_statistics",
        ),
        pytest.param(
            cts.triples(
                subject=xs.string("subject"),
                predicate=xs.string("predicate"),
                object=xs.string("object"),
                operator=xs.string("operator"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:triples(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:string($v4), xs:string($v5), xs:string($v6))"
            ),
            {
                "v0": "subject",
                "v1": "predicate",
                "v2": "object",
                "v3": "operator",
                "v4": "options",
                "v5": "query",
                "v6": "forest_ids",
            },
            id="triples",
        ),
        pytest.param(cts.true_query(), "cts:true-query()", {}, id="true_query"),
        pytest.param(cts.unordered(), "cts:unordered()", {}, id="unordered"),
        pytest.param(
            cts.uri_match(
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:uri-match(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "pattern",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="uri_match",
        ),
        pytest.param(
            cts.uri_reference(),
            "cts:uri-reference()",
            {},
            id="uri_reference",
        ),
        pytest.param(
            cts.uris(
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:uris(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "start",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="uris",
        ),
        pytest.param(
            cts.valid_document_patch_path(
                string=xs.string("string"),
                map=xs.string("map"),
            ),
            "cts:valid-document-patch-path(xs:string($v0), xs:string($v1))",
            {"v0": "string", "v1": "map"},
            id="valid_document_patch_path",
        ),
        pytest.param(
            cts.valid_extract_path(string=xs.string("string"), map=xs.string("map")),
            "cts:valid-extract-path(xs:string($v0), xs:string($v1))",
            {"v0": "string", "v1": "map"},
            id="valid_extract_path",
        ),
        pytest.param(
            cts.valid_index_path(
                string=xs.string("string"),
                ignorens=xs.string("ignorens"),
            ),
            "cts:valid-index-path(xs:string($v0), xs:string($v1))",
            {"v0": "string", "v1": "ignorens"},
            id="valid_index_path",
        ),
        pytest.param(
            cts.valid_optic_path(string=xs.string("string"), map=xs.string("map")),
            "cts:valid-optic-path(xs:string($v0), xs:string($v1))",
            {"v0": "string", "v1": "map"},
            id="valid_optic_path",
        ),
        pytest.param(
            cts.valid_tde_context(string=xs.string("string"), map=xs.string("map")),
            "cts:valid-tde-context(xs:string($v0), xs:string($v1))",
            {"v0": "string", "v1": "map"},
            id="valid_tde_context",
        ),
        pytest.param(
            cts.value_co_occurrences(
                range_index_1=xs.string("range_index_1"),
                range_index_2=xs.string("range_index_2"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:value-co-occurrences(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3), xs:double(xs:string($v4)), "
                "xs:string($v5))"
            ),
            {
                "v0": "range_index_1",
                "v1": "range_index_2",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="value_co_occurrences",
        ),
        pytest.param(
            cts.value_match(
                range_indexes=xs.string("range_indexes"),
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:value-match(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "range_indexes",
                "v1": "pattern",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="value_match",
        ),
        pytest.param(
            cts.value_ranges(
                range_indexes=xs.string("range_indexes"),
                bounds=xs.string("bounds"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:value-ranges(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "range_indexes",
                "v1": "bounds",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="value_ranges",
        ),
        pytest.param(
            cts.value_tuples(
                range_indexes=xs.string("range_indexes"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:value-tuples(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "range_indexes",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="value_tuples",
        ),
        pytest.param(
            cts.values(
                range_indexes=xs.string("range_indexes"),
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:values(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3), xs:double(xs:string($v4)), xs:string($v5))"
            ),
            {
                "v0": "range_indexes",
                "v1": "start",
                "v2": "options",
                "v3": "query",
                "v4": "quality_weight",
                "v5": "forest_ids",
            },
            id="values",
        ),
        pytest.param(
            cts.variance(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:variance(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="variance",
        ),
        pytest.param(
            cts.variance_p(
                range_index=xs.string("range_index"),
                options=xs.string("options"),
                query=xs.string("query"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:variance-p(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:string($v3))"
            ),
            {"v0": "range_index", "v1": "options", "v2": "query", "v3": "forest_ids"},
            id="variance_p",
        ),
        pytest.param(
            cts.walk(
                node=xs.string("node"),
                query=xs.string("query"),
                expr=xs.string("expr"),
            ),
            "cts:walk(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "node", "v1": "query", "v2": "expr"},
            id="walk",
        ),
        pytest.param(
            cts.word_match(
                pattern=xs.string("pattern"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:word-match(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "pattern",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="word_match",
        ),
        pytest.param(
            cts.word_query(
                text=xs.string("text"),
                options=xs.string("options"),
                weight=xs.string("weight"),
            ),
            "cts:word-query(xs:string($v0), xs:string($v1), xs:double(xs:string($v2)))",
            {"v0": "text", "v1": "options", "v2": "weight"},
            id="word_query",
        ),
        pytest.param(
            cts.words(
                start=xs.string("start"),
                options=xs.string("options"),
                query=xs.string("query"),
                quality_weight=xs.string("quality_weight"),
                forest_ids=xs.string("forest_ids"),
            ),
            (
                "cts:words(xs:string($v0), xs:string($v1), xs:string($v2), "
                "xs:double(xs:string($v3)), xs:string($v4))"
            ),
            {
                "v0": "start",
                "v1": "options",
                "v2": "query",
                "v3": "quality_weight",
                "v4": "forest_ids",
            },
            id="words",
        ),
    ],
)
def test_compile_native_call(expression, body, variables):
    declarations = "".join(
        f"declare variable ${key} as xs:string external;\n" for key in variables
    )
    assert expression.compile() == (
        'xquery version "1.0-ml";\n' + declarations + body,
        variables,
    )


@pytest.mark.parametrize(
    ("expression", "body", "variables"),
    [
        pytest.param(
            cts.aggregate(
                native_plugin=xs.string("native_plugin"),
                aggregate_name=xs.string("aggregate_name"),
                range_indexes=xs.string("range_indexes"),
            ),
            "cts:aggregate(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "native_plugin", "v1": "aggregate_name", "v2": "range_indexes"},
            id="aggregate",
        ),
        pytest.param(
            cts.and_query(queries=xs.string("queries")),
            "cts:and-query(xs:string($v0))",
            {"v0": "queries"},
            id="and_query",
        ),
        pytest.param(
            cts.avg_aggregate(range_index=xs.string("range_index")),
            "cts:avg-aggregate(xs:string($v0))",
            {"v0": "range_index"},
            id="avg_aggregate",
        ),
        pytest.param(
            cts.classify(
                data_nodes=xs.string("data_nodes"),
                classifier=xs.string("classifier"),
            ),
            "cts:classify(xs:string($v0), xs:string($v1))",
            {"v0": "data_nodes", "v1": "classifier"},
            id="classify",
        ),
        pytest.param(
            cts.cluster(nodes=xs.string("nodes")),
            "cts:cluster(xs:string($v0))",
            {"v0": "nodes"},
            id="cluster",
        ),
        pytest.param(
            cts.collection_match(pattern=xs.string("pattern")),
            "cts:collection-match(xs:string($v0))",
            {"v0": "pattern"},
            id="collection_match",
        ),
        pytest.param(
            cts.collection_reference(),
            "cts:collection-reference()",
            {},
            id="collection_reference",
        ),
        pytest.param(cts.collections(), "cts:collections()", {}, id="collections"),
        pytest.param(
            cts.column_range_query(
                schema=xs.string("schema"),
                view=xs.string("view"),
                column=xs.string("column"),
                value=xs.string("value"),
            ),
            (
                "cts:column-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3))"
            ),
            {"v0": "schema", "v1": "view", "v2": "column", "v3": "value"},
            id="column_range_query",
        ),
        pytest.param(cts.confidence(), "cts:confidence()", {}, id="confidence"),
        pytest.param(
            cts.confidence_order(),
            "cts:confidence-order()",
            {},
            id="confidence_order",
        ),
        pytest.param(
            cts.correlation(value1=xs.string("value1"), value2=xs.string("value2")),
            "cts:correlation(xs:string($v0), xs:string($v1))",
            {"v0": "value1", "v1": "value2"},
            id="correlation",
        ),
        pytest.param(
            cts.count_aggregate(range_index=xs.string("range_index")),
            "cts:count-aggregate(xs:string($v0))",
            {"v0": "range_index"},
            id="count_aggregate",
        ),
        pytest.param(
            cts.covariance(value1=xs.string("value1"), value2=xs.string("value2")),
            "cts:covariance(xs:string($v0), xs:string($v1))",
            {"v0": "value1", "v1": "value2"},
            id="covariance",
        ),
        pytest.param(
            cts.covariance_p(value1=xs.string("value1"), value2=xs.string("value2")),
            "cts:covariance-p(xs:string($v0), xs:string($v1))",
            {"v0": "value1", "v1": "value2"},
            id="covariance_p",
        ),
        pytest.param(
            cts.directory_query(uris=xs.string("uris")),
            "cts:directory-query(xs:string($v0), xs:string($v1))",
            {"v0": "uris", "v1": "1"},
            id="directory_query",
        ),
        pytest.param(
            cts.distinctive_terms(nodes=xs.string("nodes")),
            "cts:distinctive-terms(xs:string($v0))",
            {"v0": "nodes"},
            id="distinctive_terms",
        ),
        pytest.param(
            cts.document_order(),
            "cts:document-order()",
            {},
            id="document_order",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_boxes(
                parent_element_names=xs.string("parent_element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
            ),
            (
                "cts:element-attribute-pair-geospatial-boxes(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {
                "v0": "parent_element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
            },
            id="element_attribute_pair_geospatial_boxes",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_query(
                element_name=xs.string("element_name"),
                latitude_attribute_names=xs.string("latitude_attribute_names"),
                longitude_attribute_names=xs.string("longitude_attribute_names"),
                regions=xs.string("regions"),
            ),
            (
                "cts:element-attribute-pair-geospatial-query(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "element_name",
                "v1": "latitude_attribute_names",
                "v2": "longitude_attribute_names",
                "v3": "regions",
            },
            id="element_attribute_pair_geospatial_query",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_value_match(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                pattern=xs.string("pattern"),
            ),
            (
                "cts:element-attribute-pair-geospatial-value-match(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "pattern",
            },
            id="element_attribute_pair_geospatial_value_match",
        ),
        pytest.param(
            cts.element_attribute_pair_geospatial_values(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
            ),
            (
                "cts:element-attribute-pair-geospatial-values(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "element_names", "v1": "latitude_names", "v2": "longitude_names"},
            id="element_attribute_pair_geospatial_values",
        ),
        pytest.param(
            cts.element_attribute_range_query(
                element_name=xs.string("element_name"),
                attribute_name=xs.string("attribute_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
            ),
            (
                "cts:element-attribute-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "element_name",
                "v1": "attribute_name",
                "v2": "operator",
                "v3": "value",
            },
            id="element_attribute_range_query",
        ),
        pytest.param(
            cts.element_attribute_reference(
                element=xs.string("element"),
                attribute=xs.string("attribute"),
            ),
            "cts:element-attribute-reference(xs:string($v0), xs:string($v1))",
            {"v0": "element", "v1": "attribute"},
            id="element_attribute_reference",
        ),
        pytest.param(
            cts.element_attribute_value_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                attribute_name_1=xs.string("attribute_name_1"),
                element_name_2=xs.string("element_name_2"),
                attribute_name_2=xs.string("attribute_name_2"),
            ),
            (
                "cts:element-attribute-value-co-occurrences(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "element_name_1",
                "v1": "attribute_name_1",
                "v2": "element_name_2",
                "v3": "attribute_name_2",
            },
            id="element_attribute_value_co_occurrences",
        ),
        pytest.param(
            cts.element_attribute_value_geospatial_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                attribute_name_1=xs.string("attribute_name_1"),
                geo_element_name=xs.string("geo_element_name"),
            ),
            (
                "cts:element-attribute-value-geospatial-co-occurrences(xs:string($v0),"
                " xs:string($v1), xs:string($v2))"
            ),
            {
                "v0": "element_name_1",
                "v1": "attribute_name_1",
                "v2": "geo_element_name",
            },
            id="element_attribute_value_geospatial_co_occurrences",
        ),
        pytest.param(
            cts.element_attribute_value_match(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                pattern=xs.string("pattern"),
            ),
            (
                "cts:element-attribute-value-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "element_names", "v1": "attribute_names", "v2": "pattern"},
            id="element_attribute_value_match",
        ),
        pytest.param(
            cts.element_attribute_value_query(
                element_name=xs.string("element_name"),
                attribute_name=xs.string("attribute_name"),
                text=xs.string("text"),
            ),
            (
                "cts:element-attribute-value-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "element_name", "v1": "attribute_name", "v2": "text"},
            id="element_attribute_value_query",
        ),
        pytest.param(
            cts.element_attribute_value_ranges(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
            ),
            "cts:element-attribute-value-ranges(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "attribute_names"},
            id="element_attribute_value_ranges",
        ),
        pytest.param(
            cts.element_attribute_values(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
            ),
            "cts:element-attribute-values(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "attribute_names"},
            id="element_attribute_values",
        ),
        pytest.param(
            cts.element_attribute_word_match(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
                pattern=xs.string("pattern"),
            ),
            (
                "cts:element-attribute-word-match(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "element_names", "v1": "attribute_names", "v2": "pattern"},
            id="element_attribute_word_match",
        ),
        pytest.param(
            cts.element_attribute_word_query(
                element_name=xs.string("element_name"),
                attribute_name=xs.string("attribute_name"),
                text=xs.string("text"),
            ),
            (
                "cts:element-attribute-word-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "element_name", "v1": "attribute_name", "v2": "text"},
            id="element_attribute_word_query",
        ),
        pytest.param(
            cts.element_attribute_words(
                element_names=xs.string("element_names"),
                attribute_names=xs.string("attribute_names"),
            ),
            "cts:element-attribute-words(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "attribute_names"},
            id="element_attribute_words",
        ),
        pytest.param(
            cts.element_child_geospatial_boxes(
                parent_element_names=xs.string("parent_element_names"),
                child_element_names=xs.string("child_element_names"),
            ),
            "cts:element-child-geospatial-boxes(xs:string($v0), xs:string($v1))",
            {"v0": "parent_element_names", "v1": "child_element_names"},
            id="element_child_geospatial_boxes",
        ),
        pytest.param(
            cts.element_child_geospatial_query(
                parent_element_name=xs.string("parent_element_name"),
                child_element_names=xs.string("child_element_names"),
                regions=xs.string("regions"),
            ),
            (
                "cts:element-child-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "parent_element_name", "v1": "child_element_names", "v2": "regions"},
            id="element_child_geospatial_query",
        ),
        pytest.param(
            cts.element_child_geospatial_value_match(
                element_names=xs.string("element_names"),
                child_names=xs.string("child_names"),
                pattern=xs.string("pattern"),
            ),
            (
                "cts:element-child-geospatial-value-match(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "element_names", "v1": "child_names", "v2": "pattern"},
            id="element_child_geospatial_value_match",
        ),
        pytest.param(
            cts.element_child_geospatial_values(
                element_names=xs.string("element_names"),
                child_names=xs.string("child_names"),
            ),
            "cts:element-child-geospatial-values(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "child_names"},
            id="element_child_geospatial_values",
        ),
        pytest.param(
            cts.element_geospatial_boxes(element_names=xs.string("element_names")),
            "cts:element-geospatial-boxes(xs:string($v0))",
            {"v0": "element_names"},
            id="element_geospatial_boxes",
        ),
        pytest.param(
            cts.element_geospatial_query(
                element_name=xs.string("element_name"),
                regions=xs.string("regions"),
            ),
            "cts:element-geospatial-query(xs:string($v0), xs:string($v1))",
            {"v0": "element_name", "v1": "regions"},
            id="element_geospatial_query",
        ),
        pytest.param(
            cts.element_geospatial_value_match(
                element_names=xs.string("element_names"),
                pattern=xs.string("pattern"),
            ),
            "cts:element-geospatial-value-match(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "pattern"},
            id="element_geospatial_value_match",
        ),
        pytest.param(
            cts.element_geospatial_values(element_names=xs.string("element_names")),
            "cts:element-geospatial-values(xs:string($v0))",
            {"v0": "element_names"},
            id="element_geospatial_values",
        ),
        pytest.param(
            cts.element_pair_geospatial_boxes(
                parent_element_names=xs.string("parent_element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
            ),
            (
                "cts:element-pair-geospatial-boxes(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {
                "v0": "parent_element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
            },
            id="element_pair_geospatial_boxes",
        ),
        pytest.param(
            cts.element_pair_geospatial_query(
                element_name=xs.string("element_name"),
                latitude_element_names=xs.string("latitude_element_names"),
                longitude_element_names=xs.string("longitude_element_names"),
                regions=xs.string("regions"),
            ),
            (
                "cts:element-pair-geospatial-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "element_name",
                "v1": "latitude_element_names",
                "v2": "longitude_element_names",
                "v3": "regions",
            },
            id="element_pair_geospatial_query",
        ),
        pytest.param(
            cts.element_pair_geospatial_value_match(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
                pattern=xs.string("pattern"),
            ),
            (
                "cts:element-pair-geospatial-value-match(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "element_names",
                "v1": "latitude_names",
                "v2": "longitude_names",
                "v3": "pattern",
            },
            id="element_pair_geospatial_value_match",
        ),
        pytest.param(
            cts.element_pair_geospatial_values(
                element_names=xs.string("element_names"),
                latitude_names=xs.string("latitude_names"),
                longitude_names=xs.string("longitude_names"),
            ),
            (
                "cts:element-pair-geospatial-values(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "element_names", "v1": "latitude_names", "v2": "longitude_names"},
            id="element_pair_geospatial_values",
        ),
        pytest.param(
            cts.element_range_query(
                element_name=xs.string("element_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
            ),
            "cts:element-range-query(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "element_name", "v1": "operator", "v2": "value"},
            id="element_range_query",
        ),
        pytest.param(
            cts.element_reference(element=xs.string("element")),
            "cts:element-reference(xs:string($v0))",
            {"v0": "element"},
            id="element_reference",
        ),
        pytest.param(
            cts.element_value_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                element_name_2=xs.string("element_name_2"),
            ),
            "cts:element-value-co-occurrences(xs:string($v0), xs:string($v1))",
            {"v0": "element_name_1", "v1": "element_name_2"},
            id="element_value_co_occurrences",
        ),
        pytest.param(
            cts.element_value_geospatial_co_occurrences(
                element_name_1=xs.string("element_name_1"),
                geo_element_name=xs.string("geo_element_name"),
            ),
            (
                "cts:element-value-geospatial-co-occurrences(xs:string($v0), "
                "xs:string($v1))"
            ),
            {"v0": "element_name_1", "v1": "geo_element_name"},
            id="element_value_geospatial_co_occurrences",
        ),
        pytest.param(
            cts.element_value_match(
                element_names=xs.string("element_names"),
                pattern=xs.string("pattern"),
            ),
            "cts:element-value-match(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "pattern"},
            id="element_value_match",
        ),
        pytest.param(
            cts.element_value_query(element_name=xs.string("element_name")),
            "cts:element-value-query(xs:string($v0))",
            {"v0": "element_name"},
            id="element_value_query",
        ),
        pytest.param(
            cts.element_value_ranges(element_names=xs.string("element_names")),
            "cts:element-value-ranges(xs:string($v0))",
            {"v0": "element_names"},
            id="element_value_ranges",
        ),
        pytest.param(
            cts.element_values(element_names=xs.string("element_names")),
            "cts:element-values(xs:string($v0))",
            {"v0": "element_names"},
            id="element_values",
        ),
        pytest.param(
            cts.element_word_match(
                element_names=xs.string("element_names"),
                pattern=xs.string("pattern"),
            ),
            "cts:element-word-match(xs:string($v0), xs:string($v1))",
            {"v0": "element_names", "v1": "pattern"},
            id="element_word_match",
        ),
        pytest.param(
            cts.element_word_query(
                element_name=xs.string("element_name"),
                text=xs.string("text"),
            ),
            "cts:element-word-query(xs:string($v0), xs:string($v1))",
            {"v0": "element_name", "v1": "text"},
            id="element_word_query",
        ),
        pytest.param(
            cts.element_words(element_names=xs.string("element_names")),
            "cts:element-words(xs:string($v0))",
            {"v0": "element_names"},
            id="element_words",
        ),
        pytest.param(
            cts.entity_dictionary(entities=xs.string("entities")),
            "cts:entity-dictionary(xs:string($v0))",
            {"v0": "entities"},
            id="entity_dictionary",
        ),
        pytest.param(
            cts.entity_dictionary_parse(contents=xs.string("contents")),
            "cts:entity-dictionary-parse(xs:string($v0))",
            {"v0": "contents"},
            id="entity_dictionary_parse",
        ),
        pytest.param(
            cts.entity_highlight(node=xs.string("node"), expr=xs.string("expr")),
            "cts:entity-highlight(xs:string($v0), xs:string($v1))",
            {"v0": "node", "v1": "expr"},
            id="entity_highlight",
        ),
        pytest.param(
            cts.entity_walk(node=xs.string("node"), expr=xs.string("expr")),
            "cts:entity-walk(xs:string($v0), xs:string($v1))",
            {"v0": "node", "v1": "expr"},
            id="entity_walk",
        ),
        pytest.param(cts.estimate(), "cts:estimate(())", {}, id="estimate"),
        pytest.param(
            cts.field_range_query(
                field_name=xs.string("field_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
            ),
            "cts:field-range-query(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "field_name", "v1": "operator", "v2": "value"},
            id="field_range_query",
        ),
        pytest.param(
            cts.field_reference(field=xs.string("field")),
            "cts:field-reference(xs:string($v0))",
            {"v0": "field"},
            id="field_reference",
        ),
        pytest.param(
            cts.field_value_co_occurrences(
                field_name_1=xs.string("field_name_1"),
                field_name_2=xs.string("field_name_2"),
            ),
            "cts:field-value-co-occurrences(xs:string($v0), xs:string($v1))",
            {"v0": "field_name_1", "v1": "field_name_2"},
            id="field_value_co_occurrences",
        ),
        pytest.param(
            cts.field_value_match(
                field_names=xs.string("field_names"),
                pattern=xs.string("pattern"),
            ),
            "cts:field-value-match(xs:string($v0), xs:string($v1))",
            {"v0": "field_names", "v1": "pattern"},
            id="field_value_match",
        ),
        pytest.param(
            cts.field_value_query(
                field_name=xs.string("field_name"),
                text=xs.string("text"),
            ),
            "cts:field-value-query(xs:string($v0), xs:string($v1))",
            {"v0": "field_name", "v1": "text"},
            id="field_value_query",
        ),
        pytest.param(
            cts.field_value_ranges(field_names=xs.string("field_names")),
            "cts:field-value-ranges(xs:string($v0))",
            {"v0": "field_names"},
            id="field_value_ranges",
        ),
        pytest.param(
            cts.field_values(field_names=xs.string("field_names")),
            "cts:field-values(xs:string($v0))",
            {"v0": "field_names"},
            id="field_values",
        ),
        pytest.param(
            cts.field_word_match(
                field_names=xs.string("field_names"),
                pattern=xs.string("pattern"),
            ),
            "cts:field-word-match(xs:string($v0), xs:string($v1))",
            {"v0": "field_names", "v1": "pattern"},
            id="field_word_match",
        ),
        pytest.param(
            cts.field_word_query(
                field_name=xs.string("field_name"),
                text=xs.string("text"),
            ),
            "cts:field-word-query(xs:string($v0), xs:string($v1))",
            {"v0": "field_name", "v1": "text"},
            id="field_word_query",
        ),
        pytest.param(
            cts.field_words(field_names=xs.string("field_names")),
            "cts:field-words(xs:string($v0))",
            {"v0": "field_names"},
            id="field_words",
        ),
        pytest.param(cts.fitness(), "cts:fitness()", {}, id="fitness"),
        pytest.param(
            cts.fitness_order(),
            "cts:fitness-order()",
            {},
            id="fitness_order",
        ),
        pytest.param(
            cts.geospatial_attribute_pair_reference(
                element=xs.string("element"),
                lat=xs.string("lat"),
                long=xs.string("long"),
            ),
            (
                "cts:geospatial-attribute-pair-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "element", "v1": "lat", "v2": "long"},
            id="geospatial_attribute_pair_reference",
        ),
        pytest.param(
            cts.geospatial_boxes(geo_indexes=xs.string("geo_indexes")),
            "cts:geospatial-boxes(xs:string($v0))",
            {"v0": "geo_indexes"},
            id="geospatial_boxes",
        ),
        pytest.param(
            cts.geospatial_co_occurrences(
                geo_element_name_1=xs.string("geo_element_name_1"),
                geo_element_name_2=xs.string("geo_element_name_2"),
            ),
            (
                "cts:geospatial-co-occurrences(xs:string($v0), xs:QName(()), "
                "xs:QName(()), xs:string($v1))"
            ),
            {"v0": "geo_element_name_1", "v1": "geo_element_name_2"},
            id="geospatial_co_occurrences",
        ),
        pytest.param(
            cts.geospatial_element_child_reference(
                element=xs.string("element"),
                child=xs.string("child"),
            ),
            "cts:geospatial-element-child-reference(xs:string($v0), xs:string($v1))",
            {"v0": "element", "v1": "child"},
            id="geospatial_element_child_reference",
        ),
        pytest.param(
            cts.geospatial_element_pair_reference(
                element=xs.string("element"),
                lat=xs.string("lat"),
                long=xs.string("long"),
            ),
            (
                "cts:geospatial-element-pair-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "element", "v1": "lat", "v2": "long"},
            id="geospatial_element_pair_reference",
        ),
        pytest.param(
            cts.geospatial_element_reference(element=xs.string("element")),
            "cts:geospatial-element-reference(xs:string($v0))",
            {"v0": "element"},
            id="geospatial_element_reference",
        ),
        pytest.param(
            cts.geospatial_json_property_child_reference(
                property=xs.string("property"),
                child=xs.string("child"),
            ),
            (
                "cts:geospatial-json-property-child-reference(xs:string($v0), "
                "xs:string($v1))"
            ),
            {"v0": "property", "v1": "child"},
            id="geospatial_json_property_child_reference",
        ),
        pytest.param(
            cts.geospatial_json_property_pair_reference(
                property=xs.string("property"),
                lat=xs.string("lat"),
                long=xs.string("long"),
            ),
            (
                "cts:geospatial-json-property-pair-reference(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {"v0": "property", "v1": "lat", "v2": "long"},
            id="geospatial_json_property_pair_reference",
        ),
        pytest.param(
            cts.geospatial_json_property_reference(property=xs.string("property")),
            "cts:geospatial-json-property-reference(xs:string($v0))",
            {"v0": "property"},
            id="geospatial_json_property_reference",
        ),
        pytest.param(
            cts.geospatial_path_reference(path_expression=xs.string("path_expression")),
            "cts:geospatial-path-reference(xs:string($v0))",
            {"v0": "path_expression"},
            id="geospatial_path_reference",
        ),
        pytest.param(
            cts.geospatial_region_path_reference(
                path_expression=xs.string("path_expression"),
            ),
            "cts:geospatial-region-path-reference(xs:string($v0))",
            {"v0": "path_expression"},
            id="geospatial_region_path_reference",
        ),
        pytest.param(
            cts.geospatial_region_query(
                geospatial_region_reference=xs.string("geospatial_region_reference"),
                operation=xs.string("operation"),
                regions=xs.string("regions"),
            ),
            (
                "cts:geospatial-region-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "geospatial_region_reference", "v1": "operation", "v2": "regions"},
            id="geospatial_region_query",
        ),
        pytest.param(
            cts.index_order(index=xs.string("index")),
            "cts:index-order(xs:string($v0))",
            {"v0": "index"},
            id="index_order",
        ),
        pytest.param(
            cts.json_property_child_geospatial_query(
                parent_property_name=xs.string("parent_property_name"),
                child_property_names=xs.string("child_property_names"),
                regions=xs.string("regions"),
            ),
            (
                "cts:json-property-child-geospatial-query(xs:string($v0), "
                "xs:string($v1), xs:string($v2))"
            ),
            {
                "v0": "parent_property_name",
                "v1": "child_property_names",
                "v2": "regions",
            },
            id="json_property_child_geospatial_query",
        ),
        pytest.param(
            cts.json_property_geospatial_query(
                property_name=xs.string("property_name"),
                regions=xs.string("regions"),
            ),
            "cts:json-property-geospatial-query(xs:string($v0), xs:string($v1))",
            {"v0": "property_name", "v1": "regions"},
            id="json_property_geospatial_query",
        ),
        pytest.param(
            cts.json_property_pair_geospatial_query(
                property_name=xs.string("property_name"),
                latitude_property_names=xs.string("latitude_property_names"),
                longitude_property_names=xs.string("longitude_property_names"),
                regions=xs.string("regions"),
            ),
            (
                "cts:json-property-pair-geospatial-query(xs:string($v0), "
                "xs:string($v1), xs:string($v2), xs:string($v3))"
            ),
            {
                "v0": "property_name",
                "v1": "latitude_property_names",
                "v2": "longitude_property_names",
                "v3": "regions",
            },
            id="json_property_pair_geospatial_query",
        ),
        pytest.param(
            cts.json_property_range_query(
                property_name=xs.string("property_name"),
                operator=xs.string("operator"),
                value=xs.string("value"),
            ),
            (
                "cts:json-property-range-query(xs:string($v0), xs:string($v1), "
                "xs:string($v2))"
            ),
            {"v0": "property_name", "v1": "operator", "v2": "value"},
            id="json_property_range_query",
        ),
        pytest.param(
            cts.json_property_reference(property=xs.string("property")),
            "cts:json-property-reference(xs:string($v0))",
            {"v0": "property"},
            id="json_property_reference",
        ),
        pytest.param(
            cts.json_property_value_query(
                property_name=xs.string("property_name"),
                value=xs.string("value"),
            ),
            "cts:json-property-value-query(xs:string($v0), xs:string($v1))",
            {"v0": "property_name", "v1": "value"},
            id="json_property_value_query",
        ),
        pytest.param(
            cts.json_property_word_match(
                property_names=xs.string("property_names"),
                pattern=xs.string("pattern"),
            ),
            "cts:json-property-word-match(xs:string($v0), xs:string($v1))",
            {"v0": "property_names", "v1": "pattern"},
            id="json_property_word_match",
        ),
        pytest.param(
            cts.json_property_word_query(
                property_name=xs.string("property_name"),
                text=xs.string("text"),
            ),
            "cts:json-property-word-query(xs:string($v0), xs:string($v1))",
            {"v0": "property_name", "v1": "text"},
            id="json_property_word_query",
        ),
        pytest.param(
            cts.json_property_words(property_names=xs.string("property_names")),
            "cts:json-property-words(xs:string($v0))",
            {"v0": "property_names"},
            id="json_property_words",
        ),
        pytest.param(
            cts.linear_model(values=xs.string("values")),
            "cts:linear-model(xs:string($v0))",
            {"v0": "values"},
            id="linear_model",
        ),
        pytest.param(
            cts.lsqt_query(temporal_collection=xs.string("temporal_collection")),
            "cts:lsqt-query(xs:string($v0))",
            {"v0": "temporal_collection"},
            id="lsqt_query",
        ),
        pytest.param(
            cts.match_regions(
                range_indexes=xs.string("range_indexes"),
                operation=xs.string("operation"),
                regions=xs.string("regions"),
            ),
            "cts:match-regions(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "range_indexes", "v1": "operation", "v2": "regions"},
            id="match_regions",
        ),
        pytest.param(
            cts.max(range_index=xs.string("range_index")),
            "cts:max(xs:string($v0))",
            {"v0": "range_index"},
            id="max",
        ),
        pytest.param(
            cts.min(range_index=xs.string("range_index")),
            "cts:min(xs:string($v0))",
            {"v0": "range_index"},
            id="min",
        ),
        pytest.param(
            cts.near_query(queries=xs.string("queries")),
            "cts:near-query(xs:string($v0))",
            {"v0": "queries"},
            id="near_query",
        ),
        pytest.param(
            cts.or_query(queries=xs.string("queries")),
            "cts:or-query(xs:string($v0))",
            {"v0": "queries"},
            id="or_query",
        ),
        pytest.param(
            cts.parse(query=xs.string("query")),
            "cts:parse(xs:string($v0))",
            {"v0": "query"},
            id="parse",
        ),
        pytest.param(
            cts.path_geospatial_query(
                path_expression=xs.string("path_expression"),
                regions=xs.string("regions"),
            ),
            "cts:path-geospatial-query(xs:string($v0), xs:string($v1))",
            {"v0": "path_expression", "v1": "regions"},
            id="path_geospatial_query",
        ),
        pytest.param(
            cts.path_range_query(
                path_expression=xs.string("path_expression"),
                operator=xs.string("operator"),
                value=xs.string("value"),
            ),
            "cts:path-range-query(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "path_expression", "v1": "operator", "v2": "value"},
            id="path_range_query",
        ),
        pytest.param(
            cts.path_reference(path_expression=xs.string("path_expression")),
            "cts:path-reference(xs:string($v0))",
            {"v0": "path_expression"},
            id="path_reference",
        ),
        pytest.param(
            cts.percent_rank(arg=xs.string("arg"), value=xs.string("value")),
            "cts:percent-rank(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "value"},
            id="percent_rank",
        ),
        pytest.param(
            cts.period_compare_query(
                axis_1=xs.string("axis_1"),
                operator=xs.string("operator"),
                axis_2=xs.string("axis_2"),
            ),
            "cts:period-compare-query(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "axis_1", "v1": "operator", "v2": "axis_2"},
            id="period_compare_query",
        ),
        pytest.param(
            cts.period_range_query(
                axis_name=xs.string("axis_name"),
                operator=xs.string("operator"),
            ),
            "cts:period-range-query(xs:string($v0), xs:string($v1))",
            {"v0": "axis_name", "v1": "operator"},
            id="period_range_query",
        ),
        pytest.param(
            cts.point(latitude_or_wkt=xs.string("latitude_or_wkt")),
            "cts:point(xs:string($v0))",
            {"v0": "latitude_or_wkt"},
            id="point",
        ),
        pytest.param(cts.quality(), "cts:quality()", {}, id="quality"),
        pytest.param(
            cts.quality_order(),
            "cts:quality-order()",
            {},
            id="quality_order",
        ),
        pytest.param(
            cts.range_query(
                index=xs.string("index"),
                operator=xs.string("operator"),
                value=xs.string("value"),
            ),
            "cts:range-query(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "index", "v1": "operator", "v2": "value"},
            id="range_query",
        ),
        pytest.param(
            cts.rank(arg=xs.string("arg"), value=xs.string("value")),
            "cts:rank(xs:string($v0), xs:string($v1))",
            {"v0": "arg", "v1": "value"},
            id="rank",
        ),
        pytest.param(
            cts.registered_query(ids=xs.string("ids")),
            "cts:registered-query(xs:string($v0))",
            {"v0": "ids"},
            id="registered_query",
        ),
        pytest.param(
            cts.relevance_info(),
            "cts:relevance-info()",
            {},
            id="relevance_info",
        ),
        pytest.param(cts.remainder(), "cts:remainder()", {}, id="remainder"),
        pytest.param(
            cts.reverse_query(nodes=xs.string("nodes")),
            "cts:reverse-query(xs:string($v0))",
            {"v0": "nodes"},
            id="reverse_query",
        ),
        pytest.param(cts.score(), "cts:score()", {}, id="score"),
        pytest.param(cts.score_order(), "cts:score-order()", {}, id="score_order"),
        pytest.param(cts.search(), "cts:search(/, ())", {}, id="search"),
        pytest.param(
            cts.similar_query(nodes=xs.string("nodes")),
            "cts:similar-query(xs:string($v0))",
            {"v0": "nodes"},
            id="similar_query",
        ),
        pytest.param(
            cts.stddev(range_index=xs.string("range_index")),
            "cts:stddev(xs:string($v0))",
            {"v0": "range_index"},
            id="stddev",
        ),
        pytest.param(
            cts.stddev_p(range_index=xs.string("range_index")),
            "cts:stddev-p(xs:string($v0))",
            {"v0": "range_index"},
            id="stddev_p",
        ),
        pytest.param(
            cts.stem(text=xs.string("text")),
            "cts:stem(xs:string($v0))",
            {"v0": "text"},
            id="stem",
        ),
        pytest.param(
            cts.sum_aggregate(range_index=xs.string("range_index")),
            "cts:sum-aggregate(xs:string($v0))",
            {"v0": "range_index"},
            id="sum_aggregate",
        ),
        pytest.param(
            cts.thresholds(
                computed_labels=xs.string("computed_labels"),
                known_labels=xs.string("known_labels"),
            ),
            "cts:thresholds(xs:string($v0), xs:string($v1))",
            {"v0": "computed_labels", "v1": "known_labels"},
            id="thresholds",
        ),
        pytest.param(
            cts.tokenize(text=xs.string("text")),
            "cts:tokenize(xs:string($v0))",
            {"v0": "text"},
            id="tokenize",
        ),
        pytest.param(
            cts.train(
                training_nodes=xs.string("training_nodes"),
                labels=xs.string("labels"),
            ),
            "cts:train(xs:string($v0), xs:string($v1))",
            {"v0": "training_nodes", "v1": "labels"},
            id="train",
        ),
        pytest.param(
            cts.triple_range_query(
                subject=xs.string("subject"),
                predicate=xs.string("predicate"),
                object=xs.string("object"),
            ),
            "cts:triple-range-query(xs:string($v0), xs:string($v1), xs:string($v2))",
            {"v0": "subject", "v1": "predicate", "v2": "object"},
            id="triple_range_query",
        ),
        pytest.param(
            cts.triple_value_statistics(),
            "cts:triple-value-statistics()",
            {},
            id="triple_value_statistics",
        ),
        pytest.param(cts.triples(), "cts:triples()", {}, id="triples"),
        pytest.param(
            cts.uri_match(pattern=xs.string("pattern")),
            "cts:uri-match(xs:string($v0))",
            {"v0": "pattern"},
            id="uri_match",
        ),
        pytest.param(cts.uris(), "cts:uris()", {}, id="uris"),
        pytest.param(
            cts.valid_document_patch_path(string=xs.string("string")),
            "cts:valid-document-patch-path(xs:string($v0))",
            {"v0": "string"},
            id="valid_document_patch_path",
        ),
        pytest.param(
            cts.valid_extract_path(string=xs.string("string")),
            "cts:valid-extract-path(xs:string($v0))",
            {"v0": "string"},
            id="valid_extract_path",
        ),
        pytest.param(
            cts.valid_optic_path(string=xs.string("string")),
            "cts:valid-optic-path(xs:string($v0))",
            {"v0": "string"},
            id="valid_optic_path",
        ),
        pytest.param(
            cts.valid_tde_context(string=xs.string("string")),
            "cts:valid-tde-context(xs:string($v0))",
            {"v0": "string"},
            id="valid_tde_context",
        ),
        pytest.param(
            cts.value_co_occurrences(
                range_index_1=xs.string("range_index_1"),
                range_index_2=xs.string("range_index_2"),
            ),
            "cts:value-co-occurrences(xs:string($v0), xs:string($v1))",
            {"v0": "range_index_1", "v1": "range_index_2"},
            id="value_co_occurrences",
        ),
        pytest.param(
            cts.value_match(
                range_indexes=xs.string("range_indexes"),
                pattern=xs.string("pattern"),
            ),
            "cts:value-match(xs:string($v0), xs:string($v1))",
            {"v0": "range_indexes", "v1": "pattern"},
            id="value_match",
        ),
        pytest.param(
            cts.value_ranges(range_indexes=xs.string("range_indexes")),
            "cts:value-ranges(xs:string($v0))",
            {"v0": "range_indexes"},
            id="value_ranges",
        ),
        pytest.param(
            cts.value_tuples(range_indexes=xs.string("range_indexes")),
            "cts:value-tuples(xs:string($v0))",
            {"v0": "range_indexes"},
            id="value_tuples",
        ),
        pytest.param(
            cts.values(range_indexes=xs.string("range_indexes")),
            "cts:values(xs:string($v0))",
            {"v0": "range_indexes"},
            id="values",
        ),
        pytest.param(
            cts.variance(range_index=xs.string("range_index")),
            "cts:variance(xs:string($v0))",
            {"v0": "range_index"},
            id="variance",
        ),
        pytest.param(
            cts.variance_p(range_index=xs.string("range_index")),
            "cts:variance-p(xs:string($v0))",
            {"v0": "range_index"},
            id="variance_p",
        ),
        pytest.param(
            cts.word_match(pattern=xs.string("pattern")),
            "cts:word-match(xs:string($v0))",
            {"v0": "pattern"},
            id="word_match",
        ),
        pytest.param(
            cts.word_query(text=xs.string("text")),
            "cts:word-query(xs:string($v0))",
            {"v0": "text"},
            id="word_query",
        ),
        pytest.param(cts.words(), "cts:words()", {}, id="words"),
    ],
)
def test_compile_default_arguments(expression, body, variables):
    declarations = "".join(
        f"declare variable ${key} as xs:string external;\n" for key in variables
    )
    assert expression.compile() == (
        'xquery version "1.0-ml";\n' + declarations + body,
        variables,
    )
