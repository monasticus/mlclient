from __future__ import annotations

import json

import pytest
import pytest_asyncio
import respx

from mlclient import AsyncMLClient
from mlclient.exceptions import MarkLogicError
from tests.utils.ml_mockers import MLRespXMocker


@pytest_asyncio.fixture
async def ml():
    async with AsyncMLClient() as ml:
        yield ml


@pytest.mark.asyncio
@respx.mock
async def test_transaction_opens_eagerly(ml):
    _mock_open("sfr158-scratch")

    txn = await ml.transaction(database="sfr158-scratch")

    assert txn.id == "12345"
    assert txn.database == "sfr158-scratch"


@pytest.mark.asyncio
@respx.mock
async def test_transaction_raises_on_open_error(ml):
    error = {
        "errorResponse": {
            "statusCode": 400,
            "status": "Bad Request",
            "messageCode": "XDMP-XXX",
            "message": "boom",
        },
    }

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(json.dumps(error).encode())
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError) as err:
        await ml.transaction()

    assert err.value.args[0] == "[400 Bad Request] (XDMP-XXX) boom"


@pytest.mark.asyncio
@respx.mock
async def test_unpacks_to_txid_and_database(ml):
    _mock_open("sfr158-scratch")

    txn = await ml.transaction(database="sfr158-scratch")

    assert {**txn} == {"txid": "12345", "database": "sfr158-scratch"}


@pytest.mark.asyncio
@respx.mock
async def test_unpacks_to_txid_only_without_database(ml):
    _mock_open()

    txn = await ml.transaction()

    assert {**txn} == {"txid": "12345"}
    assert txn["database"] is None


@pytest.mark.asyncio
@respx.mock
async def test_getitem_rejects_unknown_key(ml):
    _mock_open()

    txn = await ml.transaction()

    with pytest.raises(KeyError):
        txn["unknown"]


@pytest.mark.asyncio
@respx.mock
async def test_status_returns_parsed(ml):
    _mock_open("sfr158-scratch")
    body = {"transaction-status": {"transaction-id": "12345"}}

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("database", "sfr158-scratch")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(body)
    ml_mocker.mock_get()

    txn = await ml.transaction(database="sfr158-scratch")

    assert await txn.status() == body


@pytest.mark.asyncio
@respx.mock
async def test_status_raises_on_error(ml):
    _mock_open()
    error = {
        "errorResponse": {
            "statusCode": 404,
            "status": "Not Found",
            "messageCode": "XDMP-NOTXN",
            "message": "no such transaction",
        },
    }

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(json.dumps(error).encode())
    ml_mocker.mock_get()

    txn = await ml.transaction()

    with pytest.raises(MarkLogicError) as err:
        await txn.status()

    assert err.value.args[0] == "[404 Not Found] (XDMP-NOTXN) no such transaction"


@pytest.mark.asyncio
@respx.mock
async def test_commit(ml):
    _mock_open("sfr158-scratch")
    _mock_finish("commit", "sfr158-scratch")

    txn = await ml.transaction(database="sfr158-scratch")

    assert await txn.commit() is None


@pytest.mark.asyncio
@respx.mock
async def test_rollback(ml):
    _mock_open()
    _mock_finish("rollback")

    txn = await ml.transaction()

    assert await txn.rollback() is None


@pytest.mark.asyncio
@respx.mock
async def test_commit_raises_on_error(ml):
    _mock_open()
    error = {
        "errorResponse": {
            "statusCode": 400,
            "status": "Bad Request",
            "messageCode": "XDMP-XXX",
            "message": "boom",
        },
    }

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(json.dumps(error).encode())
    ml_mocker.mock_post()

    txn = await ml.transaction()

    with pytest.raises(MarkLogicError) as err:
        await txn.commit()

    assert err.value.args[0] == "[400 Bad Request] (XDMP-XXX) boom"


@pytest.mark.asyncio
@respx.mock
async def test_context_manager_commits_on_success(ml):
    _mock_open("sfr158-scratch")
    _mock_finish("commit", "sfr158-scratch")

    async with await ml.transaction(database="sfr158-scratch") as txn:
        assert txn.id == "12345"


@pytest.mark.asyncio
@respx.mock
async def test_context_manager_rolls_back_on_error(ml):
    _mock_open()
    _mock_finish("rollback")

    with pytest.raises(RuntimeError, match="boom"):
        async with await ml.transaction():
            raise RuntimeError("boom")


def _mock_open(database: str | None = None):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions")
    if database is not None:
        ml_mocker.with_request_param("database", database)
    ml_mocker.with_response_code(303)
    ml_mocker.with_response_header("Location", "/v1/transactions/12345")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()


def _mock_finish(result: str, database: str | None = None):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/transactions/12345")
    ml_mocker.with_request_param("result", result)
    if database is not None:
        ml_mocker.with_request_param("database", database)
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()
