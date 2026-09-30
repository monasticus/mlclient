from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError
from mlclient.functions.xqy import cts, fn, xs
from mlclient.models import BinaryDocument, JSONDocument, TextDocument
from mlclient.services import AsyncCtsService

pytestmark = pytest.mark.ml_access


class TestAsyncCtsService:
    @pytest.mark.asyncio
    async def test_value_tuples_keep_single_json_array_inside_result_list(
        self,
        indexed_database,
    ):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            service = AsyncCtsService(ml.rest)
            assert await service.value_tuples(
                cts.uri_reference(),
                query=cts.document_query("/cts-test/a.xml"),
                database=database,
            ) == [["/cts-test/a.xml"]]

    @pytest.mark.asyncio
    async def test_mixed_content_and_scalar_nodes_preserve_types_and_scores(
        self,
        indexed_database,
    ):
        (ml, database, port) = indexed_database
        uris = ["/cts-types/text.txt", "/cts-types/binary.bin", "/cts-types/json.json"]
        binary = b"\x00\xffA\r\n\x00"
        try:
            ml.documents.write(
                [
                    TextDocument("abcd", uri=uris[0]),
                    BinaryDocument(binary, uri=uris[1]),
                    JSONDocument(
                        {"a": "b", "n": 123, "f": False, "z": None, "arr": [1, 2]},
                        uri=uris[2],
                    ),
                ],
                database=database,
            )
            async with AsyncMLClient(port=port) as async_ml:
                service = AsyncCtsService(async_ml.rest)
                query = cts.document_query([*uris, "/cts-test/a.xml"])
                hits = await service.search(query=query, database=database)
                by_uri = {hit.source_uri: hit for hit in hits}
                assert by_uri[uris[0]].content == "abcd"
                assert by_uri[uris[1]].content == binary
                assert by_uri[uris[2]].content["z"] is None
                [text_hit] = await service.search(
                    query=cts.document_query(uris[2]),
                    xpath='text("a")',
                    database=database,
                )
                assert text_hit.content == "b"
        finally:
            ml.documents.delete(uris, database=database)

    @pytest.mark.asyncio
    async def test_field_values_aggregates_and_map_boundary(self, indexed_database):
        (_, database, port) = indexed_database
        async with AsyncMLClient(port=port) as async_ml:
            service = AsyncCtsService(async_ml.rest)
            [value] = await service.field_values("price", index=2, database=database)
            assert value.value == Decimal("2.50")
            assert value.frequency == 1
            assert await service.sum_aggregate(
                cts.field_reference("price"),
                database=database,
            ) == [Decimal("3.75")]

    @pytest.mark.asyncio
    async def test_async_search_xpath_preserves_order_and_selects_hits_first(
        self,
        indexed_database,
    ):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            service = AsyncCtsService(
                ml.rest,
                namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
            )
            options = cts.index_order(
                cts.element_reference(
                    fn.qname(
                        "https://monasticus.com/mlclient/examples/cts-test",
                        "price",
                    ),
                ),
                options="descending",
            )
            parameters = {
                "expression": "/p:item",
                "options": options,
                "database": database,
            }
            labels = await service.search(**parameters, xpath="p:label")
            assert [label.content.text for label in labels] == ["beta", "alpha"]
            [label] = await service.search(**parameters, index=2, xpath="p:label")
            assert label.content.text == "alpha"
            [label] = await service.search(**parameters, range=[2, 2], xpath="p:label")
            assert label.content.text == "alpha"
            assert await service.search(**parameters, xpath="p:absent") == []
            with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH"):
                await service.search(**parameters, xpath="p:label), fn:error() (: ")

    @pytest.mark.asyncio
    async def test_async_execution_uses_the_same_composable_expressions(
        self,
        indexed_database,
    ):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            service = AsyncCtsService(ml.rest)
            query = cts.collection_query("cts-test")
            uris = await service.uris(query=query, database=database)
            assert (
                await service.uris(
                    query=query,
                    index=fn.last(),
                    database=database,
                )
            ) == [uris[-1]]
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
                await service.uris(
                    query=query,
                    range=1,
                    database=database,
                )
            ) == ["/cts-test/a.xml"]

    @pytest.mark.asyncio
    async def test_async_namespace_defaults_overrides_and_guard(self, indexed_database):
        _, database, port = indexed_database
        async with AsyncMLClient(port=port) as ml:
            service = AsyncCtsService(
                ml.rest,
                namespaces={"p": "https://monasticus.com/mlclient/examples/cts-test"},
            )
            assert len(await service.search("/p:item", database=database)) == 2
            assert (
                await service.search(
                    "/p:item",
                    namespaces={
                        "p": "https://monasticus.com/mlclient/examples/missing",
                    },
                    database=database,
                )
                == []
            )
            assert (
                await ml.eval.expression(
                    fn.count(cts.search("/p:item")),
                    namespaces={
                        "p": "https://monasticus.com/mlclient/examples/cts-test",
                    },
                    database=database,
                )
                == 2
            )
            with pytest.raises(MarkLogicError, match="MLCLIENT-INVALID-PATH"):
                await service.search("/absent:item", database=database)
