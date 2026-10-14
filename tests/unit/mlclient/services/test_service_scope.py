"""Shared service scopes route requests without changing the original service."""

import inspect
import json
from contextlib import AsyncExitStack
from dataclasses import FrozenInstanceError
from urllib.parse import parse_qs

import pytest
import respx

from mlclient import AsyncMLClient, MLClient
from mlclient.models import Document
from mlclient.services import EvalService, SearchScope, ServiceScope
from mlclient.xquery import fn


def test_scope_inherits_clears_and_remains_immutable():
    original = ServiceScope(database="catalog", txid="tx-1")
    inherited = original.overridden_by(ServiceScope(txid="tx-2"))
    assert inherited.request_params() == {"database": "catalog", "txid": "tx-2"}
    assert original.request_params() == {"database": "catalog", "txid": "tx-1"}
    assert original.overridden_by(ServiceScope(database=None)).request_params() == {
        "database": None,
        "txid": "tx-1",
    }
    assert ServiceScope().request_params() == {"database": None, "txid": None}
    assert original.overridden_by(None) is original
    with pytest.raises(FrozenInstanceError, match="cannot assign to field 'database'"):
        original.database = "another"


def test_rejects_search_scope_without_silently_dropping_filters():
    with (
        MLClient() as ml,
        pytest.raises(TypeError, match="scope must be a ServiceScope") as raised,
    ):
        EvalService(ml.rest, SearchScope(collection="products"))
    assert str(raised.value) == "scope must be a ServiceScope, got SearchScope"


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("operation", ["read", "read_stream", "write", "delete"])
@respx.mock
async def test_document_operations_use_scope_and_per_request_overrides(
    asynchronous,
    operation,
):
    route = respx.route(path="/v1/documents").respond(
        200,
        json={"name": "Coffee"},
    )
    async with AsyncExitStack() as stack:
        ml = (
            await stack.enter_async_context(AsyncMLClient())
            if asynchronous
            else stack.enter_context(MLClient())
        )
        original = ml.documents(database="catalog", txid="tx-1")
        narrowed = original(txid="tx-2")
        assert route.call_count == 0
        argument = (
            Document.create("/product.json", {"name": "Coffee"})
            if operation == "write"
            else "/product.json"
        )
        scenarios = [
            (narrowed, {}, "catalog", "tx-2"),
            (original, {}, "catalog", "tx-1"),
            (original, {"database": "archive"}, "archive", "tx-1"),
            (original, {"database": None, "txid": None}, None, None),
            (original(database=None, txid=None), {}, None, None),
            (ml.documents, {}, None, None),
        ]
        for service, overrides, database, txid in scenarios:
            result = getattr(service, operation)(argument, **overrides)
            if inspect.isawaitable(result):
                result = await result
            if operation == "read_stream":
                result = [doc async for doc in result] if asynchronous else list(result)
            params = route.calls.last.request.url.params
            assert params.get("database") == database
            assert params.get("txid") == txid


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "operation",
    ["xquery", "xqy", "javascript", "js", "file", "execute", "expression"],
)
@respx.mock
async def test_eval_entry_points_use_the_shared_scope(
    asynchronous, operation, tmp_path,
):
    route = respx.post("http://localhost:8000/v1/eval").respond(200, content=b"")
    file = tmp_path / "probe.xqy"
    file.write_text("1")
    async with AsyncExitStack() as stack:
        ml = (
            await stack.enter_async_context(AsyncMLClient())
            if asynchronous
            else stack.enter_context(MLClient())
        )
        original = ml.eval(database="catalog", txid="tx-1")
        narrowed = original(txid="tx-2")
        assert route.call_count == 0
        args = (
            [fn.string_length("coffee")]
            if operation == "expression"
            else [str(file)]
            if operation == "file"
            else []
            if operation == "execute"
            else ["1"]
        )
        code = {"xq": "1"} if operation == "execute" else {}
        scenarios = [
            (narrowed, {}, "catalog", "tx-2"),
            (original, {}, "catalog", "tx-1"),
            (original, {"database": "archive"}, "archive", "tx-1"),
            (original, {"database": None, "txid": None}, None, None),
            (original(database=None, txid=None), {}, None, None),
            (ml.eval, {}, None, None),
        ]
        for service, overrides, database, txid in scenarios:
            result = getattr(service, operation)(*args, **code, **overrides)
            if inspect.isawaitable(result):
                await result
            params = route.calls.last.request.url.params
            assert params.get("database") == database
            assert params.get("txid") == txid


@respx.mock
def test_eval_scope_keeps_external_variables_separate():
    route = respx.post("http://localhost:8000/v1/eval").respond(200, content=b"")
    with MLClient() as ml:
        ml.eval(database="catalog").xquery("$message", message="coffee")
    params = parse_qs(route.calls.last.request.content.decode())
    assert json.loads(params["vars"][0]) == {"message": "coffee"}
    assert route.calls.last.request.url.params["database"] == "catalog"
