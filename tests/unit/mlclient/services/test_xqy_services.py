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
from mlclient.functions import Expr, cts, fn, xpath, xs
from mlclient.multipart import MultipartPart, encode_multipart_mixed
from mlclient.responses import MLResponseParser
from mlclient.services import (
    AsyncCtsService,
    AsyncFnService,
    AsyncXdmpService,
    CtsService,
    FnService,
    XdmpService,
)


def _response(*items):
    parts = [
        MultipartPart({"Content-Type": mime, "X-Primitive": primitive}, value.encode())
        for primitive, mime, value in items
    ]
    body, content_type = encode_multipart_mixed(parts)
    return httpx.Response(200, content=body, headers={"Content-Type": content_type})


@pytest.mark.parametrize(
    "items",
    [
        [],
        [("array-node", "application/json", "[1,2]")],
        [("integer", "text/plain", "1"), ("integer", "text/plain", "2")],
    ],
)
@respx.mock
def test_eval_preserves_outer_sequence(items):
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(*items),
    )
    with MLClient() as ml:
        result = ml.eval.expression(fn.count([]))
    assert result == ([] if not items else [[1, 2]] if len(items) == 1 else [1, 2])
    assert route.call_count == 1


@respx.mock
def test_typed_items_and_raw_overrides_preserve_legacy_eval_behavior():
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
    assert isinstance(MLResponseParser.parse(response), float)
    assert MLResponseParser.parse_sequence(response) == [Decimal(items[0][2])]
    with pytest.raises(ValueError, match="output_type"):
        MLResponseParser.parse_sequence(response, int)


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
        assert ml.eval.expression(fn.count([])) == [7]
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
        assert ml.eval.expression(expr, database="test", txid="123", timeout=2) == [
            Decimal("1.234567890123456789"),
        ]
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
        assert await ml.eval.expression(xs.integer(1)) == [1]
        service = AsyncCtsService(ml.rest)
        assert await service.search(query=cts.true_query(), range=1) == [1]
        assert await service.uris(range=(1, 2)) == [1]
        assert await service.values(cts.uri_reference(), range=1) == [1]
        assert await service.estimate(maximum=1) == 1
        assert await AsyncFnService(ml.rest).count([1], maximum=1) == 1
        route.mock(return_value=_response(("boolean", "text/plain", "true")))
        assert await AsyncFnService(ml.rest).exists([1]) is True
        assert await AsyncFnService(ml.rest).empty([]) is True
        assert await AsyncXdmpService(ml.rest).exists(xpath("/")) is True


@respx.mock
def test_sync_conveniences_return_lists_or_single_aggregates():
    route = respx.post("http://localhost:8000/v1/eval").mock(
        return_value=_response(("integer", "text/plain", "1")),
    )
    with MLClient() as ml:
        service = CtsService(ml.rest)
        assert not hasattr(service, "word_query")
        assert service.search(range=1) == [1]
        assert service.uris(range=(1, 2)) == [1]
        assert service.values(cts.uri_reference()) == [1]
        assert service.estimate() == 1
        assert FnService(ml.rest).count([1]) == 1
        route.mock(return_value=_response(("boolean", "text/plain", "true")))
        assert FnService(ml.rest).exists([1]) is True
        assert FnService(ml.rest).empty([]) is True
        assert XdmpService(ml.rest).exists(xpath("/")) is True
        route.mock(return_value=_response())
        with pytest.raises(ValueError, match="exactly one"):
            FnService(ml.rest).count([])


@pytest.mark.parametrize("value", [True, 1.5, (1,), (1, 2, 3), [1, 2]])
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
            await AsyncFnService(ml.rest).count([], v0="override")
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
