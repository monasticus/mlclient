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
from mlclient.functions.xqy import cts, fn, xdmp, xpath, xs
from mlclient.http import HTTPConfig
from mlclient.services import AsyncCtsService, CtsService

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


def test_search_projection_preserves_order_and_selects_hits_first(expression_database):
    ml, database, _ = expression_database
    service = CtsService(ml.rest, namespaces={"p": "urn:cts-test"})
    options = cts.index_order(
        cts.element_reference(fn.qname("urn:cts-test", "price")),
        options="descending",
    )
    parameters = {"expression": "/p:item", "options": options, "database": database}
    labels = service.search(**parameters, xpath="p:label")
    assert [label.text for label in labels] == ["beta", "alpha"]
    assert service.search(**parameters, index=2, xpath="p:label").text == "alpha"
    assert service.search(**parameters, range=[2, 2], xpath="p:label").text == "alpha"
    children = service.search(**parameters, index=1, xpath="*")
    assert [child.text for child in children] == ["2.50", "2026-01-02", "beta"]
    assert service.search(**parameters, index=100, xpath="p:label") == []
    assert service.search(**parameters, xpath="p:absent") == []
    assert service.search(**parameters, index=1, xpath="/p:item/p:label").text == "beta"
    assert (
        service.search(
            options=options,
            database=database,
            index=1,
            xpath="p:item/p:label",
        ).text
        == "beta"
    )
    with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH"):
        service.search(**parameters, xpath="p:label), fn:error() (: ")


@pytest.mark.asyncio
async def test_async_search_projection_preserves_order_and_selects_hits_first(
    expression_database,
):
    _, database, port = expression_database
    async with AsyncMLClient(port=port) as ml:
        service = AsyncCtsService(ml.rest, namespaces={"p": "urn:cts-test"})
        options = cts.index_order(
            cts.element_reference(fn.qname("urn:cts-test", "price")),
            options="descending",
        )
        parameters = {"expression": "/p:item", "options": options, "database": database}
        labels = await service.search(**parameters, xpath="p:label")
        assert [label.text for label in labels] == ["beta", "alpha"]
        label = await service.search(**parameters, index=2, xpath="p:label")
        assert label.text == "alpha"
        label = await service.search(**parameters, range=[2, 2], xpath="p:label")
        assert label.text == "alpha"
        assert await service.search(**parameters, xpath="p:absent") == []
        with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH"):
            await service.search(**parameters, xpath="p:label), fn:error() (: ")


def test_scalar_roundtrips_and_sequence_composition(expression_database):
    ml, database, _ = expression_database

    def evaluate(expr):
        return ml.eval.expression(expr, database=database)

    assert evaluate(fn.count([1, 2])) == 2
    assert evaluate(fn.exists([])) is False
    assert evaluate(fn.empty(None)) is True
    assert evaluate(xs.integer(2**60 + 1)) == 2**60 + 1
    with pytest.raises(MarkLogicError, match="XDMP-AS"):
        evaluate(xs.integer(2**80))
    assert evaluate(xs.decimal(Decimal("1.234567890123456789"))) == Decimal(
        "1.234567890123456789",
    )
    assert evaluate(xs.date(date(2026, 1, 2))) == date(2026, 1, 2)
    stamp = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert evaluate(xs.date_time(stamp)) == stamp
    assert evaluate(xs.double(float("inf"))) == float("inf")
    assert math.isnan(evaluate(xs.double(float("nan"))))
    assert evaluate(xs.string(fn.count([1, 2]))) == "2"
    assert evaluate(xpath("array-node {1,2}")) == [1, 2]
    assert evaluate(xpath('"line 1\n  line 2"')) == "line 1\n  line 2"
    assert evaluate(fn.count([None, [], [1, 2]])) == 2


def test_search_lexicons_ranges_and_namespace_composition(expression_database):
    ml, database, _ = expression_database
    service = CtsService(ml.rest)
    query = cts.and_query(
        [
            cts.collection_query("cts-test"),
            cts.element_range_query(
                fn.qname("urn:cts-test", "price"),
                ">=",
                Decimal("1.25"),
            ),
            cts.element_range_query(
                fn.qname("urn:cts-test", "day"),
                ">=",
                date(2026, 1, 1),
            ),
        ],
    )
    hits = cts.search(xpath("/Q{urn:cts-test}item"), query, options="filtered")
    assert ml.eval.expression(fn.count(hits), database=database) == 2
    assert ml.eval.expression(fn.count(hits.range(2, 2)), database=database) == 1
    assert ml.eval.expression(xdmp.exists(hits), database=database) is True
    assert (
        ml.eval.expression(
            xdmp.exists(xpath("/Q{urn:cts-test}absent")),
            database=database,
        )
        is False
    )
    assert service.search(query=cts.false_query(), database=database) == []
    assert (
        service.search(query=query, range=1, database=database).getroot().tag
        == "{urn:cts-test}item"
    )
    assert service.uris(query=query, database=database) == [
        "/cts-test/a.xml",
        "/cts-test/b.xml",
    ]
    assert (
        service.uris(query=query, start="/cts-test/b.xml", database=database)
        == "/cts-test/b.xml"
    )
    ref = cts.element_reference(fn.qname("urn:cts-test", "price"))
    values = cts.values(ref)
    assert ml.eval.expression(fn.count(values), database=database) == 2
    assert ml.eval.expression(fn.exists(values), database=database) is True
    assert service.values(ref, query=query, database=database) == [
        Decimal("1.25"),
        Decimal("2.50"),
    ]
    assert service.values(
        ref,
        query=query,
        start=Decimal(2),
        database=database,
    ) == Decimal("2.50")
    assert service.estimate(query, database=database) == 2
    assert service.estimate(query, maximum=1, database=database) == 1
    assert service.estimate(database=database) == 3
    assert ml.eval.expression(cts.estimate(), database=database) == 3
    assert service.search(
        query=cts.json_property_value_query("active", True),
        database=database,
    ) == {"active": True}
    assert (
        ml.eval.expression(
            fn.count(cts.search(query=query), maximum=1),
            database=database,
        )
        == 1
    )
    assert ml.eval.expression(
        cts.word_query("alpha", weight=xs.double(fn.count([1]))),
        database=database,
    )
    forests = xpath("xdmp:database-forests(xdmp:database())")
    assert service.uris(
        query=query,
        quality_weight=0,
        forest_ids=forests,
        database=database,
    ) == ["/cts-test/a.xml", "/cts-test/b.xml"]

    path_ref = cts.path_reference(
        "/p:item/p:price",
        namespaces=xpath('map:map() => map:with("p", "urn:cts-test")'),
    )
    assert service.values(path_ref, query=query, database=database) == [
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
    expr = cts.search(query=cts.document_root_query(fn.qname("urn:cts-test", "item")))
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
            assert ml.eval.expression(fn.count(native), database=database) == 1


def test_geospatial_and_triple_native_contracts(expression_database):
    ml, database, _ = expression_database
    pairs = cts.geospatial_co_occurrences(
        fn.qname("urn:cts-test", "origin"),
        fn.qname("urn:cts-test", "destination"),
    )
    result = ml.eval.expression(pairs, database=database)
    assert result.tag == "{http://marklogic.com/cts}co-occurrence"
    assert ml.eval.expression(fn.count(pairs), database=database) == 1
    for operator in ("sameTerm", ["=", "=", "<"], []):
        query = cts.triple_range_query([], [], 1, operator=operator)
        assert ml.eval.expression(fn.count(query), database=database) == 1


def test_text_callbacks_and_native_maps(expression_database):
    ml, database, _ = expression_database
    node = xpath("<p>alpha beta</p>")
    query = cts.parse("alpha")
    result = ml.eval.expression(
        cts.highlight(node, query, xpath("<b>{$cts:text}</b>")),
        database=database,
    )
    assert result.find("b").text == "alpha"
    assert (
        ml.eval.expression(
            cts.walk(node, query, xpath("$cts:text")),
            database=database,
        )
        == "alpha"
    )
    assert (
        ml.eval.expression(
            cts.contains(node, cts.parse("alpha", bindings=xpath("map:map()"))),
            database=database,
        )
        is True
    )


def test_extended_cts_catalog_executes_through_the_common_evaluator(
    expression_database,
):
    ml, database, _ = expression_database
    query = cts.collection_query("cts-test")
    price = cts.element_reference(fn.qname("urn:cts-test", "price"))

    assert ml.eval.expression(cts.contains(xpath("<p>alpha</p>"), query)) is False
    assert (
        ml.eval.expression(cts.collections(query=query), database=database)
        == "cts-test"
    )
    assert (
        ml.eval.expression(
            cts.collection_match("cts-*", query=query),
            database=database,
        )
        == "cts-test"
    )
    assert ml.eval.expression(
        cts.uri_match("/cts-test/*.xml", query=query),
        database=database,
    ) == ["/cts-test/a.xml", "/cts-test/b.xml"]
    assert ml.eval.expression(
        cts.min(price, query=query),
        database=database,
    ) == Decimal("1.25")
    assert ml.eval.expression(
        cts.max(price, query=query),
        database=database,
    ) == Decimal("2.50")
    assert (
        ml.eval.expression(
            cts.count_aggregate(price, query=query),
            database=database,
        )
        == 2
    )

    query_id = ml.eval.expression(cts.register(query), database=database)
    try:
        assert isinstance(query_id, int)
        assert (
            ml.eval.expression(
                cts.estimate(cts.registered_query(query_id)),
                database=database,
            )
            == 3
        )
    finally:
        ml.eval.expression(cts.deregister(query_id), database=database)


@pytest.mark.asyncio
async def test_async_execution_uses_the_same_composable_expressions(
    expression_database,
):
    _, database, port = expression_database
    async with AsyncMLClient(port=port) as ml:
        query = cts.collection_query("cts-test")
        service = AsyncCtsService(ml.rest)
        uris = await service.uris(query=query, database=database)
        assert (
            await service.uris(
                query=query,
                index=fn.last(),
                database=database,
            )
            == uris[-1]
        )
        assert await service.uris(query=query, index=100, database=database) == []
        assert (
            await ml.eval.expression(
                fn.count(cts.search(query=query)),
                database=database,
            )
            == 3
        )
        assert await ml.eval.expression(
            xs.date(date(2026, 1, 2)),
            database=database,
        ) == date(2026, 1, 2)
        assert (
            await AsyncCtsService(ml.rest).uris(
                query=query,
                range=1,
                database=database,
            )
            == "/cts-test/a.xml"
        )


def test_all_paths_are_guarded_with_shared_and_local_namespaces(expression_database):
    ml, database, _ = expression_database
    bindings = {"p": "urn:cts-test", "other": "urn:absent"}
    service = CtsService(ml.rest, namespaces=bindings)
    bindings["p"] = "urn:mutated"
    assert len(service.search("/p:item", database=database)) == 2
    assert (
        service.search(
            "/p:item",
            namespaces={"p": "urn:absent"},
            database=database,
        )
        == []
    )
    assert len(service.search("/p:item", database=database)) == 2
    assert (
        len(
            service.search(
                "/item",
                namespaces={"": "urn:cts-test"},
                database=database,
            ),
        )
        == 2
    )
    paths = [cts.search("/p:item"), cts.search("/other:item")]
    assert (
        ml.eval.expression(
            fn.count(paths),
            namespaces={"p": "urn:cts-test", "other": "urn:absent"},
            database=database,
        )
        == 2
    )
    assert (
        ml.eval.expression(
            cts.valid_extract_path("/p:item"),
            namespaces={"p": "urn:cts-test"},
            database=database,
        )
        is True
    )
    assert (
        ml.eval.expression(
            cts.valid_index_path("/p:item/p:price", False),
            namespaces={"p": "urn:cts-test"},
            database=database,
        )
        is True
    )
    default_service = CtsService(ml.rest, namespaces={"": "urn:cts-test"})
    assert len(default_service.search("/item", database=database)) == 2
    assert (
        default_service.search(
            "/item",
            namespaces={"": ""},
            database=database,
        )
        == []
    )
    uri = 'urn:test"; fn:error(xs:QName("INJECTED")); (: &'
    assert (
        ml.eval.expression(
            xpath('fn:namespace-uri-from-QName(xs:QName("p:x"))'),
            namespaces={"p": uri},
            output_type=str,
            database=database,
        )
        == uri
    )
    reference_bindings = {"p": "urn:cts-test"}
    reference = cts.path_reference("/p:item/p:price", namespaces=reference_bindings)
    reference_bindings["p"] = "urn:mutated"
    assert service.values(
        reference,
        namespaces={"p": "urn:absent"},
        database=database,
    ) == [Decimal("1.25"), Decimal("2.50")]
    assert (
        service.estimate(
            cts.path_range_query(["/p:item/p:price", "/p:item/p:price"], ">", 1),
            database=database,
        )
        == 2
    )
    assert (
        ml.eval.expression(
            fn.count(
                cts.search(
                    '/*[fn:node-name(.) => fn:string() => fn:contains("item")]',
                ),
            ),
            database=database,
        )
        == 2
    )


def test_all_invalid_paths_reported_before_executing_tree(expression_database):
    ml, database, _ = expression_database
    bad_paths = [
        '/*[fn:doc("/not-executed")]',
        '/*, ()) else "INJECTED", if (true()) then cts:search(/*',
        "/unknown:price",
        '/p:item/p:price[xdmp:version() = "10"]',
    ]
    expression = fn.count(
        [
            cts.search(bad_paths[0]),
            cts.search(bad_paths[1]),
            cts.uris(query=cts.path_range_query(bad_paths[2:], "=", 1)),
            xpath('fn:error(xs:QName("SHOULD-NOT-RUN"))'),
        ],
    )
    with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH") as error:
        ml.eval.expression(
            expression,
            namespaces={"p": "urn:cts-test"},
            database=database,
        )
    for path in bad_paths:
        assert path in str(error.value)
    assert "SHOULD-NOT-RUN" not in str(error.value)


@pytest.mark.asyncio
async def test_async_namespace_defaults_overrides_and_guard(expression_database):
    _, database, port = expression_database
    async with AsyncMLClient(port=port) as ml:
        service = AsyncCtsService(ml.rest, namespaces={"p": "urn:cts-test"})
        assert len(await service.search("/p:item", database=database)) == 2
        assert (
            await service.search(
                "/p:item",
                namespaces={"p": "urn:missing"},
                database=database,
            )
            == []
        )
        assert (
            await ml.eval.expression(
                fn.count(cts.search("/p:item")),
                namespaces={"p": "urn:cts-test"},
                database=database,
            )
            == 2
        )
        with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH"):
            await service.search("/absent:item", database=database)


def test_position_context_and_service_index(expression_database):
    ml, database, _ = expression_database
    expression = xpath("(10, 20, 30)")
    for position, expected in [(1, 10), (fn.last(), 30), (4, [])]:
        assert ml.eval.expression(expression.index(position)) == expected
    assert ml.eval.expression(expression.range(2, fn.last())) == [20, 30]
    assert ml.eval.expression(expression.range(fn.last(), fn.last())) == 30
    assert ml.eval.expression(expression.range(4, fn.last())) == []
    service = CtsService(ml.rest)
    uris = service.uris(database=database)
    assert service.uris(index=1, database=database) == uris[0]
    assert service.uris(index=fn.last(), database=database) == uris[-1]
    assert service.uris(index=100, database=database) == []
    assert service.uris(range=[2, fn.last()], database=database) == uris[1:]


def test_decimal_parsing_and_qname_constructors(expression_database):
    ml, database, _ = expression_database
    expected = Decimal("0.1234567890123456789")
    assert ml.eval.xquery('xs:decimal("0.1234567890123456789")') == expected
    assert ml.eval.expression(xs.decimal(expected)) == expected
    names = {"p": "urn:cts-test"}
    assert (
        ml.eval.expression(
            xs.string(xs.qname("p:item")),
            namespaces=names,
        )
        == "p:item"
    )
    assert ml.eval.expression(xs.string(fn.qname("urn:cts-test", "p:item"))) == "p:item"
    assert (
        ml.eval.expression(
            fn.count(
                cts.search(
                    query=cts.element_query(xs.qname("item"), cts.true_query()),
                ),
            ),
            namespaces={"": "urn:cts-test"},
            database=database,
        )
        == 2
    )


def test_invalid_paths_cover_all_native_path_argument_families(expression_database):
    ml, database, _ = expression_database
    paths = [f"/unknown:path{number}" for number in range(5)]
    expression = fn.count(
        [
            cts.geospatial_path_reference(paths[0]),
            cts.geospatial_region_path_reference(paths[1]),
            cts.path_geospatial_query(paths[2], cts.point(10, 20)),
            cts.path_range_query(paths[3], "=", 1),
            cts.path_reference(paths[4]),
            xpath('fn:error(fn:QName("", "SHOULD-NOT-RUN"))'),
        ],
    )
    with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH") as error:
        ml.eval.expression(expression, database=database)
    for path in paths:
        assert path in str(error.value)
    assert "SHOULD-NOT-RUN" not in str(error.value)


def test_fn_catalog_representative_native_execution(expression_database):
    ml, database, _ = expression_database
    assert ml.eval.expression(fn.concat("a", None, "b", "c")) == "abc"
    assert ml.eval.expression(fn.substring("MarkLogic", 5, length=5)) == "Logic"
    assert ml.eval.expression(fn.tokenize("a,b,c", ",")) == ["a", "b", "c"]
    total = ml.eval.expression(fn.sum([Decimal("0.1"), Decimal("0.2")]))
    assert total == Decimal("0.3")
    assert ml.eval.expression(fn.subsequence([10, 20, 30, 40], 2, length=2)) == [20, 30]
    assert ml.eval.expression(fn.head([])) == []
    assert ml.eval.expression(fn.tail([1, 2, 3])) == [2, 3]
    assert ml.eval.expression(fn.string(None)) == ""
    assert ml.eval.expression(fn.count(fn.collection()), database=database) == 3
    assert ml.eval.expression(fn.collection(None), database=database) == []
    upper = fn.function_lookup(
        fn.qname("http://www.w3.org/2005/xpath-functions", "upper-case"),
        1,
    )
    assert ml.eval.expression(fn.function_arity(upper)) == 1
    assert ml.eval.expression(fn.map(upper, ["a", "b"])) == ["A", "B"]
    assert ml.eval.expression(
        fn.filter(
            xpath("function($x) { $x gt 1 }"),
            [1, 2, 3],
        ),
    ) == [2, 3]
    assert (
        ml.eval.expression(
            fn.fold_left(
                xpath("function($sum, $x) { $sum + $x }"),
                0,
                [1, 2, 3],
            ),
        )
        == 6
    )
    assert (
        ml.eval.expression(
            fn.adjust_date_to_timezone(
                xpath('xs:date("2026-01-02+02:00")'),
                timezone=None,
            ),
            output_type=str,
        )
        == "2026-01-02"
    )
    with pytest.raises(MarkLogicError, match="FN-TEST"):
        ml.eval.expression(
            fn.error(
                fn.qname("", "FN-TEST"),
                description="expected test error",
            ),
        )
