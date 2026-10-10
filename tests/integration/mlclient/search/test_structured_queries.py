(
    "Verify structured-query XML against native MarkLogic qu"
    "ery constructors."
)

from __future__ import annotations
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
from uuid import uuid4
from mlclient.http import HTTPConfig
from mlclient.search.structured import StructuredQuery

pytestmark = pytest.mark.ml_access


class TestStructuredQueries:
    @pytest.fixture(scope="class")
    @staticmethod
    def ml_database():
        port = int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))
        manage_port = int(os.environ.get("MLCLIENT_CTS_MANAGE_PORT", "8002"))
        name = f"mlclient-structured-test-{uuid4().hex}"
        schemas = f"{name}-schemas"
        with MLClient(
            port=port, manage_config=HTTPConfig.resolve(port=manage_port),
        ) as ml:
            host = ml.eval.xquery(render_test_resource(__file__, "ml-database.xqy"))
            ml.manage.databases.create({"database-name": schemas}).raise_for_status()
            try:
                ml.manage.forests.create(
                    {"forest-name": schemas, "host": host, "database": schemas},
                ).raise_for_status()
                ml.manage.databases.create(
                    {"database-name": name, "schema-database": schemas},
                ).raise_for_status()
                try:
                    _configure_indexes(ml, name)
                    ml.manage.forests.create(
                        {"forest-name": name, "host": host, "database": name},
                    ).raise_for_status()
                    _create_temporal_axes(ml, name)
                    yield (ml, name)
                finally:
                    ml.manage.databases.delete(
                        name, forest_delete="data",
                    ).raise_for_status()
            finally:
                ml.manage.databases.delete(
                    schemas, forest_delete="data",
                ).raise_for_status()

    def test_and_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True),
            render_test_resource(__file__, "test-and-query.xqy"),
        )

    def test_and_not_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            AndNotQuery(TermQuery("blue"), TermQuery("green")),
            render_test_resource(__file__, "test-and-not-query.xqy"),
        )

    def test_boost_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            BoostQuery(TermQuery("blue"), TermQuery("green", weight=2)),
            render_test_resource(__file__, "test-boost-query.xqy"),
        )

    def test_collection_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            CollectionQuery(["reports", "notes"]),
            render_test_resource(__file__, "test-collection-query.xqy"),
        )

    def test_container_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ContainerQuery(
                Element("section", "https://example.com/example"), TermQuery("blue"),
            ),
            render_test_resource(__file__, "test-container-query.xqy"),
        )

    def test_directory_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            DirectoryQuery(["/reports/", "/notes/"], infinite=False),
            render_test_resource(__file__, "test-directory-query.xqy"),
        )

    def test_document_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            DocumentQuery(["/reports/first.xml", "/reports/second.json"]),
            render_test_resource(__file__, "test-document-query.xqy"),
        )

    def test_document_fragment_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            DocumentFragmentQuery(TermQuery("blue")),
            render_test_resource(__file__, "test-document-fragment-query.xqy"),
        )

    def test_false_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            FalseQuery(),
            render_test_resource(__file__, "test-false-query.xqy"),
        )

    def test_locks_fragment_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            LocksFragmentQuery(TermQuery("blue")),
            render_test_resource(__file__, "test-locks-fragment-query.xqy"),
        )

    def test_near_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            NearQuery(
                [TermQuery("blue"), TermQuery("green")],
                distance=3,
                minimum_distance=1,
                distance_weight=2,
                ordered=False,
            ),
            render_test_resource(__file__, "test-near-query.xqy"),
        )

    def test_not_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            NotQuery(TermQuery("blue")),
            render_test_resource(__file__, "test-not-query.xqy"),
        )

    def test_not_in_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            NotInQuery(TermQuery("blue"), TermQuery("green")),
            render_test_resource(__file__, "test-not-in-query.xqy"),
        )

    def test_or_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            OrQuery([TermQuery("blue"), TermQuery("green")]),
            render_test_resource(__file__, "test-or-query.xqy"),
        )

    def test_properties_fragment_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PropertiesFragmentQuery(TermQuery("blue")),
            render_test_resource(__file__, "test-properties-fragment-query.xqy"),
        )

    def test_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            Query([TermQuery("blue"), CollectionQuery("reports")]),
            render_test_resource(__file__, "test-query.xqy"),
        )

    def test_range_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(
                Element("price"),
                [3, 4],
                operator="EQ",
                index_type="xs:int",
                options=["cached"],
                weight=2,
            ),
            render_test_resource(__file__, "test-range-query.xqy"),
        )

    def test_term_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            TermQuery(
                ["blue", "green"], weight=2, options=["case-sensitive", "unstemmed"],
            ),
            render_test_resource(__file__, "test-term-query.xqy"),
        )

    def test_true_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            TrueQuery(),
            render_test_resource(__file__, "test-true-query.xqy"),
        )

    def test_value_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(
                JsonProperty("active"),
                True,
                node_type="boolean",
                options=["exact"],
                weight=2,
            ),
            render_test_resource(__file__, "test-value-query.xqy"),
        )

    def test_value_query_number(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(JsonProperty("count"), 7, node_type="number"),
            render_test_resource(__file__, "test-value-query-number.xqy"),
        )

    def test_value_query_null(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(JsonProperty("count"), "", node_type="null"),
            render_test_resource(__file__, "test-value-query-null.xqy"),
        )

    def test_word_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordQuery(
                [Element("title"), Element("label")],
                ["blue", "green"],
                attribute=[Attribute("name"), Attribute("alt")],
                options=["case-sensitive"],
                weight=2,
            ),
            render_test_resource(__file__, "test-word-query.xqy"),
        )

    def test_path_range_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(
                PathIndex(
                    "/r:report/r:price", {"r": "https://example.com/example/reports"},
                ),
                3,
                operator="GE",
                index_type="xs:int",
            ),
            render_test_resource(__file__, "test-path-range-query.xqy"),
        )

    def test_collection_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            CollectionConstraintQuery("category", ["blue", "green"]),
            render_test_resource(__file__, "test-collection-constraint-query.xqy"),
            options=(
                '<constraint name="category"><collection prefix="reports'
                '/"/></constraint>'
            ),
        )

    def test_container_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ContainerConstraintQuery("section", TermQuery("blue")),
            render_test_resource(__file__, "test-container-constraint-query.xqy"),
            options=(
                '<constraint name="section"><container><element name="se'
                'ction" ns=""/></container></constraint>'
            ),
        )

    def test_element_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ElementConstraintQuery("section", TermQuery("blue")),
            render_test_resource(__file__, "test-element-constraint-query.xqy"),
            options=(
                '<constraint name="section"><element-query name="section'
                '" ns=""/></constraint>'
            ),
        )

    def test_properties_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PropertiesConstraintQuery("metadata", TermQuery("blue")),
            render_test_resource(__file__, "test-properties-constraint-query.xqy"),
            options='<constraint name="metadata"><properties/></constraint>',
        )

    def test_range_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeConstraintQuery("price", 3, operator="GE", options=["cached"]),
            render_test_resource(__file__, "test-range-constraint-query.xqy"),
            options=(
                '<constraint name="price"><range type="xs:int" facet="fa'
                'lse"><element name="price" ns=""/></range></constraint>'
            ),
        )

    def test_word_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordConstraintQuery("title", ["blue", "green"], weight=2),
            render_test_resource(__file__, "test-word-constraint-query.xqy"),
            options=(
                '<constraint name="title"><word><element name="title" ns'
                '=""/></word></constraint>'
            ),
        )

    def test_value_text_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("status", ["blue", "green"], weight=2),
            render_test_resource(__file__, "test-value-text-constraint-query.xqy"),
            options=(
                '<constraint name="status"><value><element name="status"'
                ' ns=""/></value></constraint>'
            ),
        )

    def test_value_boolean_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("active", False),
            render_test_resource(__file__, "test-value-boolean-constraint-query.xqy"),
            options=(
                '<constraint name="active"><value type="boolean"><json-p'
                'roperty>active</json-property></value></constraint>'
            ),
        )

    def test_value_number_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("count", 7),
            render_test_resource(__file__, "test-value-number-constraint-query.xqy"),
            options=(
                '<constraint name="count"><value type="number"><json-pro'
                'perty>count</json-property></value></constraint>'
            ),
        )

    def test_value_null_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("count"),
            render_test_resource(__file__, "test-value-null-constraint-query.xqy"),
            options=(
                '<constraint name="count"><value type="null"><json-prope'
                'rty>count</json-property></value></constraint>'
            ),
        )

    def test_alternative_word_constraints(self, ml_database):
        self._assert_native_query(
            ml_database,
            OrQuery(
                [
                    WordConstraintQuery("title", "blue"),
                    WordConstraintQuery("label", "blue"),
                ],
            ),
            render_test_resource(__file__, "test-alternative-word-constraints.xqy"),
            options=(
                '<constraint name="title"><word><element name="title" ns'
                '=""/></word></constraint><constraint name="label"><word'
                '><element name="label" ns=""/></word></constraint>'
            ),
        )

    def test_custom_constraint_query(self, ml_database):
        (ml, database) = ml_database
        module = render_test_resource(__file__, "test-custom-constraint-query.xqy")
        ml.eval.xquery(
            render_test_resource(__file__, "test-custom-constraint-query-2.xqy"),
            variables={"module": module},
            database=database,
        )
        self._assert_native_query(
            ml_database,
            CustomConstraintQuery("custom", ["blue", "green"]),
            render_test_resource(__file__, "test-custom-constraint-query-3.xqy"),
            options=(
                '<constraint name="custom"><custom facet="false"><parse '
                'apply="parse" ns="https://example.com/example/structure'
                'd-custom" at="/structured-custom.xqy"/></custom></const'
                'raint>'
            ),
            modules_database=True,
        )

    def test_geo_element_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoElementQuery(
                Element("location"), Point(10, 20), options=["units=miles"], weight=2,
            ),
            render_test_resource(__file__, "test-geo-element-query.xqy"),
        )

    def test_geo_child_element_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoElementQuery(
                Element("location"), Point(10, 20), parent=Element("place"),
            ),
            render_test_resource(__file__, "test-geo-child-element-query.xqy"),
        )

    def test_geo_element_pair_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoElementPairQuery(
                Element("place"), Element("lat"), Element("lon"), Box(1, 2, 3, 4),
            ),
            render_test_resource(__file__, "test-geo-element-pair-query.xqy"),
        )

    def test_geo_attribute_pair_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoAttributePairQuery(
                Element("place"),
                Attribute("lat"),
                Attribute("lon"),
                Circle(5, Point(10, 20)),
            ),
            render_test_resource(__file__, "test-geo-attribute-pair-query.xqy"),
        )

    def test_geo_json_property_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoJsonPropertyQuery(
                JsonProperty("location"),
                Polygon([Point(1, 2), Point(3, 4), Point(5, 6), Point(1, 2)]),
                parent=JsonProperty("place"),
            ),
            render_test_resource(__file__, "test-geo-json-property-query.xqy"),
        )

    def test_geo_json_property_pair_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoJsonPropertyPairQuery(
                JsonProperty("place"),
                JsonProperty("lat"),
                JsonProperty("lon"),
                Point(10, 20),
            ),
            render_test_resource(__file__, "test-geo-json-property-pair-query.xqy"),
        )

    def test_period_compare_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PeriodCompareQuery("system", "aln_equals", "valid"),
            render_test_resource(__file__, "test-period-compare-query.xqy"),
        )

    def test_period_range_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PeriodRangeQuery(
                "valid",
                "aln_contains",
                Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
            ),
            render_test_resource(__file__, "test-period-range-query.xqy"),
        )

    def test_lsqt_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            LsqtQuery("reports-temporal", timestamp="1600-01-01T00:00:00Z", weight=2),
            render_test_resource(__file__, "test-lsqt-query.xqy"),
        )

    def test_word_query_on_a_field(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordQuery(Field("summary"), "blue"),
            render_test_resource(__file__, "test-word-query-on-a-field.xqy"),
        )

    def test_word_query_on_a_json_property(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordQuery(JsonProperty("title"), "blue"),
            render_test_resource(__file__, "test-word-query-on-a-json-property.xqy"),
        )

    def test_value_query_on_a_json_property(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(JsonProperty("title"), "blue"),
            render_test_resource(__file__, "test-value-query-on-a-json-property.xqy"),
        )

    def test_range_query_on_a_field(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(Field("summary"), 3, operator="GE", index_type="xs:int"),
            render_test_resource(__file__, "test-range-query-on-a-field.xqy"),
        )

    def test_range_query_on_a_json_property(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(JsonProperty("price"), 3, operator="GE", index_type="xs:int"),
            render_test_resource(__file__, "test-range-query-on-a-json-property.xqy"),
        )

    def test_geo_path_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoPathQuery(PathIndex("/report/location"), Point(10, 20), weight=2),
            render_test_resource(__file__, "test-geo-path-query.xqy"),
        )

    def test_geo_region_path_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoRegionPathQuery(
                PathIndex("/report/area"),
                Box(1, 2, 3, 4),
                operator="intersects",
                coord="wgs84",
            ),
            render_test_resource(__file__, "test-geo-region-path-query.xqy"),
        )

    def test_geospatial_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeospatialConstraintQuery("loc", Point(10, 20)),
            render_test_resource(__file__, "test-geospatial-constraint-query.xqy"),
            options=(
                '<constraint name="loc"><geo-elem><element name="locatio'
                'n" ns=""/></geo-elem></constraint>'
            ),
        )

    def test_geo_region_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoRegionConstraintQuery("area", Box(1, 2, 3, 4), operator="intersects"),
            render_test_resource(__file__, "test-geo-region-constraint-query.xqy"),
            options=(
                '<constraint name="area"><geo-region-path coord="wgs84">'
                '<path-index>/report/area</path-index></geo-region-path>'
                '</constraint>'
            ),
        )

    def test_qtext_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            QtextQuery("blue green"),
            render_test_resource(__file__, "test-qtext-query.xqy"),
        )

    def test_operator_state(self, ml_database):
        (ml, database) = ml_database
        query = Query([TrueQuery(), OperatorState("nresults", "few")])
        result = ml.eval.xquery(
            render_test_resource(__file__, "test-operator-state.xqy"),
            variables={
                "query": ElementTree.tostring(
                    query.serialize("xml"), encoding="unicode",
                ),
                "query_json": json.dumps(query.serialize()),
            },
            database=database,
        )
        assert result == [2, 2]

    @staticmethod
    def _assert_native_query(
        ml_database,
        query: StructuredQuery,
        native: str,
        *,
        options: str = "",
        modules_database: bool = False,
    ):
        (ml, database) = ml_database
        wrapper = query if isinstance(query, Query) else Query(query)
        xml = ElementTree.tostring(wrapper.serialize("xml"), encoding="unicode")
        code = render_test_resource(__file__, "assert-native-query.xqy", native=native)
        variables = {
            "query": xml,
            "query_json": json.dumps(wrapper.serialize()),
            "options": f'<options xmlns="http://marklogic.com/appservices/search">{options}</options>',
        }
        if modules_database:
            variables["code"] = code
            code = render_test_resource(__file__, "assert-native-query-2.xqy")
        result = ml.eval.xquery(code, variables=variables, database=database)
        assert result is True, [
            ElementTree.tostring(item, encoding="unicode") for item in result
        ]


def _configure_indexes(ml: MLClient, database: str):
    (
        "Add the range indexes the native comparisons and tempor"
        "al axes need."
    )
    temporal_indexes = [
        {
            "scalar-type": "dateTime",
            "namespace-uri": "",
            "localname": localname,
            "range-value-positions": False,
            "invalid-values": "reject",
        }
        for localname in ("systemStart", "systemEnd", "validStart", "validEnd")
    ]
    ml.manage.databases.put_properties(
        database,
        {
            "range-element-index": [
                {
                    "scalar-type": "int",
                    "namespace-uri": "",
                    "localname": "price",
                    "range-value-positions": False,
                    "invalid-values": "reject",
                },
                *temporal_indexes,
            ],
            "path-namespace": [
                {"prefix": "r", "namespace-uri": "https://example.com/example/reports"},
            ],
            "range-path-index": [
                {
                    "scalar-type": "int",
                    "path-expression": "/r:report/r:price",
                    "range-value-positions": False,
                    "invalid-values": "reject",
                },
            ],
            "field": [
                {
                    "field-name": "summary",
                    "field-path": [{"path": "/report/summary", "weight": 1.0}],
                },
            ],
            "range-field-index": [
                {
                    "scalar-type": "int",
                    "field-name": "summary",
                    "collation": "",
                    "range-value-positions": False,
                    "invalid-values": "reject",
                },
            ],
            "geospatial-region-path-index": [
                {
                    "path-expression": "/report/area",
                    "coordinate-system": "wgs84",
                    "geohash-precision": 6,
                    "invalid-values": "reject",
                },
            ],
        },
    ).raise_for_status()


def _create_temporal_axes(ml: MLClient, database: str):
    (
        "Create the system and valid axes and an LSQT-enabled te"
        "mporal collection."
    )
    ml.eval.xquery(
        render_test_resource(__file__, "create-temporal-axes.xqy"), database=database,
    )
    ml.eval.xquery(
        render_test_resource(__file__, "create-temporal-axes-2.xqy"), database=database,
    )
    ml.eval.xquery(
        render_test_resource(__file__, "create-temporal-axes-3.xqy"), database=database,
    )


class TestStructuredComponentSerialization:
    @pytest.fixture(scope="class")
    @staticmethod
    def ml_client():
        with MLClient(port=int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))) as ml:
            yield ml

    def test_attribute(self, ml_client):
        query = Attribute("status", "https://example.com/example")
        self._assert_native_serialization(ml_client, query)

    def test_box(self, ml_client):
        query = Box(5, 15, 25, 35)
        self._assert_native_serialization(ml_client, query)

    def test_circle(self, ml_client):
        query = Circle(3, Point(10, 20))
        self._assert_native_serialization(ml_client, query)

    def test_container_constraint_query(self, ml_client):
        query = ContainerConstraintQuery("section", TrueQuery())
        self._assert_native_serialization(ml_client, query)

    def test_container_query(self, ml_client):
        query = ContainerQuery(
            Element("section", "https://example.com/example"),
            TermQuery("blue"),
            fragment_scope="properties",
        )
        self._assert_native_serialization(ml_client, query)

    def test_element(self, ml_client):
        query = Element("label", "https://example.com/example")
        self._assert_native_serialization(ml_client, query)

    def test_element_constraint_query(self, ml_client):
        query = ElementConstraintQuery("section", TrueQuery())
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
            "location", Point(10, 20), operator="intersects", weight=2,
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

    def test_lsqt_query(self, ml_client):
        query = LsqtQuery(
            "reports",
            timestamp="2024-01-01T00:00:00Z",
            options=["cached-incremental"],
            weight=2,
        )
        self._assert_native_serialization(ml_client, query)

    def test_operator_state(self, ml_client):
        query = OperatorState("sort", "relevance")
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

    def test_qtext_query(self, ml_client):
        query = QtextQuery("blue AND green")
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
            collation="https://example.com/example",
            options=["cached"],
            weight=2,
            fragment_scope="documents",
            attribute=Attribute("amount"),
        )
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
