from __future__ import annotations

from tests.utils.resources import render_test_resource

from datetime import date
from decimal import Decimal
from xml.etree.ElementTree import Element as XmlElement, tostring
from uuid import uuid4

import pytest

from mlclient import _constants as constants
from mlclient.calls import ApiCall
from mlclient.exceptions import MarkLogicError
from mlclient.xquery import cts, fn
from mlclient.models import JSONDocument, TupleHit, ValueHit, XMLDocument
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import (
    Attribute,
    ContainerConstraintQuery,
    Element,
    Field,
    JsonProperty,
    PathIndex,
    SEARCH_NS_URI,
    TermQuery,
    sq,
)

pytestmark = pytest.mark.ml_access

NS = "https://monasticus.com/mlclient/examples/cts-test"
URIS = ["/cts-test/a.xml", "/cts-test/b.xml", "/cts-test/c.json"]


class QueryOptionsPutCall(ApiCall):
    """Install persistent query options for a values scenario."""

    def __init__(self, name: str, body: dict):
        super().__init__(
            method=constants.METHOD_PUT,
            body=body,
            content_type=constants.HEADER_JSON,
        )
        self._name = name

    @property
    def endpoint(self):
        return f"/v1/config/query/{self._name}"


class QueryOptionsDeleteCall(ApiCall):
    """Remove persistent query options installed by a values scenario."""

    def __init__(self, name: str):
        super().__init__(method=constants.METHOD_DELETE)
        self._name = name

    @property
    def endpoint(self):
        return f"/v1/config/query/{self._name}"


class TransformCall(ApiCall):
    """Install or remove a uniquely named response transform."""

    def __init__(self, name: str, method: str, body: str | None = None):
        super().__init__(method=method, body=body, content_type="application/xquery")
        self._name = name

    @property
    def endpoint(self):
        return f"/v1/config/transforms/{self._name}"


@pytest.fixture(scope="class")
def response_transform(indexed_database):
    ml, _, _ = indexed_database
    name = f"mlclient-search-{uuid4().hex}"
    body = render_test_resource(__file__, "response-transform.xqy", name=name)
    ml.rest.call(TransformCall(name, "PUT", body)).raise_for_status()
    try:
        yield name
    finally:
        ml.rest.call(TransformCall(name, "DELETE")).raise_for_status()


@pytest.fixture(scope="class")
def values_options(indexed_database):
    ml, _, _ = indexed_database
    name = f"mlclient-values-{uuid4().hex}"
    options = {
        "options": {
            "values": [
                {
                    "name": "price",
                    "range": {
                        "type": "xs:decimal",
                        "element": {"ns": NS, "name": "price"},
                    },
                },
                {
                    "name": "day",
                    "range": {"type": "xs:date", "element": {"ns": NS, "name": "day"}},
                },
            ],
        },
    }
    ml.rest.call(QueryOptionsPutCall(name, options)).raise_for_status()
    try:
        yield name
    finally:
        ml.rest.call(QueryOptionsDeleteCall(name)).raise_for_status()


class TestSearchService:
    def test_json_property_values_options(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "label",
            Range(
                JsonProperty("label"),
                collation="http://marklogic.com/collation/",
            ),
        )

        result = ml.search(database=database, options=options).values("label")

        assert result == [ValueHit("gamma", frequency=1)]

    def test_json_property_options_as_native_xml(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "label",
            Range(
                JsonProperty("label"),
                collation="http://marklogic.com/collation/",
            ),
        )
        body = XmlElement(f"{{{SEARCH_NS_URI}}}search")
        body.append(options.to_xml())

        response = ml.rest.values.post(
            "label",
            tostring(body, encoding="unicode"),
            database=database,
            data_format="json",
            view="values",
        )

        response.raise_for_status()
        assert response.json()["values-response"]["distinct-value"] == [
            {"frequency": 1, "_value": "gamma"},
        ]

    def test_transformed_documents(self, indexed_database, response_transform):
        ml, database, _ = indexed_database

        result = ml.search(database=database).documents(
            cts.document_query("/cts-test/a.xml"),
            transform=response_transform,
            transform_params={"value": 0},
        )

        assert len(result) == 1
        assert result[0].uri == "/cts-test/a.xml"
        assert result[0].content.getroot().attrib == {
            "transformed": "0",
            "amount": "1.25",
            "quantity": "2",
            "lat": "10",
            "lon": "20",
        }

    def test_transformed_documents_with_inline_options(
        self,
        indexed_database,
        response_transform,
    ):
        ml, database, _ = indexed_database

        result = ml.search(database=database, options=SearchOptions()).documents(
            cts.document_query("/cts-test/a.xml"),
            transform=response_transform,
            transform_params={"value": 0},
        )

        assert len(result) == 1
        assert result[0].uri == "/cts-test/a.xml"
        assert result[0].content.getroot().attrib == {
            "transformed": "0",
            "amount": "1.25",
            "quantity": "2",
            "lat": "10",
            "lon": "20",
        }

    def test_field_values_options(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values("price", Range(Field("price"), "xs:decimal"))

        result = ml.search(database=database, options=options).values("price")

        assert result == [
            ValueHit(Decimal("1.25"), frequency=1),
            ValueHit(Decimal("2.5"), frequency=1),
        ]

    def test_path_values_options(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(PathIndex("/t:item/t:price", {"t": NS}), "xs:decimal"),
        )

        result = ml.search(database=database, options=options).values("price")

        assert result == [
            ValueHit(Decimal("1.25"), frequency=1),
            ValueHit(Decimal("2.5"), frequency=1),
        ]

    def test_attribute_values_options(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "amount",
            Range(Element("item", NS), "xs:decimal", attribute=Attribute("amount")),
        )

        result = ml.search(database=database, options=options).values("amount")

        assert result == [
            ValueHit(Decimal("1.25"), frequency=1),
            ValueHit(Decimal("2.5"), frequency=1),
        ]

    def test_options_as_native_xml(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )
        body = XmlElement(f"{{{SEARCH_NS_URI}}}search")
        body.append(options.to_xml())

        response = ml.rest.values.post(
            "price",
            tostring(body, encoding="unicode"),
            database=database,
            data_format="json",
            view="values",
        )

        response.raise_for_status()
        assert response.json()["values-response"]["distinct-value"] == [
            {"frequency": 1, "_value": "1.25"},
            {"frequency": 1, "_value": "2.5"},
        ]

    def test_zero_values_limit(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )

        assert (
            ml.search(database=database, options=options).values("price", limit=0) == []
        )

    def test_empty_aggregate(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )

        assert (
            ml.search(database=database, options=options).aggregate(
                "price",
                "avg",
                "zzz",
            )
            is None
        )

    def test_tuple_decimal_precision(self, indexed_database):
        ml, database, _ = indexed_database
        uri = "/options-test/precise.xml"
        doc = XMLDocument(
            f'<item xmlns="{NS}"><price>0.123456789123456789</price>'
            "<day>2026-01-01</day></item>",
            uri,
        )
        options = SearchOptions().tuples(
            "price-day",
            Range(Element("price", NS), "xs:decimal"),
            Range(Element("day", NS), "xs:date"),
        )
        try:
            ml.documents.write(doc, database=database)

            result = ml.search(database=database, options=options).tuples(
                "price-day",
                cts.document_query(uri),
            )

            assert result == [
                TupleHit(
                    (Decimal("0.123456789123456789"), date(2026, 1, 1)),
                    frequency=1,
                ),
            ]
        finally:
            ml.documents.delete(uri, database=database)

    def test_values_with_inline_options(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )

        values = ml.search(database=database, options=options).values(
            "price",
            direction="descending",
            frequency="fragment",
            limit=1,
        )

        assert values == [ValueHit(Decimal("2.5"), frequency=1)]

    def test_aggregate_of_decimal_values(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )

        result = ml.search(database=database, options=options).aggregate("price", "sum")

        assert result == Decimal("3.75")
        assert type(result) is Decimal

    def test_aggregate_count_has_integer_type(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().values(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )

        prices = ml.search(database=database, options=options)
        result = prices.aggregate("price", "count")

        assert result == 2
        assert type(result) is int

    def test_typed_co_occurrences(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().tuples(
            "price-day",
            Range(Element("price", NS), "xs:decimal"),
            Range(Element("day", NS), "xs:date"),
        )

        result = ml.search(database=database, options=options).tuples("price-day")

        assert result == [
            TupleHit((Decimal("1.25"), date(2026, 1, 1)), frequency=1),
            TupleHit((Decimal("2.5"), date(2026, 1, 2)), frequency=1),
        ]

    def test_report_with_facets_and_scores(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().range_constraint(
            "price",
            Range(Element("price", NS), "xs:decimal"),
        )

        scoped = ml.search(database=database, collection="cts-test", options=options)
        report = scoped.report("alpha OR beta")

        assert report.total == 2
        assert sorted(result["uri"] for result in report.results) == URIS[:2]
        assert all(result["score"] > 0 for result in report.results)
        assert report.facets["price"]["facetValues"] == [
            {"name": "1.25", "count": 1, "value": 1.25},
            {"name": "2.5", "count": 1, "value": 2.5},
        ]
        assert "total-time" in report.metrics
        assert report.effective_timestamp.isdigit()

    def test_uris_of_a_query_too_long_for_a_url(self, indexed_database):
        ml, database, _ = indexed_database
        missing = [f"/cts-test/missing-{i}.xml" for i in range(1000)]
        query = cts.document_query(missing + URIS)

        uris = ml.search(database=database).uris(query, pos=[1, 10])

        assert sorted(uris) == URIS

    def test_inline_page_length_applies_to_multi_document_reads(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        options = SearchOptions().control("page-length", 2)
        scoped = ml.search(database=database, collection="cts-test", options=options)

        assert len(scoped.uris()) == 2
        assert len(scoped.documents()) == 2
        assert scoped.report().page_length == 2

    def test_installed_page_length_does_not_apply_to_multi_document_reads(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        name = f"mlclient-page-{uuid4().hex}"
        options = {"options": {"page-length": 2}}
        ml.rest.call(QueryOptionsPutCall(name, options)).raise_for_status()
        try:
            scoped = ml.search(database=database, collection="cts-test", options=name)

            # MarkLogic ignores an options page-length in a multi-document read;
            # the service can apply only inline options it holds.
            assert len(scoped.uris()) == len(URIS)
            assert len(scoped.uris(pos=[1, 2])) == 2
        finally:
            ml.rest.call(QueryOptionsDeleteCall(name)).raise_for_status()

    def test_word_constraint_in_a_string_query(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().word_constraint("label", Element("label", NS))

        scoped = ml.search(database=database, collection="cts-test", options=options)

        assert scoped.uris("label:alpha") == ["/cts-test/a.xml"]

    def test_value_constraint_on_a_json_property(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().value_constraint("label", JsonProperty("label"))

        scoped = ml.search(database=database, collection="cts-test", options=options)

        assert scoped.uris("label:gamma") == ["/cts-test/c.json"]

    def test_word_constraint_on_an_attribute(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().word_constraint(
            "quantity",
            Element("item", NS),
            attribute=Attribute("quantity"),
        )

        scoped = ml.search(database=database, collection="cts-test", options=options)

        assert scoped.uris("quantity:4") == ["/cts-test/b.xml"]

    def test_value_constraint_on_an_attribute(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().value_constraint(
            "quantity",
            Element("item", NS),
            attribute=Attribute("quantity"),
        )

        scoped = ml.search(database=database, collection="cts-test", options=options)

        assert scoped.uris("quantity:2") == ["/cts-test/a.xml"]

    def test_value_constraint_matches_only_its_json_node_type(self, indexed_database):
        ml, database, _ = indexed_database
        as_boolean = SearchOptions().value_constraint(
            "active",
            JsonProperty("active"),
            node_type="boolean",
        )
        as_string = SearchOptions().value_constraint("active", JsonProperty("active"))

        def search(options):
            return ml.search(database=database, collection="cts-test", options=options)

        assert search(as_boolean).uris("active:true") == ["/cts-test/c.json"]
        assert search(as_string).uris("active:true") == []

    def test_collection_constraint_calculates_a_facet_by_default(
        self,
        indexed_database,
    ):
        ml, database, _ = indexed_database
        options = SearchOptions().collection_constraint("set", prefix="cts-")

        report = ml.search(database=database, options=options).report("set:test")

        assert "set" in report.facets

    def test_collection_constraint_with_prefix(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().collection_constraint("set", prefix="cts-")

        uris = ml.search(database=database, options=options).uris("set:test")

        assert sorted(uris) == URIS

    def test_container_constraint_query(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().container_constraint(
            "place",
            Element("location", NS),
        )
        query = ContainerConstraintQuery("place", TermQuery("20"))

        uris = ml.search(database=database, options=options).uris(query)

        assert uris == ["/cts-test/a.xml"]

    def test_constraint_options_are_valid_native_xml(self, indexed_database):
        ml, database, _ = indexed_database
        options = (
            SearchOptions()
            .range_constraint("price", Range(Element("price", NS), "xs:decimal"))
            .word_constraint("label", Element("label", NS), options="unstemmed")
            .value_constraint("name", JsonProperty("label"))
            .collection_constraint("set", prefix="cts-")
            .container_constraint("place", Element("location", NS))
        )

        report = ml.eval.xquery(
            render_test_resource(
                __file__,
                "test-constraint-options-are-valid-native-xml.xqy",
            ),
            variables={"options": tostring(options.to_xml(), encoding="unicode")},
            database=database,
        )

        assert report == 0

    def test_documents_sorted_with_inline_options(self, indexed_database):
        ml, database, _ = indexed_database
        options = SearchOptions().sort(
            Range(Element("price", NS), "xs:decimal"),
            direction="descending",
        )

        scoped = ml.search(database=database, collection="cts-test", options=options)
        docs = scoped.documents("alpha OR beta")

        assert [doc.uri for doc in docs] == ["/cts-test/b.xml", "/cts-test/a.xml"]

    def test_uris_with_inline_options(self, indexed_database):
        ml, database, _ = indexed_database

        uris = ml.search(
            database=database,
            collection="cts-test",
            options=SearchOptions().control("page-length", 1),
        ).uris(
            "alpha OR beta",
            pos=1,
        )

        assert len(uris) == 1
        assert uris[0] in URIS[:2]

    def test_snapshot_pagination(self, indexed_database):
        ml, database, _ = indexed_database
        first = ml.search(database=database, collection="cts-test").report(
            "alpha OR beta",
            pos=1,
        )

        second = ml.search(
            database=database,
            collection="cts-test",
            timestamp=first.effective_timestamp,
        ).report(
            "alpha OR beta",
            pos=2,
        )

        assert second.effective_timestamp == first.effective_timestamp
        assert first.results[0]["uri"] != second.results[0]["uri"]
        assert first.total == second.total == 2

    def test_documents_for_cts_query(self, indexed_database):
        ml, database, _ = indexed_database
        query = cts.and_query(
            [cts.collection_query("cts-test"), cts.word_query(["alpha", "gamma"])],
        )

        docs = ml.search(database=database).documents(query)

        assert sorted(doc.uri for doc in docs) == [
            "/cts-test/a.xml",
            "/cts-test/c.json",
        ]
        by_uri = {doc.uri: doc for doc in docs}
        assert isinstance(by_uri["/cts-test/a.xml"], XMLDocument)
        assert isinstance(by_uri["/cts-test/c.json"], JSONDocument)
        assert by_uri["/cts-test/c.json"].content == {"active": True, "label": "gamma"}

    def test_documents_for_structured_query(self, indexed_database):
        ml, database, _ = indexed_database
        query = sq.and_(
            sq.collection("cts-test"),
            sq.word(Element("label", NS), "beta"),
        )

        docs = ml.search(database=database).documents(query)

        assert [doc.uri for doc in docs] == ["/cts-test/b.xml"]

    def test_documents_for_string_query(self, indexed_database):
        ml, database, _ = indexed_database

        docs = ml.search(database=database).documents("gamma")

        assert [doc.uri for doc in docs] == ["/cts-test/c.json"]

    def test_documents_with_metadata(self, indexed_database):
        ml, database, _ = indexed_database

        docs = ml.search(database=database).documents(
            "gamma",
            category=["content", "collections"],
        )

        assert [doc.uri for doc in docs] == ["/cts-test/c.json"]
        assert docs[0].metadata.collections() == ["cts-test"]

    def test_documents_for_cts_range_query(self, indexed_database):
        ml, database, _ = indexed_database
        query = cts.element_range_query(fn.qname(NS, "price"), ">", Decimal(2))

        docs = ml.search(database=database).documents(query)

        assert [doc.uri for doc in docs] == ["/cts-test/b.xml"]

    def test_uris_for_cts_value_queries(self, indexed_database):
        ml, database, _ = indexed_database
        query = cts.or_query(
            [
                cts.element_value_query(fn.qname(NS, "label"), "alpha"),
                cts.json_property_value_query("active", True),
            ],
        )

        uris = ml.search(database=database).uris(query)

        assert sorted(uris) == ["/cts-test/a.xml", "/cts-test/c.json"]

    def test_documents_without_matches(self, indexed_database):
        ml, database, _ = indexed_database

        assert ml.search(database=database).documents(cts.word_query("zzz")) == []

    def test_uris_page_through_all_matches(self, indexed_database):
        ml, database, _ = indexed_database
        query = cts.collection_query("cts-test")

        pages = [
            ml.search(database=database).uris(query, pos=pos)
            for pos in ([1, 2], 3, [4, 5])
        ]

        assert [len(page) for page in pages] == [2, 1, 0]
        assert sorted(uri for page in pages for uri in page) == URIS

    def test_uris_without_matches(self, indexed_database):
        ml, database, _ = indexed_database

        assert ml.search(database=database).uris("zzz") == []

    def test_values_of_decimal_range_index(self, indexed_database, values_options):
        ml, database, _ = indexed_database

        values = ml.search(database=database, options=values_options).values("price")

        assert values == [
            ValueHit(Decimal("1.25"), frequency=1),
            ValueHit(Decimal("2.5"), frequency=1),
        ]

    def test_values_of_date_range_index_restricted_by_query(
        self,
        indexed_database,
        values_options,
    ):
        ml, database, _ = indexed_database

        values = ml.search(database=database, options=values_options).values(
            "day",
            cts.word_query("beta"),
        )

        assert values == [ValueHit(date(2026, 1, 2), frequency=1)]

    def test_values_of_undefined_name(self, indexed_database, values_options):
        ml, database, _ = indexed_database

        with pytest.raises(MarkLogicError, match="REST-INVALIDPARAM"):
            ml.search(database=database, options=values_options).values("missing")
