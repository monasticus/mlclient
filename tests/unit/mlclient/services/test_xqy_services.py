from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.functions.xqy import Expr, cts, fn, xdmp, xpath, xs
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.responses import MLResponseParser
from mlclient.services import (
    AsyncCtsService,
    CtsService,
)


def _response(*items):
    parts = [
        MultipartPart({"Content-Type": mime, "X-Primitive": primitive}, value.encode())
        for primitive, mime, value in items
    ]
    body, content_type = encode_multipart_mixed(parts)
    return httpx.Response(200, content=body, headers={"Content-Type": content_type})


@pytest.mark.parametrize(
    ("items", "expected"),
    [
        ([], []),
        ([("integer", "text/plain", "0")], 0),
        ([("boolean", "text/plain", "false")], False),
        ([("string", "text/plain", "")], ""),
        ([("array-node", "application/json", "[]")], []),
        ([("array-node", "application/json", "[1,2]")], [1, 2]),
        ([("array-node", "application/json", "[[1]]")], [[1]]),
        (
            [("integer", "text/plain", "1"), ("integer", "text/plain", "2")],
            [1, 2],
        ),
    ],
)
@pytest.mark.asyncio
@respx.mock
async def test_eval_collapses_only_the_outer_singleton(items, expected):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(*items),
    )
    with MLClient() as ml:
        result = ml.eval.expression(fn.count([]))
    async with AsyncMLClient() as ml:
        async_result = await ml.eval.expression(fn.count([]))
    assert result == expected
    assert type(result) is type(expected)
    assert async_result == expected
    assert type(async_result) is type(expected)
    assert route.call_count == 2


@respx.mock
def test_typed_items_and_raw_overrides_share_parser():
    items = [
        ("decimal", "text/plain", "1.234567890123456789"),
        ("double", "text/plain", "1.25"),
        ("float", "text/plain", "INF"),
        ("unsignedLong", "text/plain", "18446744073709551615"),
        ("date", "text/plain", "2026-01-02"),
        ("dateTime", "text/plain", "2026-01-02T03:04:05Z"),
        ("dateTime", "text/plain", "2026-01-02T03:04:05.123"),
        ("boolean", "text/plain", "1"),
        ("boolean", "text/plain", "false"),
        ("QName", "text/plain", "p:x"),
    ]
    respx.post("http://localhost:8000/v1/eval").mock(return_value=_response(*items))
    with MLClient() as ml:
        assert ml.eval.expression(xs.string("unused")) == [
            Decimal("1.234567890123456789"),
            1.25,
            float("inf"),
            18446744073709551615,
            date(2026, 1, 2),
            datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            datetime(2026, 1, 2, 3, 4, 5, 123000),
            True,
            False,
            b"p:x",
        ]
        assert ml.eval.expression(fn.count([]), output_type=str) == [
            i[2] for i in items
        ]
        assert ml.eval.expression(fn.count([]), output_type=bytes) == [
            i[2].encode() for i in items
        ]
    response = _response(items[0])
    response.request = httpx.Request("POST", "http://localhost/v1/eval")
    assert MLResponseParser.parse(response) == Decimal(items[0][2])


@respx.mock
def test_xml_json_and_nonmultipart_results():
    route = respx.post("http://localhost:8000/v1/eval")
    with MLClient() as ml:
        route.mock(
            return_value=_response(
                ("document-node()", "application/xml", "<a/>"),
                ("element", "application/xml", "<b/>"),
                ("object-node", "application/json", '{"a":1}'),
            ),
        )
        a, b, c = ml.eval.expression(cts.search())
        assert a.getroot().tag == "a"
        assert b.tag == "b"
        assert c == {"a": 1}
        route.mock(
            return_value=httpx.Response(
                200,
                content="7",
                headers={"Content-Type": "text/plain", "X-Primitive": "integer"},
            ),
        )
        assert ml.eval.expression(fn.count([])) == 7
        route.mock(return_value=httpx.Response(200, content=b""))
        assert ml.eval.expression(fn.count([])) == []


class _CountedExpr(Expr):
    def __init__(self):
        self.renders = 0

    def render(self, ctx):
        self.renders += 1
        return xs.decimal(Decimal("1.234567890123456789")).render(ctx)


@respx.mock
def test_wire_parameters_timeout_and_single_compilation():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("decimal", "text/plain", "1.234567890123456789")),
    )
    expr = _CountedExpr()
    with MLClient() as ml:
        assert ml.eval.expression(
            expr, database="test", txid="123", timeout=2,
        ) == Decimal("1.234567890123456789")
    request = route.calls.last.request
    body = parse_qs(request.content.decode())
    assert json.loads(body["vars"][0]) == {"v0": "1.234567890123456789"}
    assert "\n" in body["xquery"][0]
    assert dict(request.url.params) == {"database": "test", "txid": "123"}
    assert request.extensions["timeout"]["read"] == 2
    assert expr.renders == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_expression_and_all_conveniences_share_execution_contract():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("integer", "text/plain", "1")),
    )
    async with AsyncMLClient() as ml:
        assert await ml.eval.expression(xs.integer(1)) == 1
        service = AsyncCtsService(ml.rest)
        assert await service.search(query=cts.true_query(), range=1) == 1
        assert await service.uris(range=[1, 2]) == 1
        assert await service.values(cts.uri_reference(), range=1) == 1
        assert await service.search(index=1) == 1
        assert await service.uris(index=fn.last()) == 1
        assert await service.values(cts.uri_reference(), index=1) == 1
        with pytest.raises(ValueError, match="mutually exclusive"):
            await service.search(index=1, range=[1, 2])
        assert await service.estimate(maximum=1) == 1
        assert await ml.eval.expression(fn.count([1], maximum=1)) == 1
        route.mock(return_value=_response(("boolean", "text/plain", "true")))
        assert await ml.eval.expression(fn.exists([1])) is True
        assert await ml.eval.expression(fn.empty([])) is True
        assert await ml.eval.expression(xdmp.exists(xpath("/"))) is True


@respx.mock
def test_sync_conveniences_share_result_cardinality():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("integer", "text/plain", "1")),
    )
    with MLClient() as ml:
        service = CtsService(ml.rest)
        assert service.word_query("cat").compile() == cts.word_query("cat").compile()
        assert service.search(range=1) == 1
        assert service.uris(range=[1, 2]) == 1
        assert service.values(cts.uri_reference()) == 1
        assert service.search(index=1) == 1
        assert service.uris(index=fn.last()) == 1
        assert service.values(cts.uri_reference(), index=1) == 1
        with pytest.raises(ValueError, match="mutually exclusive"):
            service.uris(index=1, range=[1, 2])
        assert service.estimate() == 1
        assert ml.eval.expression(fn.count([1])) == 1
        route.mock(return_value=_response(("boolean", "text/plain", "true")))
        assert ml.eval.expression(fn.exists([1])) is True
        assert ml.eval.expression(fn.empty([])) is True
        assert ml.eval.expression(xdmp.exists(xpath("/"))) is True
        route.mock(return_value=_response())
        with pytest.raises(TypeError, match="exactly one"):
            service.estimate()


@pytest.mark.parametrize("value", [True, 1.5, (1,), (1, 2, 3), [1], [1, 2, 3]])
@respx.mock
def test_service_range_validation_happens_before_io(value):
    with MLClient() as ml, pytest.raises(TypeError, match="range"):
        CtsService(ml.rest).search(range=value)
    assert not respx.calls


@pytest.mark.asyncio
@respx.mock
async def test_invalid_execution_arguments_fail_before_io_sync_and_async():
    with MLClient() as ml:
        for kwargs in ({"v0": "override"}, {"variables": {}}, {"databse": "typo"}):
            with pytest.raises(TypeError):
                ml.eval.expression(xs.string("original"), **kwargs)
            with pytest.raises(TypeError):
                CtsService(ml.rest).search(**kwargs)
        with pytest.raises(TypeError, match="Expr"):
            ml.eval.expression("1")
        with pytest.raises(ValueError, match="output_type"):
            ml.eval.expression(fn.count([]), output_type=int)
    async with AsyncMLClient() as ml:
        with pytest.raises(TypeError, match="Expr"):
            await ml.eval.expression("1")
        with pytest.raises(ValueError, match="output_type"):
            await ml.eval.expression(fn.count([]), output_type=int)
        with pytest.raises(TypeError):
            await ml.eval.expression(fn.count([]), v0="override")
    assert not respx.calls


@pytest.mark.asyncio
@respx.mock
async def test_server_errors_propagate_without_local_version_gates():
    error = {
        "errorResponse": {
            "statusCode": 400,
            "status": "Bad Request",
            "messageCode": "XDMP-UNDFUN",
            "message": "Undefined function cts:document-root-query",
        },
    }
    respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(400, json=error["errorResponse"]),
    )
    expr = cts.document_root_query("x")
    with MLClient() as ml, pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
        ml.eval.expression(expr)
    async with AsyncMLClient() as ml:
        with pytest.raises(MarkLogicError, match="XDMP-UNDFUN"):
            await ml.eval.expression(expr)


@pytest.mark.asyncio
@respx.mock
async def test_eval_namespaces_belong_only_to_the_expression_invocation():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("integer", "text/plain", "1")),
    )
    with MLClient() as ml:
        ml.eval.expression(fn.count([1]), namespaces={"p": "urn:test"})
        assert 'declare namespace p = "urn:test";' in parse_qs(
            route.calls.last.request.content.decode(),
        )["xquery"][0]
        ml.eval.expression(fn.count([1]))
        assert "declare namespace p" not in parse_qs(
            route.calls.last.request.content.decode(),
        )["xquery"][0]
        with pytest.raises(TypeError, match="namespaces"):
            type(ml.eval)(ml.rest, namespaces={"p": "urn:test"})
    async with AsyncMLClient() as ml:
        await ml.eval.expression(fn.count([1]), namespaces={"p": "urn:test"})
        assert 'declare namespace p = "urn:test";' in parse_qs(
            route.calls.last.request.content.decode(),
        )["xquery"][0]
        await ml.eval.expression(fn.count([1]))
        assert "declare namespace p" not in parse_qs(
            route.calls.last.request.content.decode(),
        )["xquery"][0]
        with pytest.raises(TypeError, match="namespaces"):
            type(ml.eval)(ml.rest, namespaces={"p": "urn:test"})
