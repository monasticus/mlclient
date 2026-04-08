from pathlib import Path

import httpx
import pytest
import respx

from mlclient import AsyncMLClient
from mlclient.calls import TimestampGetCall
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker


@pytest.mark.asyncio
@respx.mock
async def test_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.call(TimestampGetCall())

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_get_timestamp():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-timestamp.txt",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_content_type("text/plain; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.get_timestamp()

    assert resp.status_code == httpx.codes.OK
    assert "2024-01-15T10:30:00.000Z" in resp.text


@pytest.mark.asyncio
@respx.mock
async def test_get_server_config():
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "test-get-server-config.xml",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/server-config")
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.admin.get_server_config()

    assert resp.status_code == httpx.codes.OK
    assert "server-config" in resp.text
    assert "localhost" in resp.text
