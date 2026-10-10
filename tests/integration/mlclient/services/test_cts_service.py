from __future__ import annotations

from tests.utils.resources import render_test_resource

from decimal import Decimal

import pytest

from mlclient.exceptions import MarkLogicError
from mlclient.xquery import Cts, fn, xs
from mlclient.services import CtsService
from tests.utils.expressions import StaticExpression

pytestmark = pytest.mark.ml_access

NS = "https://monasticus.com/mlclient/examples/cts-test"
PRICE = fn.qname(NS, "price")
PRICE_REF = Cts.element_reference(PRICE)
FIELD_REF = Cts.field_reference("price")
NODE = fn.doc("/cts-test/a.xml")
SEARCH_NODE = Cts.search(
    query=Cts.word_query("alpha"),
    options="relevance-trace",
).pos(1)
TRAINING_NODES = [NODE, fn.doc("/cts-test/b.xml")]
LABELS = StaticExpression(
    render_test_resource(__file__, "query.xqy"),
)
CLASSIFIER = Cts.train(TRAINING_NODES, LABELS)
DICTIONARY = Cts.entity_dictionary(Cts.entity("alpha", "alpha", "alpha", "label"))

OPERATIONS = [
    ("entity_dictionary_get", ("/cts-test/dictionary",), {}),
    ("triples", (), {}),
    ("json_property_word_match", ("label", "g*"), {}),
    ("json_property_words", ("label",), {}),
    ("element_attribute_word_match", (fn.qname(NS, "item"), "amount", "1*"), {}),
    ("element_attribute_words", (fn.qname(NS, "item"), "amount"), {}),
    (
        "match_regions",
        (
            Cts.element_reference(fn.qname(NS, "region")),
            "intersects",
            Cts.point(10, 20),
        ),
        {},
    ),
    ("classify", (TRAINING_NODES, CLASSIFIER), {}),
    ("train", (TRAINING_NODES, LABELS), {}),
    (
        "thresholds",
        (Cts.classify(TRAINING_NODES, CLASSIFIER), LABELS),
        {},
    ),
    ("entity_highlight", (NODE, xs.string("matched")), {"dict": DICTIONARY}),
    ("entity_walk", (NODE, xs.string("matched")), {"dict": DICTIONARY}),
    ("search", (), {"query": Cts.word_query("alpha")}),
    ("uris", (), {}),
    ("values", (PRICE_REF,), {}),
    ("estimate", (), {}),
    ("avg_aggregate", (PRICE_REF,), {}),
    ("cluster", (NODE,), {}),
    ("collection_match", ("cts-*",), {}),
    ("collections", (), {}),
    ("confidence", (), {"node": SEARCH_NODE}),
    ("contains", (NODE, Cts.word_query("alpha")), {}),
    ("correlation", (PRICE_REF, FIELD_REF), {}),
    ("count_aggregate", (PRICE_REF,), {}),
    ("covariance", (PRICE_REF, FIELD_REF), {}),
    ("covariance_p", (PRICE_REF, FIELD_REF), {}),
    ("distinctive_terms", (NODE,), {}),
    ("element_value_co_occurrences", (PRICE, fn.qname(NS, "day")), {}),
    ("element_value_match", (PRICE, Decimal("1.25")), {}),
    ("element_value_ranges", (PRICE,), {"bounds": [1, 2, 3]}),
    ("element_values", (PRICE,), {}),
    ("element_walk", (NODE, fn.qname(NS, "label"), xs.string("changed")), {}),
    ("field_value_match", ("price", Decimal("1.25")), {}),
    ("field_value_co_occurrences", ("price", "price-copy"), {}),
    ("field_value_ranges", ("price",), {"bounds": [1, 2, 3]}),
    ("field_values", ("price",), {}),
    ("field_word_match", ("label", "a*"), {}),
    ("field_words", ("label",), {}),
    ("element_word_match", (fn.qname(NS, "label"), "a*"), {}),
    ("element_words", (fn.qname(NS, "label"),), {}),
    ("element_geospatial_boxes", (fn.qname(NS, "origin"),), {}),
    ("element_geospatial_value_match", (fn.qname(NS, "origin"), "10,20"), {}),
    ("element_geospatial_values", (fn.qname(NS, "origin"),), {}),
    (
        "geospatial_boxes",
        (Cts.geospatial_element_reference(fn.qname(NS, "origin")),),
        {},
    ),
    (
        "geospatial_co_occurrences",
        (fn.qname(NS, "origin"), fn.qname(NS, "destination")),
        {},
    ),
    (
        "element_value_geospatial_co_occurrences",
        (PRICE, fn.qname(NS, "origin")),
        {},
    ),
    ("fitness", (), {"node": SEARCH_NODE}),
    ("frequency", (Cts.values(PRICE_REF).pos(1),), {}),
    ("highlight", (NODE, Cts.word_query("alpha"), xs.string("changed")), {}),
    ("linear_model", ([PRICE_REF, FIELD_REF],), {}),
    ("max", (PRICE_REF,), {}),
    ("median", (Cts.values(PRICE_REF),), {}),
    ("min", (PRICE_REF,), {}),
    ("part_of_speech", (xs.string("running"),), {}),
    ("percent_rank", (Cts.values(PRICE_REF), Decimal("1.25")), {}),
    ("percentile", (Cts.values(PRICE_REF), 0.5), {}),
    ("quality", (), {"node": SEARCH_NODE}),
    ("rank", (Cts.values(PRICE_REF), Decimal("1.25")), {}),
    ("relevance_info", (), {"node": SEARCH_NODE}),
    ("remainder", (), {"node": SEARCH_NODE}),
    ("score", (), {"node": SEARCH_NODE}),
    ("stddev", (PRICE_REF,), {}),
    ("stddev_p", (PRICE_REF,), {}),
    ("stem", ("running",), {}),
    ("sum_aggregate", (PRICE_REF,), {}),
    ("tokenize", ("alpha beta",), {}),
    ("triple_value_statistics", (), {}),
    ("uri_match", ("/cts-test/*",), {}),
    ("valid_document_patch_path", ("/t:item/t:price",), {}),
    ("valid_extract_path", ("/t:item/t:price",), {}),
    ("valid_index_path", ("/t:item/t:price", False), {}),
    ("valid_optic_path", ("/t:item/t:price",), {}),
    ("valid_tde_context", ("/t:item",), {}),
    ("value_co_occurrences", (PRICE_REF, FIELD_REF), {}),
    ("value_match", (PRICE_REF, Decimal("1.25")), {}),
    ("value_ranges", (PRICE_REF,), {"bounds": [1, 2, 3]}),
    ("value_tuples", (PRICE_REF,), {}),
    ("variance", (PRICE_REF,), {}),
    ("variance_p", (PRICE_REF,), {}),
    ("walk", (NODE, Cts.word_query("alpha"), xs.string("matched")), {}),
    ("word_match", ("a*",), {}),
    ("words", (), {}),
    (
        "element_attribute_value_co_occurrences",
        (fn.qname(NS, "item"), "amount", fn.qname(NS, "item"), "quantity"),
        {},
    ),
    (
        "element_attribute_value_geospatial_co_occurrences",
        (fn.qname(NS, "item"), "amount", fn.qname(NS, "origin")),
        {},
    ),
    (
        "element_attribute_value_match",
        (fn.qname(NS, "item"), "amount", Decimal("1.25")),
        {},
    ),
    (
        "element_attribute_value_ranges",
        (fn.qname(NS, "item"), "amount"),
        {"bounds": [1, 2, 3]},
    ),
    ("element_attribute_values", (fn.qname(NS, "item"), "amount"), {}),
    (
        "element_attribute_pair_geospatial_boxes",
        (fn.qname(NS, "item"), "lat", "lon"),
        {},
    ),
    (
        "element_attribute_pair_geospatial_value_match",
        (fn.qname(NS, "item"), "lat", "lon", "10,20"),
        {},
    ),
    (
        "element_attribute_pair_geospatial_values",
        (fn.qname(NS, "item"), "lat", "lon"),
        {},
    ),
    (
        "element_child_geospatial_boxes",
        (fn.qname(NS, "location"), fn.qname(NS, "point")),
        {},
    ),
    (
        "element_child_geospatial_value_match",
        (fn.qname(NS, "location"), fn.qname(NS, "point"), "10,20"),
        {},
    ),
    (
        "element_child_geospatial_values",
        (fn.qname(NS, "location"), fn.qname(NS, "point")),
        {},
    ),
    (
        "element_pair_geospatial_boxes",
        (fn.qname(NS, "location"), fn.qname(NS, "lat"), fn.qname(NS, "lon")),
        {},
    ),
    (
        "element_pair_geospatial_value_match",
        (fn.qname(NS, "location"), fn.qname(NS, "lat"), fn.qname(NS, "lon"), "10,20"),
        {},
    ),
    (
        "element_pair_geospatial_values",
        (fn.qname(NS, "location"), fn.qname(NS, "lat"), fn.qname(NS, "lon")),
        {},
    ),
    (
        "period_compare",
        (
            Cts.period(
                xs.date_time("2026-01-01T00:00:00"),
                xs.date_time("2026-01-02T00:00:00"),
            ),
            "aln_equals",
            Cts.period(
                xs.date_time("2026-01-01T00:00:00"),
                xs.date_time("2026-01-02T00:00:00"),
            ),
        ),
        {},
    ),
]


class TestCtsService:
    def test_aggregate(self, indexed_database):
        ml, database, _ = indexed_database
        cts = CtsService(ml.rest)

        with pytest.raises(MarkLogicError, match=r"^XDMP-NOLIBRARY:"):
            cts.aggregate(
                "native/mlclient-missing-plugin",
                "sum",
                PRICE_REF,
                database=database,
            )

    def test_register(self, indexed_database):
        ml, database, _ = indexed_database
        cts = CtsService(ml.rest)

        [identifier] = cts.register(Cts.word_query("alpha"), database=database)
        try:
            assert isinstance(identifier, int)
            assert cts.search(
                query=Cts.registered_query(identifier),
                database=database,
            )
        finally:
            cts.deregister(identifier, database=database)

    def test_deregister(self, indexed_database):
        ml, database, _ = indexed_database
        cts = CtsService(ml.rest)
        [identifier] = cts.register(Cts.word_query("alpha"), database=database)

        result = cts.deregister(identifier, database=database)

        assert result == []
        with pytest.raises(MarkLogicError):
            cts.search(query=Cts.registered_query(identifier), database=database)

    @pytest.mark.parametrize(
        ("name", "args", "kwargs"),
        OPERATIONS,
        ids=[name for name, _, _ in OPERATIONS],
    )
    def test_operation_returns_results(self, indexed_database, name, args, kwargs):
        ml, database, _ = indexed_database
        cts = CtsService(ml.rest, namespaces={"t": NS})

        result = getattr(cts, name)(*args, **kwargs, database=database)

        assert result
