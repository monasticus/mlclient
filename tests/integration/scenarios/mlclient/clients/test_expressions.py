"""Expression round-trips in an isolated database, removed after the module."""

from __future__ import annotations

import math
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from mlclient import AsyncMLClient, MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.functions import cts, fn, xdmp, xpath, xs
from mlclient.http import HTTPConfig
from mlclient.services import AsyncCtsService, AsyncFnService, CtsService, FnService

pytestmark = pytest.mark.ml_access


@pytest.fixture(scope="module")
def expression_database():
    port = int(os.environ.get("MLCLIENT_CTS_PORT", "8000"))
    manage_port = int(os.environ.get("MLCLIENT_CTS_MANAGE_PORT", "8002"))
    name = f"mlclient-cts-test-{uuid4().hex}"
    with MLClient(port=port, manage_config=HTTPConfig.resolve(port=manage_port)) as ml:
        ml.manage.databases.create(
            {
                "database-name": name,
                "uri-lexicon": True,
                "collection-lexicon": True,
                "geospatial-element-index": [
                    {
                        "namespace-uri": "urn:cts-test",
                        "localname": name,
                        "coordinate-system": "wgs84",
                        "point-format": "point",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    }
                    for name in ("origin", "destination")
                ],
                "path-namespace": [{"prefix": "t", "namespace-uri": "urn:cts-test"}],
                "range-path-index": [
                    {
                        "scalar-type": "decimal",
                        "path-expression": "/t:item/t:price",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                ],
                "range-element-index": [
                    {
                        "scalar-type": "decimal",
                        "namespace-uri": "urn:cts-test",
                        "localname": "price",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                    {
                        "scalar-type": "date",
                        "namespace-uri": "urn:cts-test",
                        "localname": "day",
                        "range-value-positions": False,
                        "invalid-values": "reject",
                    },
                ],
            },
        ).raise_for_status()
        try:
            host = ml.eval.xquery("xdmp:host-name(xdmp:host())")
            ml.manage.forests.create(
                {"forest-name": name, "host": host, "database": name},
            ).raise_for_status()
            ml.eval.xquery(
                """
                xdmp:document-insert("/cts-test/a.xml",
                    <item xmlns="urn:cts-test"><price>1.25</price>
                        <day>2026-01-01</day><label>alpha</label>
                        <origin>10,20</origin><destination>30,40</destination></item>,
                    (), "cts-test"),
                xdmp:document-insert("/cts-test/b.xml",
                    <item xmlns="urn:cts-test"><price>2.50</price>
                        <day>2026-01-02</day><label>beta</label></item>,
                    (), "cts-test"),
                xdmp:document-insert("/cts-test/c.json",
                    object-node {"active": true()}, (), "cts-test")
            """,
                database=name,
            )
            yield ml, name, port
        finally:
            ml.manage.databases.delete(name, forest_delete="data").raise_for_status()


def test_scalar_roundtrips_and_sequence_composition(expression_database):
    ml, database, _ = expression_database

    def evaluate(expr):
        return ml.eval.expression(expr, database=database)

    assert evaluate(fn.count([1, 2])) == [2]
    assert evaluate(fn.exists([])) == [False]
    assert evaluate(fn.empty(None)) == [True]
    assert evaluate(xs.integer(2**60 + 1)) == [2**60 + 1]
    with pytest.raises(MarkLogicError, match="XDMP-CAST"):
        evaluate(xs.integer(2**80))
    assert evaluate(xs.decimal(Decimal("1.234567890123456789"))) == [
        Decimal("1.234567890123456789"),
    ]
    assert evaluate(xs.date(date(2026, 1, 2))) == [date(2026, 1, 2)]
    stamp = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert evaluate(xs.date_time(stamp)) == [stamp]
    assert evaluate(xs.double(float("inf"))) == [float("inf")]
    assert math.isnan(evaluate(xs.double(float("nan")))[0])
    assert evaluate(xs.string(fn.count([1, 2]))) == ["2"]
    assert evaluate(xpath("array-node {1,2}")) == [[1, 2]]
    assert evaluate(xpath('"line 1\n  line 2"')) == ["line 1\n  line 2"]
    assert evaluate(fn.count([None, [], [1, 2]])) == [2]


def test_search_lexicons_ranges_and_namespace_composition(expression_database):
    ml, database, _ = expression_database
    service = CtsService(ml.rest)
    query = cts.and_query(
        [
            cts.collection_query("cts-test"),
            cts.element_range_query(
                xs.qname("price", "urn:cts-test"),
                ">=",
                Decimal("1.25"),
            ),
            cts.element_range_query(
                xs.qname("day", "urn:cts-test"),
                ">=",
                date(2026, 1, 1),
            ),
        ],
    )
    hits = cts.search(xpath("/Q{urn:cts-test}item"), query, options="filtered")
    assert FnService(ml.rest).count(hits, database=database) == 2
    assert ml.eval.expression(fn.count(hits.window(2, 2)), database=database) == [1]
    assert ml.eval.expression(xdmp.exists(hits), database=database) == [True]
    assert ml.eval.expression(
        xdmp.exists(xpath("/Q{urn:cts-test}absent")),
        database=database,
    ) == [False]
    assert service.search(query=cts.false_query(), database=database) == []
    assert len(service.search(query=query, range=1, database=database)) == 1
    assert service.uris(query, database=database) == [
        "/cts-test/a.xml",
        "/cts-test/b.xml",
    ]
    assert service.uris(query, start="/cts-test/b.xml", database=database) == [
        "/cts-test/b.xml",
    ]
    ref = cts.element_reference(xs.qname("price", "urn:cts-test"))
    assert service.values(ref, query, database=database) == [
        Decimal("1.25"),
        Decimal("2.50"),
    ]
    assert service.values(ref, query, start=Decimal(2), database=database) == [
        Decimal("2.50"),
    ]
    assert service.estimate(query, database=database) == 2
    assert service.estimate(query, maximum=1, database=database) == 1
    assert service.estimate(database=database) == 3
    assert ml.eval.expression(cts.estimate(), database=database) == [3]
    assert service.search(
        query=cts.json_property_value_query("active", True),
        database=database,
    ) == [{"active": True}]
    assert ml.eval.expression(
        fn.count(cts.search(query=query), maximum=1),
        database=database,
    ) == [1]
    assert ml.eval.expression(
        cts.word_query("alpha", weight=xs.double(fn.count([1]))),
        database=database,
    )
    forests = xpath("xdmp:database-forests(xdmp:database())")
    assert service.uris(
        query,
        quality_weight=0,
        forest_ids=forests,
        database=database,
    ) == ["/cts-test/a.xml", "/cts-test/b.xml"]

    path_ref = cts.path_reference(
        "/p:item/p:price",
        namespaces=xpath('map:map() => map:with("p", "urn:cts-test")'),
    )
    assert service.values(path_ref, query, database=database) == [
        Decimal("1.25"),
        Decimal("2.50"),
    ]
    assert (
        service.estimate(
            cts.path_range_query(
                "/Q{urn:cts-test}item/Q{urn:cts-test}price",
                ">",
                Decimal(2),
            ),
            database=database,
        )
        == 1
    )
    assert (
        service.search(
            query=cts.word_query(
                "(: (( :) /), cts:false-query()), 424242, (( (: )) :)",
            ),
            database=database,
        )
        == []
    )


def test_native_version_support_is_reported_by_server(expression_database):
    ml, database, _ = expression_database
    major = int(ml.eval.xquery("xdmp:version()").split(".")[0])
    expr = cts.search(query=cts.document_root_query(xs.qname("item", "urn:cts-test")))
    if major < 11:
        with pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
            ml.eval.expression(expr, database=database)
    else:
        assert len(ml.eval.expression(expr, database=database)) == 2
    for native in (
        cts.document_format_query("xml"),
        cts.document_permission_query("admin", "read"),
        cts.iri_reference(),
    ):
        if major < 11:
            with pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
                ml.eval.expression(native, database=database)
        else:
            assert ml.eval.expression(fn.count(native), database=database) == [1]


def test_geospatial_and_triple_native_contracts(expression_database):
    ml, database, _ = expression_database
    pairs = cts.geospatial_co_occurrences(
        xs.qname("origin", "urn:cts-test"),
        xs.qname("destination", "urn:cts-test"),
    )
    result = ml.eval.expression(pairs, database=database)
    assert len(result) == 1
    assert result[0].tag == "{http://marklogic.com/cts}co-occurrence"
    assert ml.eval.expression(fn.count(pairs), database=database) == [1]
    for operator in ("sameTerm", ["=", "=", "<"], []):
        query = cts.triple_range_query([], [], 1, operator=operator)
        assert ml.eval.expression(fn.count(query), database=database) == [1]


def test_text_callbacks_and_native_maps(expression_database):
    ml, database, _ = expression_database
    node = xpath("<p>alpha beta</p>")
    query = cts.parse("alpha")
    result = ml.eval.expression(
        cts.highlight(node, query, xpath("<b>{$cts:text}</b>")),
        database=database,
    )
    assert result[0].find("b").text == "alpha"
    assert ml.eval.expression(
        cts.walk(node, query, xpath("$cts:text")),
        database=database,
    ) == ["alpha"]
    assert ml.eval.expression(
        cts.contains(node, cts.parse("alpha", bindings=xpath("map:map()"))),
        database=database,
    ) == [True]


def test_extended_cts_catalog_executes_through_the_common_evaluator(
    expression_database,
):
    ml, database, _ = expression_database
    query = cts.collection_query("cts-test")
    price = cts.element_reference(xs.qname("price", "urn:cts-test"))

    assert ml.eval.expression(cts.contains(xpath("<p>alpha</p>"), query)) == [False]
    assert ml.eval.expression(cts.collections(query=query), database=database) == [
        "cts-test",
    ]
    assert ml.eval.expression(
        cts.collection_match("cts-*", query=query),
        database=database,
    ) == ["cts-test"]
    assert ml.eval.expression(
        cts.uri_match("/cts-test/*.xml", query=query),
        database=database,
    ) == ["/cts-test/a.xml", "/cts-test/b.xml"]
    assert ml.eval.expression(cts.min(price, query=query), database=database) == [
        Decimal("1.25"),
    ]
    assert ml.eval.expression(cts.max(price, query=query), database=database) == [
        Decimal("2.50"),
    ]
    assert ml.eval.expression(
        cts.count_aggregate(price, query=query),
        database=database,
    ) == [2]

    query_id = ml.eval.expression(cts.register(query), database=database)[0]
    try:
        assert isinstance(query_id, int)
        assert ml.eval.expression(
            cts.estimate(cts.registered_query(query_id)),
            database=database,
        ) == [3]
    finally:
        ml.eval.expression(cts.deregister(query_id), database=database)


@pytest.mark.asyncio
async def test_async_execution_uses_the_same_composable_expressions(
    expression_database,
):
    _, database, port = expression_database
    async with AsyncMLClient(port=port) as ml:
        query = cts.collection_query("cts-test")
        assert (
            await AsyncFnService(ml.rest).count(
                cts.search(query=query),
                database=database,
            )
            == 3
        )
        assert await ml.eval.expression(
            xs.date(date(2026, 1, 2)),
            database=database,
        ) == [date(2026, 1, 2)]
        assert await AsyncCtsService(ml.rest).uris(
            query,
            range=1,
            database=database,
        ) == ["/cts-test/a.xml"]
