"""The structured builder constructs query objects with the supplied arguments."""

import pytest

from mlclient.search import structured
from mlclient.search.structured import (
    AndQuery,
    CollectionQuery,
    Element,
    NearQuery,
    NotQuery,
    OrQuery,
    Query,
    RangeQuery,
    StructuredQueryBuilder,
    TermQuery,
    sq,
)


def test_builder_composes_range_and_term():
    query = sq.query(
        sq.and_(
            sq.range(sq.element("price"), 20, operator="GE", index_type="xs:int"),
            sq.term("blue"),
        ),
    )
    assert query == Query(
        [
            AndQuery(
                [
                    RangeQuery(
                        Element("price"),
                        20,
                        operator="GE",
                        index_type="xs:int",
                    ),
                    TermQuery("blue"),
                ],
            ),
        ],
    )


@pytest.mark.parametrize("ordered", [None, True, False])
def test_builder_and_preserves_order(ordered):
    builder = StructuredQueryBuilder()
    blue = builder.term("blue")
    green = builder.term("green")
    assert builder.and_(blue, green, ordered=ordered) == AndQuery(
        [TermQuery("blue"), TermQuery("green")],
        ordered=ordered,
    )


def test_builder_or_composes_queries():
    assert sq.or_(sq.collection("reports"), sq.not_(sq.term("blue"))) == OrQuery(
        [CollectionQuery("reports"), NotQuery(TermQuery("blue"))],
    )


def test_builder_near_preserves_optional_arguments():
    assert sq.near(
        sq.term("blue"),
        sq.term("green"),
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    ) == NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )


def test_builder_near_without_options():
    assert sq.near(sq.term("blue")) == NearQuery([TermQuery("blue")])


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (sq.query, Query([])),
        (sq.and_, AndQuery([])),
        (sq.or_, OrQuery([])),
        (sq.near, NearQuery([])),
    ],
    ids=["query", "and", "or", "near"],
)
def test_builder_empty_composition(build, expected):
    assert build() == expected


def test_builder_near_rejects_invalid_distance():
    with pytest.raises(TypeError) as error:
        sq.near(sq.term("blue"), distance=1.5)
    assert str(error.value) == "NearQuery.distance must be an integer, got float"


@pytest.mark.parametrize(
    "builder",
    [sq, StructuredQueryBuilder()],
    ids=["sq", "instance"],
)
@pytest.mark.parametrize(
    ("build", "expected"),
    [
        pytest.param(
            lambda b: b.and_not(TermQuery("blue"), TermQuery("green")),
            structured.AndNotQuery(TermQuery("blue"), TermQuery("green")),
            id="and_not",
        ),
        pytest.param(
            lambda b: b.attribute("status", ns="https://example.com/items"),
            structured.Attribute("status", ns="https://example.com/items"),
            id="attribute",
        ),
        pytest.param(
            lambda b: b.boost(TermQuery("blue"), TermQuery("green")),
            structured.BoostQuery(TermQuery("blue"), TermQuery("green")),
            id="boost",
        ),
        pytest.param(lambda b: b.box(1, 2, 3, 4), structured.Box(1, 2, 3, 4), id="box"),
        pytest.param(
            lambda b: b.circle(5, structured.Point(1, 2)),
            structured.Circle(5, structured.Point(1, 2)),
            id="circle",
        ),
        pytest.param(
            lambda b: b.collection_constraint("category", ["reports", "notes"]),
            structured.CollectionConstraintQuery("category", ["reports", "notes"]),
            id="collection_constraint",
        ),
        pytest.param(
            lambda b: b.collection(["reports", "notes"]),
            CollectionQuery(["reports", "notes"]),
            id="collection",
        ),
        pytest.param(
            lambda b: b.container_constraint("section", TermQuery("blue")),
            structured.ContainerConstraintQuery("section", TermQuery("blue")),
            id="container_constraint",
        ),
        pytest.param(
            lambda b: b.container(
                Element("section"),
                TermQuery("blue"),
                fragment_scope="properties",
            ),
            structured.ContainerQuery(
                Element("section"),
                TermQuery("blue"),
                fragment_scope="properties",
            ),
            id="container",
        ),
        pytest.param(
            lambda b: b.custom_constraint("custom", ["blue", "green"]),
            structured.CustomConstraintQuery("custom", ["blue", "green"]),
            id="custom_constraint",
        ),
        pytest.param(
            lambda b: b.directory(["/reports/", "/notes/"], infinite=True),
            structured.DirectoryQuery(["/reports/", "/notes/"], infinite=True),
            id="directory",
        ),
        pytest.param(
            lambda b: b.document_fragment(TermQuery("blue")),
            structured.DocumentFragmentQuery(TermQuery("blue")),
            id="document_fragment",
        ),
        pytest.param(
            lambda b: b.document(["/a.xml", "/b.xml"]),
            structured.DocumentQuery(["/a.xml", "/b.xml"]),
            id="document",
        ),
        pytest.param(
            lambda b: b.element("title", ns="https://example.com/items"),
            Element("title", ns="https://example.com/items"),
            id="element",
        ),
        pytest.param(
            lambda b: b.element_constraint("title", TermQuery("blue")),
            structured.ElementConstraintQuery("title", TermQuery("blue")),
            id="element_constraint",
        ),
        pytest.param(lambda b: b.false(), structured.FalseQuery(), id="false"),
        pytest.param(
            lambda b: b.field("title", collation="http://marklogic.com/collation/"),
            structured.Field("title", collation="http://marklogic.com/collation/"),
            id="field",
        ),
        pytest.param(
            lambda b: b.geo_attribute_pair(
                Element("location"),
                structured.Attribute("lat"),
                structured.Attribute("lon"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoAttributePairQuery(
                Element("location"),
                structured.Attribute("lat"),
                structured.Attribute("lon"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_attribute_pair",
        ),
        pytest.param(
            lambda b: b.geo_element_pair(
                Element("location"),
                Element("lat"),
                Element("lon"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoElementPairQuery(
                Element("location"),
                Element("lat"),
                Element("lon"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_element_pair",
        ),
        pytest.param(
            lambda b: b.geo_element(
                Element("point"),
                structured.Point(1, 2),
                parent=Element("location"),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoElementQuery(
                Element("point"),
                structured.Point(1, 2),
                parent=Element("location"),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_element",
        ),
        pytest.param(
            lambda b: b.geo_json_property_pair(
                structured.JsonProperty("location"),
                structured.JsonProperty("lat"),
                structured.JsonProperty("lon"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoJsonPropertyPairQuery(
                structured.JsonProperty("location"),
                structured.JsonProperty("lat"),
                structured.JsonProperty("lon"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_json_property_pair",
        ),
        pytest.param(
            lambda b: b.geo_json_property(
                structured.JsonProperty("point"),
                structured.Point(1, 2),
                parent=structured.JsonProperty("location"),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoJsonPropertyQuery(
                structured.JsonProperty("point"),
                structured.Point(1, 2),
                parent=structured.JsonProperty("location"),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_json_property",
        ),
        pytest.param(
            lambda b: b.geo_path(
                structured.PathIndex("/location"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoPathQuery(
                structured.PathIndex("/location"),
                structured.Point(1, 2),
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_path",
        ),
        pytest.param(
            lambda b: b.geo_region_constraint(
                "location",
                structured.Point(1, 2),
                operator="intersects",
                weight=2,
            ),
            structured.GeoRegionConstraintQuery(
                "location",
                structured.Point(1, 2),
                operator="intersects",
                weight=2,
            ),
            id="geo_region_constraint",
        ),
        pytest.param(
            lambda b: b.geo_region_path(
                structured.PathIndex("/location"),
                structured.Point(1, 2),
                operator="intersects",
                coord="wgs84",
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            structured.GeoRegionPathQuery(
                structured.PathIndex("/location"),
                structured.Point(1, 2),
                operator="intersects",
                coord="wgs84",
                options="ordered",
                weight=2,
                fragment_scope="properties",
            ),
            id="geo_region_path",
        ),
        pytest.param(
            lambda b: b.geospatial_constraint(
                "location",
                structured.Point(1, 2),
                text="blue",
            ),
            structured.GeospatialConstraintQuery(
                "location",
                structured.Point(1, 2),
                text="blue",
            ),
            id="geospatial_constraint",
        ),
        pytest.param(
            lambda b: b.json_property("title"),
            structured.JsonProperty("title"),
            id="json_property",
        ),
        pytest.param(
            lambda b: b.locks_fragment(TermQuery("blue")),
            structured.LocksFragmentQuery(TermQuery("blue")),
            id="locks_fragment",
        ),
        pytest.param(
            lambda b: b.lsqt(
                "events",
                timestamp="2026-01-01T00:00:00Z",
                options="cached",
                weight=2,
            ),
            structured.LsqtQuery(
                "events",
                timestamp="2026-01-01T00:00:00Z",
                options="cached",
                weight=2,
            ),
            id="lsqt",
        ),
        pytest.param(
            lambda b: b.not_in(TermQuery("blue"), TermQuery("green")),
            structured.NotInQuery(TermQuery("blue"), TermQuery("green")),
            id="not_in",
        ),
        pytest.param(
            lambda b: b.not_(TermQuery("blue")),
            NotQuery(TermQuery("blue")),
            id="not_",
        ),
        pytest.param(
            lambda b: b.operator_state("sort", "ascending"),
            structured.OperatorState("sort", "ascending"),
            id="operator_state",
        ),
        pytest.param(
            lambda b: b.path_index(
                "/i:item",
                namespaces={"i": "https://example.com/items"},
            ),
            structured.PathIndex(
                "/i:item",
                namespaces={"i": "https://example.com/items"},
            ),
            id="path_index",
        ),
        pytest.param(
            lambda b: b.period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
            structured.Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
            id="period",
        ),
        pytest.param(
            lambda b: b.period_compare(
                "valid",
                "aln_before",
                "system",
                options="cached",
            ),
            structured.PeriodCompareQuery(
                "valid",
                "aln_before",
                "system",
                options="cached",
            ),
            id="period_compare",
        ),
        pytest.param(
            lambda b: b.period_range(
                "valid",
                "aln_before",
                structured.Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
                options="cached",
                weight=2,
            ),
            structured.PeriodRangeQuery(
                "valid",
                "aln_before",
                structured.Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
                options="cached",
                weight=2,
            ),
            id="period_range",
        ),
        pytest.param(lambda b: b.point(1, 2), structured.Point(1, 2), id="point"),
        pytest.param(
            lambda b: b.polygon(
                [
                    structured.Point(1, 2),
                    structured.Point(3, 4),
                    structured.Point(5, 6),
                ],
            ),
            structured.Polygon(
                [
                    structured.Point(1, 2),
                    structured.Point(3, 4),
                    structured.Point(5, 6),
                ],
            ),
            id="polygon",
        ),
        pytest.param(
            lambda b: b.properties_constraint("category", TermQuery("blue")),
            structured.PropertiesConstraintQuery("category", TermQuery("blue")),
            id="properties_constraint",
        ),
        pytest.param(
            lambda b: b.properties_fragment(TermQuery("blue")),
            structured.PropertiesFragmentQuery(TermQuery("blue")),
            id="properties_fragment",
        ),
        pytest.param(
            lambda b: b.qtext("blue AND green"),
            structured.QtextQuery("blue AND green"),
            id="qtext",
        ),
        pytest.param(
            lambda b: b.range_constraint("price", 20, operator="GE", options="cached"),
            structured.RangeConstraintQuery(
                "price",
                20,
                operator="GE",
                options="cached",
            ),
            id="range_constraint",
        ),
        pytest.param(
            lambda b: b.range(
                Element("price"),
                20,
                operator="GE",
                index_type="xs:int",
                collation="http://marklogic.com/collation/",
                attribute=structured.Attribute("amount"),
                options="cached",
                weight=2,
                fragment_scope="properties",
            ),
            RangeQuery(
                Element("price"),
                20,
                operator="GE",
                index_type="xs:int",
                collation="http://marklogic.com/collation/",
                attribute=structured.Attribute("amount"),
                options="cached",
                weight=2,
                fragment_scope="properties",
            ),
            id="range",
        ),
        pytest.param(
            lambda b: b.term(["blue", "green"], weight=2, options="exact"),
            TermQuery(["blue", "green"], weight=2, options="exact"),
            id="term",
        ),
        pytest.param(lambda b: b.true(), structured.TrueQuery(), id="true"),
        pytest.param(
            lambda b: b.value_constraint("title", ["blue", "green"], weight=2),
            structured.ValueConstraintQuery("title", ["blue", "green"], weight=2),
            id="value_constraint",
        ),
        pytest.param(
            lambda b: b.value(
                Element("title"),
                "blue",
                attribute=structured.Attribute("label"),
                options="exact",
                weight=2,
                fragment_scope="properties",
                node_type="string",
            ),
            structured.ValueQuery(
                Element("title"),
                "blue",
                attribute=structured.Attribute("label"),
                options="exact",
                weight=2,
                fragment_scope="properties",
                node_type="string",
            ),
            id="value",
        ),
        pytest.param(
            lambda b: b.word_constraint("title", ["blue", "green"], weight=2),
            structured.WordConstraintQuery("title", ["blue", "green"], weight=2),
            id="word_constraint",
        ),
        pytest.param(
            lambda b: b.word(
                Element("title"),
                ["blue", "green"],
                attribute=structured.Attribute("label"),
                options="exact",
                weight=2,
                fragment_scope="properties",
            ),
            structured.WordQuery(
                Element("title"),
                ["blue", "green"],
                attribute=structured.Attribute("label"),
                options="exact",
                weight=2,
                fragment_scope="properties",
            ),
            id="word",
        ),
    ],
)
def test_builder_factories_construct_expected_objects(builder, build, expected):
    actual = build(builder)
    assert type(actual) is type(expected)
    assert actual == expected
