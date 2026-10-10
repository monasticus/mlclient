"""Native serialization resources and public query behavior."""

import pytest
from xml.etree.ElementTree import fromstring, tostring
from tests.utils.resources import discover_serialization_cases
from mlclient.xquery import AfterQuery, cts
from mlclient.xquery import AndNotQuery
from mlclient.xquery import AndQuery
from mlclient.xquery import BeforeQuery
from mlclient.xquery import BoostQuery
from mlclient.xquery import CollectionQuery
from mlclient.xquery import ColumnRangeQuery
from mlclient.xquery import (
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
    fn,
)
from mlclient.xquery import DocumentFormatQuery
from mlclient.xquery import DocumentFragmentQuery
from mlclient.xquery import DocumentPermissionQuery
from mlclient.xquery import DocumentQuery
from mlclient.xquery import ElementAttributePairGeospatialQuery
from mlclient.xquery import ElementAttributeValueQuery
from mlclient.xquery import ElementAttributeWordQuery
from mlclient.xquery import ElementChildGeospatialQuery
from mlclient.xquery import ElementGeospatialQuery
import datetime
from decimal import Decimal
from mlclient.xquery import xs
from mlclient.xquery import ElementValueQuery
from mlclient.xquery import FalseQuery
from mlclient.xquery import FieldValueQuery
from mlclient.xquery import FieldWordQuery
from mlclient.xquery import GeospatialRegionQuery
from mlclient.xquery import JsonPropertyChildGeospatialQuery
from mlclient.xquery import JsonPropertyGeospatialQuery
from mlclient.xquery import JsonPropertyPairGeospatialQuery
from mlclient.xquery import JsonPropertyScopeQuery
from mlclient.xquery import JsonPropertyValueQuery
from mlclient.xquery import JsonPropertyWordQuery
from mlclient.xquery import LocksFragmentQuery
from mlclient.xquery import LsqtQuery
from mlclient.xquery import NotInQuery
from mlclient.xquery import NotQuery
from mlclient.xquery import OrQuery
from mlclient.xquery import PathGeospatialQuery
from mlclient.xquery import PathRangeQuery
from mlclient.xquery import PeriodCompareQuery
from mlclient.xquery import PeriodRangeQuery
from mlclient.xquery import PropertiesFragmentQuery
import json
from mlclient.xquery import FunctionCall
from mlclient.xquery import RegisteredQuery
from mlclient.xquery import ReverseQuery
from mlclient.xquery import RuntimeQuery
from mlclient.xquery import SimilarQuery
from mlclient.xquery import TripleRangeQuery
from mlclient.xquery import TrueQuery
from mlclient.xquery import CtsQuery, WordQuery
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Comment, ProcessingInstruction, SubElement
from mlclient.xquery import xdmp


@pytest.mark.parametrize(
    "case", discover_serialization_cases(__file__), ids=lambda case: case.name,
)
def test_serialization(case):
    case.assert_matches()


def test_after_query():
    query = cts.after_query(16000000000)
    assert isinstance(query, AfterQuery)


def test_and_not_query():
    query = cts.and_not_query(
        cts.collection_query("reports"), cts.collection_query("notes"),
    )
    assert isinstance(query, AndNotQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:and-not-query(cts:collection-query($v0), cts:col'
            'lection-query($v1))'
        ),
        {"v0": "reports", "v1": "notes"},
    )


def test_and_query():
    query = cts.and_query(
        [cts.word_query("blue", options="lang=en"), cts.collection_query("reports")],
        options="ordered",
    )
    assert isinstance(query, AndQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:string external;\ncts:and-query((cts:'
            'word-query($v0, $v1), cts:collection-query($v2)), $v3)'
        ),
        {"v0": "blue", "v1": "lang=en", "v2": "reports", "v3": "ordered"},
    )


def test_before_query():
    query = cts.before_query(16000000000)
    assert isinstance(query, BeforeQuery)


def test_boost_query():
    query = cts.boost_query(
        cts.collection_query("reports"), cts.collection_query("notes"),
    )
    assert isinstance(query, BoostQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:boost-query(cts:collection-query($v0), cts:colle'
            'ction-query($v1))'
        ),
        {"v0": "reports", "v1": "notes"},
    )


def test_collection_query():
    query = cts.collection_query(["reports", "notes"])
    assert isinstance(query, CollectionQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:collection-query(($v0, $v1))'
        ),
        {"v0": "reports", "v1": "notes"},
    )


def test_cts_column_range_query_compilation():
    query = cts.column_range_query(
        "reports", "items", "price", 2, operator=">=", options="cached", weight=2,
    )
    assert isinstance(query, ColumnRangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:integer external;\ndeclare variable $'
            'v4 as xs:string external;\ndeclare variable $v5 as xs:st'
            'ring external;\ndeclare variable $v6 as xs:integer exter'
            'nal;\ncts:column-range-query($v0, $v1, $v2, $v3, xs:stri'
            'ng($v4), $v5, xs:double($v6))'
        ),
        {
            "v0": "reports",
            "v1": "items",
            "v2": "price",
            "v3": "2",
            "v4": ">=",
            "v5": "cached",
            "v6": "2",
        },
    )


def test_cts_column_range_query_serialization_requires_tde_column_metadata():
    query = cts.column_range_query("reports", "items", "price", 2)
    message = (
        "cts:column-range-query: CTS column serialization requir"
        "es the destination database's TDE column ID; use with_c"
        "olumn_id()."
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == message
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert str(error.value) == message


def test_cts_column_range_query_serialization_with_explicit_column_id():
    original = cts.column_range_query(
        "reports", "items", "price", 2, operator=">=", options="cached", weight=2,
    )
    query = original.with_column_id(11548423394257569743)
    assert query.compile() == original.compile()
    assert original.column_id is None
    expected = {
        "tripleRangeQuery": {
            "objectOperator": ">=",
            "predicate": [
                {"column": "reports.items.price", "columnID": "11548423394257569743"},
            ],
            "object": [
                {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "value": 2},
            ],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}


test_cts_direct_construction_direct_construction_matches_the_builder_ns = (
    "http://example.com/ns"
)


@pytest.mark.parametrize(
    ("constructed", "built"),
    [
        (
            ElementRangeQuery("price", ">=", 10),
            cts.element_range_query("price", ">=", 10),
        ),
        (
            ElementRangeQuery(
                fn.qname(
                    test_cts_direct_construction_direct_construction_matches_the_builder_ns,
                    "price",
                ),
                "<",
                1.5,
                weight=2,
            ),
            cts.element_range_query(
                fn.qname(
                    test_cts_direct_construction_direct_construction_matches_the_builder_ns,
                    "price",
                ),
                "<",
                1.5,
                weight=2,
            ),
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
def test_cts_direct_construction_direct_construction_matches_the_builder(
    constructed, built,
):
    assert constructed == built


def test_direct_query_rejects_an_unsupported_depth():
    with pytest.raises(ValueError, match="directory depth must be '1' or 'infinity'"):
        DirectoryQuery("/a/", "2")


def test_direct_query_rejects_an_unsupported_operator():
    with pytest.raises(ValueError, match="unsupported range operator: 'gt'"):
        ElementRangeQuery("price", "gt", 10)


def test_directory_query():
    query = cts.directory_query(["/reports/", "/notes/"], depth="infinity")
    assert isinstance(query, DirectoryQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ncts:dire'
            'ctory-query(($v0, $v1), xs:string($v2))'
        ),
        {"v0": "/reports/", "v1": "/notes/", "v2": "infinity"},
    )


def test_document_format_query():
    query = cts.document_format_query("json")
    assert isinstance(query, DocumentFormatQuery)


def test_document_fragment_query():
    query = cts.document_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, DocumentFragmentQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:document-fragment-query(cts:collectio'
            'n-query($v0))'
        ),
        {"v0": "reports"},
    )


def test_document_permission_query():
    query = cts.document_permission_query("admin", "read")
    assert isinstance(query, DocumentPermissionQuery)


def test_document_query():
    query = cts.document_query(["/reports/a.xml", "/notes/b.json"])
    assert isinstance(query, DocumentQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:document-query(($v0, $v1))'
        ),
        {"v0": "/reports/a.xml", "v1": "/notes/b.json"},
    )


def test_document_root_query():
    query = cts.document_root_query("root")
    assert isinstance(query, DocumentRootQuery)


test_document_root_query_namespaced_ns = "https://example.com/cts-test"


def test_document_root_query_namespaced():
    query = cts.document_root_query(
        fn.qname(test_document_root_query_namespaced_ns, "t:root"),
    )
    assert isinstance(query, DocumentRootQuery)


def test_element_attribute_pair_geospatial_query():
    query = cts.element_attribute_pair_geospatial_query(
        "item", "lat", "lon", cts.point(10, 20), weight=3,
    )
    assert isinstance(query, ElementAttributePairGeospatialQuery)


def test_element_attribute_range_query():
    query = cts.element_attribute_range_query("item", "amount", "!=", 3)
    assert isinstance(query, ElementAttributeRangeQuery)


def test_element_attribute_value_query():
    query = cts.element_attribute_value_query(
        "item", "status", "ok", options="exact", weight=0.5,
    )
    assert isinstance(query, ElementAttributeValueQuery)


def test_element_attribute_word_query():
    query = cts.element_attribute_word_query("item", "status", "ok")
    assert isinstance(query, ElementAttributeWordQuery)


def test_element_child_geospatial_query():
    query = cts.element_child_geospatial_query("location", "point", cts.point(10, 20))
    assert isinstance(query, ElementChildGeospatialQuery)


def test_element_geospatial_query_point():
    query = cts.element_geospatial_query(
        "origin", cts.point(10.5, -20.25), options="coordinate-system=wgs84", weight=2,
    )
    assert isinstance(query, ElementGeospatialQuery)


def test_element_geospatial_query_regions():
    query = cts.element_geospatial_query(
        "origin",
        [
            cts.box(1.5, 2, 3, 4),
            cts.circle(5, cts.point(10, 20)),
            cts.polygon(
                [cts.point(0, 0), cts.point(0, 1), cts.point(1, 1), cts.point(0, 0)],
            ),
        ],
    )
    assert isinstance(query, ElementGeospatialQuery)


def test_element_pair_geospatial_query():
    query = cts.element_pair_geospatial_query(
        "location", "lat", "lon", cts.point(10, 20),
    )
    assert isinstance(query, ElementPairGeospatialQuery)


test_element_query_ns = "https://example.com/cts-test"


def test_element_query():
    query = cts.element_query(
        ["a", fn.qname(test_element_query_ns, "t:b")], cts.word_query("x"),
    )
    assert isinstance(query, ElementQuery)


def test_element_range_query_boolean():
    query = cts.element_range_query("flag", "=", True)
    assert isinstance(query, ElementRangeQuery)


def test_element_range_query_date():
    query = cts.element_range_query("day", ">", datetime.date(2026, 1, 1))
    assert isinstance(query, ElementRangeQuery)


test_element_range_query_date_time_start = datetime.datetime(
    2026, 1, 1, tzinfo=datetime.timezone.utc,
)


def test_element_range_query_date_time():
    query = cts.element_range_query(
        "at", "<=", test_element_range_query_date_time_start,
    )
    assert isinstance(query, ElementRangeQuery)


def test_element_range_query_decimal():
    query = cts.element_range_query("price", "<", Decimal("1.5"))
    assert isinstance(query, ElementRangeQuery)


def test_element_range_query_double():
    query = cts.element_range_query("price", ">", xs.double(1.5))
    assert isinstance(query, ElementRangeQuery)


def test_element_range_query_integer():
    query = cts.element_range_query("price", ">=", 10, options="min-occurs=1", weight=2)
    assert isinstance(query, ElementRangeQuery)


def test_element_range_query_strings():
    query = cts.element_range_query("code", "=", ["a", "b"])
    assert isinstance(query, ElementRangeQuery)


def test_element_value_query():
    query = cts.element_value_query("title", "blue")
    assert isinstance(query, ElementValueQuery)


def test_element_value_query_any_value():
    query = cts.element_value_query("title")
    assert isinstance(query, ElementValueQuery)


test_element_word_query_ns = "https://example.com/cts-test"


def test_element_word_query():
    query = cts.element_word_query(
        fn.qname(test_element_word_query_ns, "title"),
        ["blue", "red"],
        options="case-insensitive",
        weight=2,
    )
    assert isinstance(query, ElementWordQuery)


def test_false_query():
    query = cts.false_query()
    assert isinstance(query, FalseQuery)
    assert query.compile() == ('xquery version "1.0-ml";\ncts:false-query()', {})


def test_field_range_query():
    query = cts.field_range_query("price", "<=", 2)
    assert isinstance(query, FieldRangeQuery)


def test_field_value_query():
    query = cts.field_value_query("price", ["1", "2"], weight=3)
    assert isinstance(query, FieldValueQuery)


def test_field_word_query():
    query = cts.field_word_query("title", "blue", options="lang=en", weight=2)
    assert isinstance(query, FieldWordQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:integer external;\ncts:field-word-que'
            'ry($v0, $v1, $v2, xs:double($v3))'
        ),
        {"v0": "title", "v1": "blue", "v2": "lang=en", "v3": "2"},
    )


def test_cts_geospatial_region_query_compilation():
    query = cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region", options=["unchecked", "coordinate-system=wgs84"],
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
        options="cached",
        weight=2,
    )
    assert isinstance(query, GeospatialRegionQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:string external;\ndeclare variable $v'
            '4 as xs:integer external;\ndeclare variable $v5 as xs:in'
            'teger external;\ndeclare variable $v6 as xs:integer exte'
            'rnal;\ndeclare variable $v7 as xs:integer external;\ndecl'
            'are variable $v8 as xs:string external;\ndeclare variabl'
            'e $v9 as xs:integer external;\ncts:geospatial-region-que'
            'ry(cts:geospatial-region-path-reference($v0, ($v1, $v2)'
            '), $v3, cts:box(xs:double($v4), xs:double($v5), xs:doub'
            'le($v6), xs:double($v7)), $v8, xs:double($v9))'
        ),
        {
            "v0": "/report/region",
            "v1": "unchecked",
            "v2": "coordinate-system=wgs84",
            "v3": "intersects",
            "v4": "1",
            "v5": "2",
            "v6": "3",
            "v7": "4",
            "v8": "cached",
            "v9": "2",
        },
    )


def test_cts_geospatial_region_query_serialization():
    query = cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region", options=["unchecked", "coordinate-system=wgs84"],
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
        options="cached",
        weight=2,
    )
    expected = {
        "geospatialRegionQuery": {
            "geospatialRegionPathReference": [
                {
                    "geospatialRegionPathReference": {
                        "pathExpression": "/report/region",
                        "coordinateSystem": "wgs84",
                    },
                },
            ],
            "operation": "intersects",
            "region": ["[1, 2, 3, 4]"],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}


def test_json_property_child_geospatial_query():
    query = cts.json_property_child_geospatial_query(
        "location", "point", cts.point(10, 20),
    )
    assert isinstance(query, JsonPropertyChildGeospatialQuery)


def test_json_property_geospatial_query():
    query = cts.json_property_geospatial_query("origin", cts.point(10, 20))
    assert isinstance(query, JsonPropertyGeospatialQuery)


def test_json_property_pair_geospatial_query():
    query = cts.json_property_pair_geospatial_query(
        "location", "lat", "lon", cts.point(10, 20),
    )
    assert isinstance(query, JsonPropertyPairGeospatialQuery)


def test_json_property_range_query():
    query = cts.json_property_range_query("price", ">", 10)
    assert isinstance(query, JsonPropertyRangeQuery)


def test_json_property_scope_query():
    query = cts.json_property_scope_query(["report", "note"], cts.true_query())
    assert isinstance(query, JsonPropertyScopeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:json-property-scope-query(($v0, $v1), cts:true-q'
            'uery())'
        ),
        {"v0": "report", "v1": "note"},
    )


def test_json_property_value_query_mixed():
    query = cts.json_property_value_query(["a", "b"], ["x", 7, 1.5, False])
    assert isinstance(query, JsonPropertyValueQuery)


def test_json_property_value_query_string():
    query = cts.json_property_value_query("label", "gamma")
    assert isinstance(query, JsonPropertyValueQuery)


def test_json_property_word_query():
    query = cts.json_property_word_query(
        ["title", "body"], ["blue", "green"], options=["lang=en", "exact"], weight=2,
    )
    assert isinstance(query, JsonPropertyWordQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:string external;\ndeclare variable $v'
            '4 as xs:string external;\ndeclare variable $v5 as xs:str'
            'ing external;\ndeclare variable $v6 as xs:integer extern'
            'al;\ncts:json-property-word-query(($v0, $v1), ($v2, $v3)'
            ', ($v4, $v5), xs:double($v6))'
        ),
        {
            "v0": "title",
            "v1": "body",
            "v2": "blue",
            "v3": "green",
            "v4": "lang=en",
            "v5": "exact",
            "v6": "2",
        },
    )


def test_locks_fragment_query():
    query = cts.locks_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, LocksFragmentQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:locks-fragment-query(cts:collection-q'
            'uery($v0))'
        ),
        {"v0": "reports"},
    )


test_lsqt_query_start = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def test_lsqt_query():
    query = cts.lsqt_query(
        "temporal", timestamp=test_lsqt_query_start, options="cached", weight=2,
    )
    assert isinstance(query, LsqtQuery)


def test_lsqt_query_defaults():
    query = cts.lsqt_query("temporal")
    assert isinstance(query, LsqtQuery)


def test_near_query():
    query = cts.near_query(
        [cts.true_query(), cts.false_query()],
        distance=2.5,
        options=["ordered", "minimum-distance=2"],
        distance_weight=0.5,
    )
    assert isinstance(query, NearQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:dou'
            'ble external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:double external;\ncts:near-query((cts'
            ':true-query(), cts:false-query()), $v0, ($v1, $v2), $v3'
            ')'
        ),
        {"v0": "2.5", "v1": "ordered", "v2": "minimum-distance=2", "v3": "0.5"},
    )


def test_not_in_query():
    query = cts.not_in_query(
        cts.collection_query("reports"), cts.collection_query("notes"),
    )
    assert isinstance(query, NotInQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:not-in-query(cts:collection-query($v0), cts:coll'
            'ection-query($v1))'
        ),
        {"v0": "reports", "v1": "notes"},
    )


def test_not_query():
    query = cts.not_query(cts.collection_query("reports"))
    assert isinstance(query, NotQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:not-query(cts:collection-query($v0))'
        ),
        {"v0": "reports"},
    )


def test_or_query():
    query = cts.or_query([cts.collection_query("reports")], options="synonym")
    assert isinstance(query, OrQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:or-query((cts:collection-query($v0)), $v1)'
        ),
        {"v0": "reports", "v1": "synonym"},
    )


def test_path_geospatial_query():
    query = cts.path_geospatial_query("/item/origin", cts.point(10, 20))
    assert isinstance(query, PathGeospatialQuery)


def test_path_range_query():
    query = cts.path_range_query("/item/price", ">", 1)
    assert isinstance(query, PathRangeQuery)


def test_period_compare_query():
    query = cts.period_compare_query(
        "system", "aln_equals", "valid", options="cached-incremental",
    )
    assert isinstance(query, PeriodCompareQuery)


test_period_range_query_start = datetime.datetime(
    2026, 1, 1, tzinfo=datetime.timezone.utc,
)
test_period_range_query_end = datetime.datetime(
    2026, 2, 1, tzinfo=datetime.timezone.utc,
)


def test_period_range_query():
    query = cts.period_range_query(
        ["valid", "system"],
        "aln_before",
        period=cts.period(test_period_range_query_start, test_period_range_query_end),
    )
    assert isinstance(query, PeriodRangeQuery)


def test_period_range_query_without_period():
    query = cts.period_range_query("valid", "aln_before")
    assert isinstance(query, PeriodRangeQuery)


def test_properties_fragment_query():
    query = cts.properties_fragment_query(cts.collection_query("reports"))
    assert isinstance(query, PropertiesFragmentQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:properties-fragment-query(cts:collect'
            'ion-query($v0))'
        ),
        {"v0": "reports"},
    )


def test_query_error_subclass_is_reported_with_its_context():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ("{not json",)))
    with pytest.raises(
        ValueError, match=r"^cts:reverse-query: nodes: Expecting",
    ) as error:
        query.to_json()
    argument_error = error.value.__cause__
    assert isinstance(argument_error.__cause__, json.JSONDecodeError)


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
def test_query_function_values_compile_but_cannot_serialize(method, value):
    query = cts.element_range_query("value", "=", value)
    (code, _) = query.compile()
    assert value.fn + "(" in code
    with pytest.raises(TypeError, match="value argument requires server evaluation"):
        getattr(query, method)()


@pytest.mark.parametrize("method", ["to_json", "to_xml", "to_combined_query"])
@pytest.mark.parametrize("value", ["1", "0"])
def test_query_json_property_boolean_cast_requires_server_evaluation(method, value):
    query = cts.json_property_value_query("v", FunctionCall("xs:boolean", (value,)))
    with pytest.raises(TypeError, match="value argument requires server evaluation"):
        getattr(query, method)()


@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            cts.and_query([], options=xs.string("bogus")),
            (
                "cts:and-query: options ['bogus'] are not and-query opti"
                "ons; use at most one of ordered, unordered"
            ),
        ),
        (
            cts.or_query([], options=xs.string("ordered")),
            (
                "cts:or-query: options ['ordered'] are not or-query opti"
                "ons; use at most one of synonym"
            ),
        ),
    ],
)
def test_query_options_resolved_from_expressions_are_checked_when_serialized(
    query, message,
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
def test_query_unsupported_literal_temporal_operator_is_rejected(build):
    with pytest.raises(ValueError, match="temporal operator") as error:
        build()
    assert str(error.value) == "unsupported temporal operator: 'bogus'"


def test_cts_range_query_compilation():
    query = cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
        weight=2,
    )
    assert isinstance(query, RangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:string external;\ndeclare '
            'variable $v3 as xs:string external;\ndeclare variable $v'
            '4 as xs:integer external;\ndeclare variable $v5 as xs:in'
            'teger external;\ndeclare variable $v6 as xs:string exter'
            'nal;\ndeclare variable $v7 as xs:integer external;\ncts:r'
            'ange-query(cts:element-reference(xs:QName($v0), ($v1, $'
            'v2)), xs:string($v3), ($v4, $v5), $v6, xs:double($v7))'
        ),
        {
            "v0": "price",
            "v1": "type=int",
            "v2": "unchecked",
            "v3": ">=",
            "v4": "2",
            "v5": "3",
            "v6": "cached",
            "v7": "2",
        },
    )


def test_cts_range_query_serialization():
    query = cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
        weight=2,
    )
    expected = {
        "rangeQuery": {
            "reference": [
                {
                    "elementReference": {
                        "namespaceURI": "",
                        "localname": "price",
                        "scalarType": "int",
                    },
                },
            ],
            "operator": ">=",
            "value": [{"type": "decimal", "val": "2"}, {"type": "decimal", "val": "3"}],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}


def test_registered_query():
    query = cts.registered_query([1, 2], options="unfiltered", weight=2)
    assert isinstance(query, RegisteredQuery)


def test_cts_reverse_query_compilation():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)), weight=2,
    )
    assert isinstance(query, ReverseQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:integer extern'
            'al;\ncts:reverse-query(xdmp:unquote($v0), xs:double($v1)'
            ')'
        ),
        {"v0": "<report>blue</report>", "v1": "2"},
    )


def test_cts_reverse_query_computed_nodes_require_evaluation():
    query = cts.reverse_query(fn.doc("/report.xml"))
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:reverse-query(fn:doc($v0))'
        ),
        {"v0": "/report.xml"},
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert (
        str(error.value)
        == (
            "cts:reverse-query: nodes: CTS node argument requires a "
            "literal xdmp:unquote call or server evaluation."
        )
    )


def test_cts_reverse_query_reserved_xml_namespace_prefix_requires_evaluation():
    source = (
        '<report xmlns:ns0="https://example.com/reports" kind="n'
        's0:blue" />'
    )
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert (
        str(error.value)
        == (
            "cts:reverse-query: nodes: CTS XML namespace prefixes ns"
            "N conflict with ElementTree; use named prefixes or serv"
            "er evaluation."
        )
    )


def test_cts_reverse_query_serialization():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)), weight=2,
    )
    expected = {"reverseQuery": {"nodes": ["<report>blue</report>"], "weight": 2}}
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}


def test_cts_runtime_query_query_compiles():
    source = '{"wordQuery":{"text":["blue"]}}'
    query = cts.query(FunctionCall("xdmp:unquote", (source,)))
    assert isinstance(query, RuntimeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:query(xdmp:unquote($v0))'
        ),
        {"v0": source},
    )


def test_runtime_query_composes():
    query = cts.and_query([cts.parse("blue"), cts.collection_query("reports")])
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:and-query((cts:parse($v0), cts:collection-query('
            '$v1)))'
        ),
        {"v0": "blue", "v1": "reports"},
    )


def test_cts_runtime_query_serialization_compiles():
    query = cts.parse("blue AND green")
    assert isinstance(query, RuntimeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:parse($v0)'
        ),
        {"v0": "blue AND green"},
    )


def test_cts_runtime_query_serialization_with_bindings_compiles():
    query = cts.parse("blue", bindings=FunctionCall("map:map"))
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ncts:parse($v0, map:map())'
        ),
        {"v0": "blue"},
    )


def test_cts_similar_query_comments_in_distinctive_term_options_are_skipped():
    options = (
        '<options xmlns="cts:distinctive-terms"><!-- tuned --><m'
        'ax-terms>20</max-terms><?review later?></options>'
    )
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    assert query.to_json()["similarQuery"]["options"] == {"maxTerms": 20}


def test_cts_similar_query_compilation():
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)), weight=2,
    )
    assert isinstance(query, SimilarQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:integer extern'
            'al;\ncts:similar-query(xdmp:unquote($v0), xs:double($v1)'
            ')'
        ),
        {"v0": "<report>blue</report>", "v1": "2"},
    )


def test_cts_similar_query_serialization():
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)), weight=2,
    )
    expected = {"similarQuery": {"nodes": ["<report>blue</report>"], "weight": 2}}
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}


def test_cts_triple_range_query_compilation():
    query = cts.triple_range_query(
        FunctionCall("sem:iri", ("https://example.com/r",)),
        FunctionCall("sem:iri", ("https://example.com/p",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    )
    assert isinstance(query, TripleRangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ndeclare variable $v2 as xs:integer external;\ndeclare'
            ' variable $v3 as xs:boolean external;\ndeclare variable '
            '$v4 as xs:string external;\ndeclare variable $v5 as xs:s'
            'tring external;\ndeclare variable $v6 as xs:string exter'
            'nal;\ndeclare variable $v7 as xs:integer external;\ncts:t'
            'riple-range-query(sem:iri($v0), sem:iri($v1), ($v2, $v3'
            ', $v4), $v5, $v6, xs:double($v7))'
        ),
        {
            "v0": "https://example.com/r",
            "v1": "https://example.com/p",
            "v2": "2",
            "v3": True,
            "v4": "blue",
            "v5": ">",
            "v6": "cached",
            "v7": "2",
        },
    )


def test_cts_triple_range_query_serialization():
    query = cts.triple_range_query(
        FunctionCall("sem:iri", ("https://example.com/r",)),
        FunctionCall("sem:iri", ("https://example.com/p",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    )
    expected = {
        "tripleRangeQuery": {
            "objectOperator": ">",
            "subject": ["https://example.com/r"],
            "predicate": ["https://example.com/p"],
            "object": [
                {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "value": 2},
                {"datatype": "http://www.w3.org/2001/XMLSchema#boolean", "value": True},
                {
                    "datatype": "http://www.w3.org/2001/XMLSchema#string",
                    "value": "blue",
                },
            ],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}


def test_true_query():
    query = cts.true_query()
    assert isinstance(query, TrueQuery)
    assert query.compile() == ('xquery version "1.0-ml";\ncts:true-query()', {})


def test_word_query():
    query = cts.word_query("blue", options="lang=en")
    assert isinstance(query, WordQuery)
    assert isinstance(query, CtsQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            'ing external;\ndeclare variable $v1 as xs:string externa'
            'l;\ncts:word-query($v0, $v1)'
        ),
        {"v0": "blue", "v1": "lang=en"},
    )


def test_word_query_combined_query():
    assert cts.word_query("blue").to_combined_query() == {
        "search": {"ctsquery": {"wordQuery": {"text": ["blue"]}}},
    }


def test_word_query_independent_json(mocker):
    mocker.patch.object(WordQuery, "to_xml", side_effect=AssertionError)
    assert cts.word_query("blue").to_json() == {"wordQuery": {"text": ["blue"]}}


def test_word_query_independent_xml(mocker):
    mocker.patch.object(WordQuery, "to_json", side_effect=AssertionError)
    assert (
        tostring(cts.word_query("blue").to_xml())
        == (
            b'<cts:word-query xmlns:cts="http://marklogic.com/cts"><c'
            b'ts:text>blue</cts:text></cts:word-query>'
        )
    )


def test_word_query_snapshot():
    texts = ["blue"]
    query = cts.word_query(texts)
    texts.append("green")
    output = query.serialize()
    output["wordQuery"]["text"].append("red")
    assert query.serialize() == {"wordQuery": {"text": ["blue"]}}


test_period_range_query_full_options_start = datetime.datetime(
    2026, 1, 1, tzinfo=datetime.timezone.utc,
)
test_period_range_query_full_options_end = datetime.datetime(
    2026, 2, 1, tzinfo=datetime.timezone.utc,
)


def test_period_range_query_full_options():
    query = cts.period_range_query(
        ["valid", "system"],
        "aln_before",
        period=cts.period(
            test_period_range_query_full_options_start,
            test_period_range_query_full_options_end,
        ),
        options="cached",
    )
    assert isinstance(query, PeriodRangeQuery)


@pytest.mark.parametrize(
    "constructor", [cts.similar_query, cts.reverse_query, SimilarQuery, ReverseQuery],
)
def test_python_nodes_cts_models_accept_python_nodes_and_sequences(constructor):
    element = fromstring("<report>blue</report>")
    models = [{"label": "blue"}, element, ElementTree(element)]
    query = constructor(models)
    key = (
        "similarQuery"
        if constructor in (cts.similar_query, SimilarQuery)
        else "reverseQuery"
    )
    assert query.to_json() == {
        key: {
            "nodes": [
                {"label": "blue"},
                "<report>blue</report>",
                "<report>blue</report>",
            ],
        },
    }
    assert "<report>blue</report>" in tostring(query.to_xml(), encoding="unicode")
    models[0]["label"] = "changed"
    element.text = "changed"
    assert query.to_json()[key]["nodes"][0] == {"label": "blue"}
    assert query.to_json()[key]["nodes"][1] == "<report>blue</report>"


def test_python_nodes_python_xml_namespaces_attributes_comments_and_tail():
    root = fromstring(
        (
            '<r:report xmlns:r="https://example.com/reports" xmlns:a'
            '="https://example.com/attributes" a:flag="yes">blue</r:'
            'report>'
        ),
    )
    root.set("xmlns:node0", "https://example.com/existing-prefix")
    root.append(Comment("retained"))
    root.append(ProcessingInstruction("status", "ready"))
    SubElement(root, "{https://example.com/reports}label").text = "ns0:literal text"
    query = cts.similar_query(root)
    serialized = query.to_xml()
    model = serialized.find("{http://marklogic.com/cts}node")[0]
    assert model.tag == "{https://example.com/reports}report"
    assert model.attrib["{https://example.com/attributes}flag"] == "yes"
    assert model.find("{https://example.com/reports}label").text == "ns0:literal text"
    assert "<!--retained-->" in tostring(serialized, encoding="unicode")
    assert "<?status ready?>" in tostring(serialized, encoding="unicode")


def test_direct_query_serializes_like_the_builder():
    assert (
        ElementRangeQuery("price", ">=", 10).to_json()
        == cts.element_range_query("price", ">=", 10).to_json()
    )


def test_cts_range_query_reference_names_and_nullable_options_in_json():
    query = cts.range_query(
        [
            cts.field_reference("price", options=["type=int", "non-nullable"]),
            cts.json_property_reference("price", options="type=int"),
            cts.path_reference("/report/price", options="type=int"),
            cts.uri_reference(),
            cts.collection_reference(),
            cts.iri_reference(),
        ],
        "=",
        "blue",
    )
    assert query.to_json() == {
        "rangeQuery": {
            "reference": [
                {
                    "fieldReference": {
                        "fieldName": "price",
                        "scalarType": "int",
                        "nullable": False,
                    },
                },
                {"jsonPropertyReference": {"property": "price", "scalarType": "int"}},
                {
                    "pathReference": {
                        "pathExpression": "/report/price",
                        "scalarType": "int",
                    },
                },
                {"uriReference": {}},
                {"collectionReference": {}},
                {"iriReference": {}},
            ],
            "operator": "=",
            "value": [{"type": "string", "val": "blue"}],
        },
    }


def test_cts_range_query_reference_names_and_nullable_options_in_xml():
    query = cts.range_query(
        [
            cts.element_attribute_reference(
                fn.qname("https://example.com/reports", "report"),
                "label",
                options=[
                    "type=string",
                    "collation=http://marklogic.com/collation/",
                    "nullable",
                ],
            ),
            cts.field_reference("price", options=["type=int", "non-nullable"]),
            cts.json_property_reference("price", options="type=int"),
            cts.path_reference("/report/price", options="type=int"),
            cts.uri_reference(),
            cts.collection_reference(),
            cts.iri_reference(),
        ],
        "=",
        "blue",
    )
    assert (
        tostring(query.to_xml(), encoding="unicode")
        == (
            '<cts:range-query xmlns:cts="http://marklogic.com/cts" x'
            'mlns:xsi="http://www.w3.org/2001/XMLSchema-instance" op'
            'erator="="><cts:element-attribute-reference><cts:parent'
            '-namespace-uri>https://example.com/reports</cts:parent-'
            'namespace-uri><cts:parent-localname>report</cts:parent-'
            'localname><cts:namespace-uri /><cts:localname>label</ct'
            's:localname><cts:scalar-type>string</cts:scalar-type><c'
            'ts:collation>http://marklogic.com/collation/</cts:colla'
            'tion><cts:nullable>true</cts:nullable></cts:element-att'
            'ribute-reference><cts:field-reference><cts:field-name>p'
            'rice</cts:field-name><cts:scalar-type>int</cts:scalar-t'
            'ype><cts:nullable>false</cts:nullable></cts:field-refer'
            'ence><cts:json-property-reference><cts:property>price</'
            'cts:property><cts:scalar-type>int</cts:scalar-type></ct'
            's:json-property-reference><cts:path-reference><cts:path'
            '-expression>/report/price</cts:path-expression><cts:sca'
            'lar-type>int</cts:scalar-type></cts:path-reference><cts'
            ':uri-reference /><cts:collection-reference /><cts:iri-r'
            'eference /><cts:value xmlns:xs="http://www.w3.org/2001/'
            'XMLSchema" xsi:type="xs:string">blue</cts:value></cts:r'
            'ange-query>'
        )
    )


def test_python_nodes_python_options_element_serializes_locally():
    options = fromstring(
        (
            '<options xmlns="cts:distinctive-terms"><max-terms>20</m'
            'ax-terms></options>'
        ),
    )
    assert cts.similar_query({"label": "blue"}, options=options).to_json() == {
        "similarQuery": {"nodes": [{"label": "blue"}], "options": {"maxTerms": 20}},
    }


def test_similar_query_unquoted_json_node():
    query = cts.similar_query(xdmp.unquote('{"label":"blue","count":2}'))
    assert query.to_json() == {
        "similarQuery": {"nodes": [{"label": "blue", "count": 2}]},
    }
