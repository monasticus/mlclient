"""Verify structured JSON preserves XML through MarkLogic REST conversion."""

from tests.utils.resources import render_test_resource

import json
import os
from xml.etree import ElementTree

import pytest

from mlclient import MLClient
from mlclient.search import QueryComponent
from mlclient.search.structured import (
    AndNotQuery,
    AndQuery,
    Attribute,
    BoostQuery,
    Box,
    Circle,
    CollectionConstraintQuery,
    CollectionQuery,
    ContainerConstraintQuery,
    ContainerQuery,
    CustomConstraintQuery,
    DirectoryQuery,
    DocumentFragmentQuery,
    DocumentQuery,
    Element,
    ElementConstraintQuery,
    FalseQuery,
    Field,
    GeoAttributePairQuery,
    GeoElementPairQuery,
    GeoElementQuery,
    GeoJsonPropertyPairQuery,
    GeoJsonPropertyQuery,
    GeoPathQuery,
    GeoRegionConstraintQuery,
    GeoRegionPathQuery,
    GeospatialConstraintQuery,
    JsonProperty,
    LocksFragmentQuery,
    LsqtQuery,
    NearQuery,
    NotInQuery,
    NotQuery,
    OperatorState,
    OrQuery,
    PathIndex,
    Period,
    PeriodCompareQuery,
    PeriodRangeQuery,
    Point,
    Polygon,
    PropertiesConstraintQuery,
    PropertiesFragmentQuery,
    QtextQuery,
    Query,
    RangeConstraintQuery,
    RangeQuery,
    TermQuery,
    TrueQuery,
    ValueConstraintQuery,
    ValueQuery,
    WordConstraintQuery,
    WordQuery,
    sq,
)

pytestmark = pytest.mark.ml_access


class TestStructuredQuerySerialization:
    @pytest.fixture(scope="class")
    @staticmethod
    def ml_client():
        with MLClient(port=int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))) as ml:
            yield ml

    def test_and_not_query(self, ml_client):
        query = AndNotQuery(TermQuery("blue"), TermQuery("green"))
        self._assert_native_serialization(ml_client, query)

    def test_and_query(self, ml_client):
        query = AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True)
        self._assert_native_serialization(ml_client, query)

    def test_attribute(self, ml_client):
        query = Attribute("status", "urn:example")
        self._assert_native_serialization(ml_client, query)

    def test_boost_query(self, ml_client):
        query = BoostQuery(TermQuery("blue"), TermQuery("green", weight=2))
        self._assert_native_serialization(ml_client, query)

    def test_box(self, ml_client):
        query = Box(5, 15, 25, 35)
        self._assert_native_serialization(ml_client, query)

    def test_circle(self, ml_client):
        query = Circle(3, Point(10, 20))
        self._assert_native_serialization(ml_client, query)

    def test_collection_constraint_query(self, ml_client):
        query = CollectionConstraintQuery("category", ["blue", "green"])
        self._assert_native_serialization(ml_client, query)

    def test_collection_query(self, ml_client):
        query = CollectionQuery(["reports", "notes"])
        self._assert_native_serialization(ml_client, query)

    def test_container_constraint_query(self, ml_client):
        query = ContainerConstraintQuery("section", TrueQuery())
        self._assert_native_serialization(ml_client, query)

    def test_container_query(self, ml_client):
        query = ContainerQuery(
            Element("section", "urn:example"),
            TermQuery("blue"),
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_custom_constraint_query(self, ml_client):
        query = CustomConstraintQuery("custom", ["blue", "green"])
        self._assert_native_serialization(ml_client, query)

    def test_directory_query(self, ml_client):
        query = DirectoryQuery(["/reports/", "/notes/"], infinite=False)
        self._assert_native_serialization(ml_client, query)

    def test_document_fragment_query(self, ml_client):
        query = DocumentFragmentQuery(TermQuery("blue"))
        self._assert_native_serialization(ml_client, query)

    def test_document_query(self, ml_client):
        query = DocumentQuery(["/reports/first.xml", "/reports/second.json"])
        self._assert_native_serialization(ml_client, query)

    def test_element(self, ml_client):
        query = Element("label", "urn:example")
        self._assert_native_serialization(ml_client, query)

    def test_element_constraint_query(self, ml_client):
        query = ElementConstraintQuery("section", TrueQuery())
        self._assert_native_serialization(ml_client, query)

    def test_false_query(self, ml_client):
        query = FalseQuery()
        self._assert_native_serialization(ml_client, query)

    def test_field(self, ml_client):
        query = Field("body", collation="http://marklogic.com/collation/")
        self._assert_native_serialization(ml_client, query)

    def test_geo_attribute_pair_query(self, ml_client):
        query = GeoAttributePairQuery(
            Element("place"),
            Attribute("lat"),
            Attribute("lon"),
            Point(10, 20),
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_element_pair_query(self, ml_client):
        query = GeoElementPairQuery(
            Element("place"),
            Element("lat"),
            Element("lon"),
            Point(10, 20),
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_element_query(self, ml_client):
        query = GeoElementQuery(
            Element("location"),
            Point(10, 20),
            parent=Element("place"),
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_json_property_pair_query(self, ml_client):
        query = GeoJsonPropertyPairQuery(
            JsonProperty("place"),
            JsonProperty("lat"),
            JsonProperty("lon"),
            Point(10, 20),
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_json_property_query(self, ml_client):
        query = GeoJsonPropertyQuery(
            JsonProperty("location"),
            Point(10, 20),
            parent=JsonProperty("place"),
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_path_query(self, ml_client):
        query = GeoPathQuery(
            PathIndex("/place/location"),
            Point(10, 20),
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_region_constraint_query(self, ml_client):
        query = GeoRegionConstraintQuery(
            "location",
            Point(10, 20),
            operator="intersects",
            weight=2,
        )
        self._assert_native_serialization(ml_client, query)

    def test_geo_region_path_query(self, ml_client):
        query = GeoRegionPathQuery(
            PathIndex("/place/region"),
            Point(10, 20),
            operator="intersects",
            coord="wgs84",
            options=["units=miles"],
            weight=2,
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_geospatial_constraint_query(self, ml_client):
        query = GeospatialConstraintQuery("location", Point(10, 20), text="nearby")
        self._assert_native_serialization(ml_client, query)

    def test_json_property(self, ml_client):
        query = JsonProperty("title")
        self._assert_native_serialization(ml_client, query)

    def test_locks_fragment_query(self, ml_client):
        query = LocksFragmentQuery(TermQuery("blue"))
        self._assert_native_serialization(ml_client, query)

    def test_lsqt_query(self, ml_client):
        query = LsqtQuery(
            "reports",
            timestamp="2024-01-01T00:00:00Z",
            options=["cached-incremental"],
            weight=2,
        )
        self._assert_native_serialization(ml_client, query)

    def test_near_query(self, ml_client):
        query = NearQuery(
            [TermQuery("blue"), TermQuery("green")],
            distance=3,
            minimum_distance=1,
            distance_weight=2,
            ordered=False,
        )
        self._assert_native_serialization(ml_client, query)

    def test_not_in_query(self, ml_client):
        query = NotInQuery(TermQuery("blue"), TermQuery("green"))
        self._assert_native_serialization(ml_client, query)

    def test_not_query(self, ml_client):
        query = NotQuery(TermQuery("blue"))
        self._assert_native_serialization(ml_client, query)

    def test_operator_state(self, ml_client):
        query = OperatorState("sort", "relevance")
        self._assert_native_serialization(ml_client, query)

    def test_or_query(self, ml_client):
        query = OrQuery([TermQuery("blue"), TermQuery("green")])
        self._assert_native_serialization(ml_client, query)

    def test_path_index(self, ml_client):
        query = PathIndex("/report/price")
        self._assert_native_serialization(ml_client, query)

    def test_period(self, ml_client):
        query = Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")
        self._assert_native_serialization(ml_client, query)

    def test_period_compare_query(self, ml_client):
        query = PeriodCompareQuery("system", "aln_equals", "valid", options=["cached"])
        self._assert_native_serialization(ml_client, query)

    def test_period_range_query(self, ml_client):
        query = PeriodRangeQuery(
            ["valid", "system"],
            "aln_contains",
            [Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")],
            options=["cached"],
            weight=2,
        )
        self._assert_native_serialization(ml_client, query)

    def test_point(self, ml_client):
        query = Point(10, 20)
        self._assert_native_serialization(ml_client, query)

    def test_polygon(self, ml_client):
        query = Polygon([Point(10, 20), Point(11, 21), Point(10, 22)])
        self._assert_native_serialization(ml_client, query)

    def test_properties_constraint_query(self, ml_client):
        query = PropertiesConstraintQuery("metadata", TrueQuery())
        self._assert_native_serialization(ml_client, query)

    def test_properties_fragment_query(self, ml_client):
        query = PropertiesFragmentQuery(TermQuery("blue"))
        self._assert_native_serialization(ml_client, query)

    def test_qtext_query(self, ml_client):
        query = QtextQuery("blue AND green")
        self._assert_native_serialization(ml_client, query)

    def test_query(self, ml_client):
        query = Query([TermQuery("blue"), CollectionQuery("reports")])
        self._assert_native_serialization(ml_client, query)

    def test_query_builder(self, ml_client):
        query = sq.query(
            sq.and_(
                sq.range(sq.element("price"), 20, operator="GE", index_type="xs:int"),
                sq.term("blue"),
            ),
        )
        self._assert_native_serialization(ml_client, query)

    def test_range_constraint_query(self, ml_client):
        query = RangeConstraintQuery("price", [3, 4], operator="EQ", options=["cached"])
        self._assert_native_serialization(ml_client, query)

    def test_range_query(self, ml_client):
        query = RangeQuery(
            Element("price"),
            [3, 4],
            operator="EQ",
            index_type="xs:int",
            collation="urn:example",
            options=["cached"],
            weight=2,
            fragment_scope="documents",
            attribute=Attribute("amount"),
        )
        self._assert_native_serialization(ml_client, query)

    def test_term_query(self, ml_client):
        query = TermQuery(
            ["blue", "green"],
            weight=2,
            options=["case-sensitive", "unstemmed"],
        )
        self._assert_native_serialization(ml_client, query)

    def test_true_query(self, ml_client):
        query = TrueQuery()
        self._assert_native_serialization(ml_client, query)

    def test_value_constraint_query(self, ml_client):
        query = ValueConstraintQuery("status", ["blue", "green"], weight=2)
        self._assert_native_serialization(ml_client, query)

    def test_value_query(self, ml_client):
        query = ValueQuery(
            JsonProperty("active"),
            True,
            node_type="boolean",
            options=["exact"],
            weight=2,
            fragment_scope="documents",
        )
        self._assert_native_serialization(ml_client, query)

    def test_word_constraint_query(self, ml_client):
        query = WordConstraintQuery("title", ["blue", "green"], weight=2)
        self._assert_native_serialization(ml_client, query)

    def test_word_query(self, ml_client):
        query = WordQuery(
            [Element("title"), Element("label")],
            ["blue", "green"],
            attribute=[Attribute("name"), Attribute("alt")],
            options=["case-sensitive"],
            weight=2,
            fragment_scope="documents",
        )
        self._assert_native_serialization(ml_client, query)

    @staticmethod
    def _assert_native_serialization(ml: MLClient, query: QueryComponent):
        xml = ElementTree.tostring(query.serialize("xml"), encoding="unicode")
        result = ml.eval.xquery(
            render_test_resource(__file__, "assert-native-serialization.xqy"),
            variables={"xml": xml, "json": json.dumps(query.serialize())},
        )
        assert result is True, result
