"""CTS query classes normalize their arguments exactly like the cts builder."""

import pytest

from mlclient.xquery import (
    ColumnRangeQuery,
    DirectoryQuery,
    DocumentRootQuery,
    ElementAttributeRangeQuery,
    ElementPairGeospatialQuery,
    ElementQuery,
    ElementRangeQuery,
    ElementWordQuery,
    FieldRangeQuery,
    JsonPropertyRangeQuery,
    NearQuery,
    RangeQuery,
    cts,
    fn,
)

NS = "http://example.com/ns"


@pytest.mark.parametrize(
    ("constructed", "built"),
    [
        (
            ElementRangeQuery("price", ">=", 10),
            cts.element_range_query("price", ">=", 10),
        ),
        (
            ElementRangeQuery(fn.qname(NS, "price"), "<", 1.5, weight=2),
            cts.element_range_query(fn.qname(NS, "price"), "<", 1.5, weight=2),
        ),
        (
            ElementAttributeRangeQuery("item", "price", "=", 3),
            cts.element_attribute_range_query("item", "price", "=", 3),
        ),
        (
            ElementWordQuery(["title", "subtitle"], "coffee"),
            cts.element_word_query(["title", "subtitle"], "coffee"),
        ),
        (
            ElementQuery("item", cts.word_query("tea")),
            cts.element_query("item", cts.word_query("tea")),
        ),
        (
            ElementPairGeospatialQuery("place", "lat", "lon", cts.point(1, 2)),
            cts.element_pair_geospatial_query("place", "lat", "lon", cts.point(1, 2)),
        ),
        (DocumentRootQuery("item"), cts.document_root_query("item")),
        (DirectoryQuery("/a/", "infinity"), cts.directory_query("/a/", "infinity")),
        (
            FieldRangeQuery("price-field", "!=", 1),
            cts.field_range_query("price-field", "!=", 1),
        ),
        (
            JsonPropertyRangeQuery("price", "<=", 2),
            cts.json_property_range_query("price", "<=", 2),
        ),
        (
            NearQuery([cts.word_query("a"), cts.word_query("b")], distance=3),
            cts.near_query([cts.word_query("a"), cts.word_query("b")], distance=3),
        ),
        (
            ColumnRangeQuery("main", "items", "price", 5, operator=">"),
            cts.column_range_query("main", "items", "price", 5, operator=">"),
        ),
        (
            RangeQuery(cts.element_reference("price"), ">", 1, weight=0.5),
            cts.range_query(cts.element_reference("price"), ">", 1, weight=0.5),
        ),
    ],
)
def test_direct_construction_matches_the_builder(constructed, built):
    assert constructed == built


def test_directly_constructed_query_serializes_like_the_builder():
    assert ElementRangeQuery("price", ">=", 10).to_json() == (
        cts.element_range_query("price", ">=", 10).to_json()
    )


def test_directly_constructed_query_rejects_an_unsupported_operator():
    with pytest.raises(ValueError, match="unsupported range operator: 'gt'"):
        ElementRangeQuery("price", "gt", 10)


def test_directly_constructed_query_rejects_an_unsupported_depth():
    with pytest.raises(ValueError, match="directory depth must be '1' or 'infinity'"):
        DirectoryQuery("/a/", "2")
