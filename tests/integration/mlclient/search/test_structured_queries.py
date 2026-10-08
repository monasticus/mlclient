"""Verify structured-query XML against native MarkLogic query constructors."""

from __future__ import annotations

import os
import json
from uuid import uuid4
from xml.etree import ElementTree

import pytest

from mlclient import MLClient
from mlclient.http import HTTPConfig
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
    StructuredQuery,
    TermQuery,
    TrueQuery,
    ValueConstraintQuery,
    ValueQuery,
    WordConstraintQuery,
    WordQuery,
)

pytestmark = pytest.mark.ml_access


class TestStructuredQueries:
    @pytest.fixture(scope="class")
    @staticmethod
    def ml_database():
        port = int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))
        manage_port = int(os.environ.get("MLCLIENT_CTS_MANAGE_PORT", "8002"))
        name = f"mlclient-structured-test-{uuid4().hex}"
        # Temporal axes live in the schema database, so the test database gets
        # its own one rather than writing them into the shared Schemas.
        schemas = f"{name}-schemas"
        with MLClient(
            port=port,
            manage_config=HTTPConfig.resolve(port=manage_port),
        ) as ml:
            host = ml.eval.xquery("xdmp:host-name(xdmp:host())")
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
                    yield ml, name
                finally:
                    ml.manage.databases.delete(
                        name,
                        forest_delete="data",
                    ).raise_for_status()
            finally:
                ml.manage.databases.delete(
                    schemas,
                    forest_delete="data",
                ).raise_for_status()

    def test_and_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True),
            'cts:and-query((cts:word-query("blue"), cts:word-query("green")), '
            '"ordered")',
        )

    def test_and_not_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            AndNotQuery(TermQuery("blue"), TermQuery("green")),
            'cts:and-not-query(cts:word-query("blue"), cts:word-query("green"))',
        )

    def test_boost_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            BoostQuery(TermQuery("blue"), TermQuery("green", weight=2)),
            'cts:boost-query(cts:word-query("blue"), cts:word-query("green", (), 2))',
        )

    def test_collection_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            CollectionQuery(["reports", "notes"]),
            'cts:collection-query(("reports", "notes"))',
        )

    def test_container_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ContainerQuery(Element("section", "urn:example"), TermQuery("blue")),
            'cts:element-query(fn:QName("urn:example", "section"), '
            'cts:word-query("blue"))',
        )

    def test_directory_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            DirectoryQuery(["/reports/", "/notes/"], infinite=False),
            'cts:directory-query(("/reports/", "/notes/"), "1")',
        )

    def test_document_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            DocumentQuery(["/reports/first.xml", "/reports/second.json"]),
            'cts:document-query(("/reports/first.xml", "/reports/second.json"))',
        )

    def test_document_fragment_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            DocumentFragmentQuery(TermQuery("blue")),
            'cts:document-fragment-query(cts:word-query("blue"))',
        )

    def test_false_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            FalseQuery(),
            "cts:false-query()",
        )

    def test_locks_fragment_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            LocksFragmentQuery(TermQuery("blue")),
            'cts:locks-fragment-query(cts:word-query("blue"))',
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
            'cts:near-query((cts:word-query("blue"), cts:word-query("green")), '
            '3, "minimum-distance=1", 2)',
        )

    def test_not_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            NotQuery(TermQuery("blue")),
            'cts:not-query(cts:word-query("blue"))',
        )

    def test_not_in_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            NotInQuery(TermQuery("blue"), TermQuery("green")),
            'cts:not-in-query(cts:word-query("blue"), cts:word-query("green"))',
        )

    def test_or_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            OrQuery([TermQuery("blue"), TermQuery("green")]),
            'cts:or-query((cts:word-query("blue"), cts:word-query("green")))',
        )

    def test_properties_fragment_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PropertiesFragmentQuery(TermQuery("blue")),
            'cts:properties-fragment-query(cts:word-query("blue"))',
        )

    def test_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            Query([TermQuery("blue"), CollectionQuery("reports")]),
            'cts:and-query((cts:word-query("blue"), cts:collection-query("reports")))',
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
            'cts:element-range-query(xs:QName("price"), "=", '
            '(xs:int(3), xs:int(4)), ("cached"), 2)',
        )

    def test_term_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            TermQuery(
                ["blue", "green"],
                weight=2,
                options=["case-sensitive", "unstemmed"],
            ),
            'cts:word-query(("blue", "green"), ("case-sensitive", "unstemmed"), 2)',
        )

    def test_true_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            TrueQuery(),
            "cts:true-query()",
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
            'cts:json-property-value-query("active", fn:true(), "exact", 2)',
        )

    def test_value_query_number(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(JsonProperty("count"), 7, node_type="number"),
            'cts:json-property-value-query("count", xs:double(7))',
        )

    def test_value_query_null(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(JsonProperty("count"), "", node_type="null"),
            'cts:json-property-value-query("count", null-node {})',
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
            "cts:element-attribute-word-query("
            '(xs:QName("title"), xs:QName("label")), '
            '(xs:QName("name"), xs:QName("alt")), '
            '("blue", "green"), "case-sensitive", 2)',
        )

    def test_path_range_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(
                PathIndex("/r:report/r:price", {"r": "urn:example:reports"}),
                3,
                operator="GE",
                index_type="xs:int",
            ),
            'cts:path-range-query("/r:report/r:price", ">=", xs:int(3))',
        )

    def test_collection_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            CollectionConstraintQuery("category", ["blue", "green"]),
            'cts:collection-query(("reports/blue", "reports/green"))',
            options=(
                '<constraint name="category">'
                '<collection prefix="reports/"/></constraint>'
            ),
        )

    def test_container_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ContainerConstraintQuery("section", TermQuery("blue")),
            'cts:element-query(xs:QName("section"), cts:word-query("blue"))',
            options=(
                '<constraint name="section"><container>'
                '<element name="section" ns=""/></container></constraint>'
            ),
        )

    def test_element_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ElementConstraintQuery("section", TermQuery("blue")),
            'cts:element-query(xs:QName("section"), cts:word-query("blue"))',
            options=(
                '<constraint name="section">'
                '<element-query name="section" ns=""/></constraint>'
            ),
        )

    def test_properties_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PropertiesConstraintQuery("metadata", TermQuery("blue")),
            'cts:properties-fragment-query(cts:word-query("blue"))',
            options='<constraint name="metadata"><properties/></constraint>',
        )

    def test_range_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeConstraintQuery("price", 3, operator="GE", options=["cached"]),
            'cts:element-range-query(xs:QName("price"), ">=", xs:int(3), "cached")',
            options=(
                '<constraint name="price"><range type="xs:int" facet="false">'
                '<element name="price" ns=""/></range></constraint>'
            ),
        )

    def test_word_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordConstraintQuery("title", ["blue", "green"], weight=2),
            'cts:element-word-query(xs:QName("title"), ("blue", "green"), (), 2)',
            options=(
                '<constraint name="title"><word>'
                '<element name="title" ns=""/></word></constraint>'
            ),
        )

    def test_value_text_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("status", ["blue", "green"], weight=2),
            'cts:element-value-query(xs:QName("status"), ("blue", "green"), (), 2)',
            options=(
                '<constraint name="status"><value>'
                '<element name="status" ns=""/></value></constraint>'
            ),
        )

    def test_value_boolean_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("active", False),
            'cts:json-property-value-query("active", fn:false())',
            options=(
                '<constraint name="active"><value type="boolean">'
                "<json-property>active</json-property></value></constraint>"
            ),
        )

    def test_value_number_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("count", 7),
            'cts:json-property-value-query("count", xs:double(7))',
            options=(
                '<constraint name="count"><value type="number">'
                "<json-property>count</json-property></value></constraint>"
            ),
        )

    def test_value_null_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueConstraintQuery("count"),
            'cts:json-property-value-query("count", null-node {})',
            options=(
                '<constraint name="count"><value type="null">'
                "<json-property>count</json-property></value></constraint>"
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
            'cts:or-query((cts:element-word-query(xs:QName("title"), "blue"), '
            'cts:element-word-query(xs:QName("label"), "blue")))',
            options=(
                '<constraint name="title"><word>'
                '<element name="title" ns=""/></word></constraint>'
                '<constraint name="label"><word>'
                '<element name="label" ns=""/></word></constraint>'
            ),
        )

    def test_custom_constraint_query(self, ml_database):
        ml, database = ml_database
        module = (
            'xquery version "1.0-ml"; '
            'module namespace custom="urn:example:structured-custom"; '
            'declare namespace search="http://marklogic.com/appservices/search"; '
            "declare function custom:parse($query as element(), "
            "$options as element(search:options)) as cts:query { "
            "cts:word-query($query/search:text/string()) };"
        )
        ml.eval.xquery(
            "declare variable $module external; "
            'xdmp:document-insert("/structured-custom.xqy", text {$module})',
            variables={"module": module},
            database=database,
        )
        self._assert_native_query(
            ml_database,
            CustomConstraintQuery("custom", ["blue", "green"]),
            'cts:word-query(("blue", "green"))',
            options=(
                '<constraint name="custom"><custom facet="false">'
                '<parse apply="parse" ns="urn:example:structured-custom" '
                'at="/structured-custom.xqy"/></custom></constraint>'
            ),
            modules_database=True,
        )

    def test_geo_element_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoElementQuery(
                Element("location"),
                Point(10, 20),
                options=["units=miles"],
                weight=2,
            ),
            'cts:element-geospatial-query(xs:QName("location"), '
            'cts:point(10, 20), "units=miles", 2)',
        )

    def test_geo_child_element_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoElementQuery(
                Element("location"),
                Point(10, 20),
                parent=Element("place"),
            ),
            'cts:element-child-geospatial-query(xs:QName("place"), '
            'xs:QName("location"), cts:point(10, 20))',
        )

    def test_geo_element_pair_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoElementPairQuery(
                Element("place"),
                Element("lat"),
                Element("lon"),
                Box(1, 2, 3, 4),
            ),
            'cts:element-pair-geospatial-query(xs:QName("place"), '
            'xs:QName("lat"), xs:QName("lon"), cts:box(1, 2, 3, 4))',
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
            'cts:element-attribute-pair-geospatial-query(xs:QName("place"), '
            'xs:QName("lat"), xs:QName("lon"), cts:circle(5, cts:point(10, 20)))',
        )

    def test_geo_json_property_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoJsonPropertyQuery(
                JsonProperty("location"),
                Polygon([Point(1, 2), Point(3, 4), Point(5, 6), Point(1, 2)]),
                parent=JsonProperty("place"),
            ),
            'cts:json-property-child-geospatial-query("place", "location", '
            "cts:polygon((cts:point(1, 2), cts:point(3, 4), cts:point(5, 6), "
            "cts:point(1, 2))))",
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
            'cts:json-property-pair-geospatial-query("place", "lat", "lon", '
            "cts:point(10, 20))",
        )

    def test_period_compare_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PeriodCompareQuery("system", "aln_equals", "valid"),
            'cts:period-compare-query("system", "aln_equals", "valid")',
        )

    def test_period_range_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            PeriodRangeQuery(
                "valid",
                "aln_contains",
                Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
            ),
            'cts:period-range-query("valid", "aln_contains", '
            'cts:period(xs:dateTime("2026-01-01T00:00:00Z"), '
            'xs:dateTime("2026-02-01T00:00:00Z")))',
        )

    def test_lsqt_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            LsqtQuery("reports-temporal", timestamp="1600-01-01T00:00:00Z", weight=2),
            'cts:lsqt-query("reports-temporal", '
            'xs:dateTime("1600-01-01T00:00:00Z"), (), 2)',
        )

    def test_word_query_on_a_field(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordQuery(Field("summary"), "blue"),
            'cts:field-word-query("summary", "blue", "lang=en")',
        )

    def test_word_query_on_a_json_property(self, ml_database):
        self._assert_native_query(
            ml_database,
            WordQuery(JsonProperty("title"), "blue"),
            'cts:json-property-word-query("title", "blue", "lang=en")',
        )

    def test_value_query_on_a_json_property(self, ml_database):
        self._assert_native_query(
            ml_database,
            ValueQuery(JsonProperty("title"), "blue"),
            'cts:json-property-value-query("title", "blue", "lang=en")',
        )

    def test_range_query_on_a_field(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(Field("summary"), 3, operator="GE", index_type="xs:int"),
            'cts:field-range-query("summary", ">=", xs:int(3))',
        )

    def test_range_query_on_a_json_property(self, ml_database):
        self._assert_native_query(
            ml_database,
            RangeQuery(JsonProperty("price"), 3, operator="GE", index_type="xs:int"),
            'cts:json-property-range-query("price", ">=", xs:int(3))',
        )

    def test_geo_path_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoPathQuery(PathIndex("/report/location"), Point(10, 20), weight=2),
            'cts:path-geospatial-query("/report/location", cts:point(10, 20), (), 2)',
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
            'cts:geospatial-region-query(cts:geospatial-region-path-reference('
            '"/report/area", "coordinate-system=wgs84"), "intersects", '
            "cts:box(1, 2, 3, 4))",
        )

    def test_geospatial_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeospatialConstraintQuery("loc", Point(10, 20)),
            'cts:element-geospatial-query(xs:QName("location"), cts:point(10, 20))',
            options=(
                '<constraint name="loc"><geo-elem>'
                '<element name="location" ns=""/></geo-elem></constraint>'
            ),
        )

    def test_geo_region_constraint_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            GeoRegionConstraintQuery("area", Box(1, 2, 3, 4), operator="intersects"),
            'cts:geospatial-region-query(cts:geospatial-region-path-reference('
            '"/report/area", "coordinate-system=wgs84"), "intersects", '
            "cts:box(1, 2, 3, 4))",
            options=(
                '<constraint name="area"><geo-region-path coord="wgs84">'
                "<path-index>/report/area</path-index></geo-region-path>"
                "</constraint>"
            ),
        )

    def test_qtext_query(self, ml_database):
        self._assert_native_query(
            ml_database,
            QtextQuery("blue green"),
            'cts:and-query((cts:word-query("blue", "lang=en"), '
            'cts:word-query("green", "lang=en")))',
        )

    def test_operator_state(self, ml_database):
        ml, database = ml_database
        query = Query([TrueQuery(), OperatorState("nresults", "few")])
        result = ml.eval.xquery(
            'import module namespace search="http://marklogic.com/appservices/search" '
            'at "/MarkLogic/appservices/search/search.xqy"; '
            "import module namespace csu="
            '"http://marklogic.com/rest-api/config-query-util" '
            'at "/MarkLogic/rest-api/lib/config-query-util.xqy"; '
            "declare variable $query external; "
            "declare variable $query_json external; "
            "let $options := <search:options>"
            "<search:page-length>10</search:page-length>"
            '<search:operator name="nresults"><search:state name="few">'
            "<search:page-length>2</search:page-length>"
            "</search:state></search:operator></search:options> "
            "for $structured in (xdmp:unquote($query)/*, "
            "csu:json-to-xml(xdmp:unquote($query_json))) "
            "return xs:int(search:resolve($structured, $options)/@page-length)",
            variables={
                "query": ElementTree.tostring(
                    query.serialize("xml"),
                    encoding="unicode",
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
        ml, database = ml_database
        wrapper = query if isinstance(query, Query) else Query(query)
        xml = ElementTree.tostring(wrapper.serialize("xml"), encoding="unicode")
        code = (
            'import module namespace search="http://marklogic.com/appservices/search" '
            'at "/MarkLogic/appservices/search/search.xqy"; '
            "import module namespace csu="
            '"http://marklogic.com/rest-api/config-query-util" '
            'at "/MarkLogic/rest-api/lib/config-query-util.xqy"; '
            'declare namespace r="urn:example:reports"; '
            "declare variable $query external; "
            "declare variable $query_json external; "
            "declare variable $options external; "
            "let $actual := search:resolve("
            "xdmp:unquote($query)/*, "
            "<search:options>"
            "<search:return-results>false</search:return-results>"
            "<search:return-facets>false</search:return-facets>"
            "<search:return-query>true</search:return-query>"
            "{xdmp:unquote($options)/*/*}"
            "</search:options>)/search:query/* "
            "let $actual_json := search:resolve("
            "csu:json-to-xml(xdmp:unquote($query_json)), "
            "<search:options>"
            "<search:return-results>false</search:return-results>"
            "<search:return-facets>false</search:return-facets>"
            "<search:return-query>true</search:return-query>"
            "{xdmp:unquote($options)/*/*}"
            "</search:options>)/search:query/* "
            f"let $expected := <container>{{{native}}}</container>/* "
            "return if (deep-equal($actual, $expected) and "
            "deep-equal($actual_json, $expected)) then fn:true() "
            "else (<actual>{$actual}</actual>, "
            "<actual-json>{$actual_json}</actual-json>, "
            "<expected>{$expected}</expected>)"
        )
        variables = {
            "query": xml,
            "query_json": json.dumps(wrapper.serialize()),
            "options": (
                '<options xmlns="http://marklogic.com/appservices/search">'
                f"{options}</options>"
            ),
        }
        if modules_database:
            variables["code"] = code
            code = (
                "declare variable $code external; "
                "declare variable $query external; "
                "declare variable $query_json external; "
                "declare variable $options external; "
                "xdmp:eval($code, "
                '(xs:QName("query"), $query, xs:QName("query_json"), $query_json, '
                'xs:QName("options"), $options), '
                '<options xmlns="xdmp:eval">'
                "<database>{xdmp:database()}</database>"
                "<modules>{xdmp:database()}</modules><root>/</root>"
                "</options>)"
            )
        result = ml.eval.xquery(
            code,
            variables=variables,
            database=database,
        )
        assert result is True, [
            ElementTree.tostring(item, encoding="unicode") for item in result
        ]


def _configure_indexes(ml: MLClient, database: str):
    """Add the range indexes the native comparisons and temporal axes need."""
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
                {
                    "prefix": "r",
                    "namespace-uri": "urn:example:reports",
                },
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
    """Create the system and valid axes and an LSQT-enabled temporal collection."""
    ml.eval.xquery(
        'import module namespace temporal="http://marklogic.com/xdmp/temporal" '
        'at "/MarkLogic/temporal.xqy"; '
        'temporal:axis-create("system", '
        'cts:element-reference(xs:QName("systemStart")), '
        'cts:element-reference(xs:QName("systemEnd"))), '
        'temporal:axis-create("valid", '
        'cts:element-reference(xs:QName("validStart")), '
        'cts:element-reference(xs:QName("validEnd")))',
        database=database,
    )
    ml.eval.xquery(
        'import module namespace temporal="http://marklogic.com/xdmp/temporal" '
        'at "/MarkLogic/temporal.xqy"; '
        'temporal:collection-create("reports-temporal", "system", "valid")',
        database=database,
    )
    # A new temporal collection is visible only after its own transaction.
    ml.eval.xquery(
        'import module namespace temporal="http://marklogic.com/xdmp/temporal" '
        'at "/MarkLogic/temporal.xqy"; '
        'temporal:set-use-lsqt("reports-temporal", fn:true())',
        database=database,
    )
