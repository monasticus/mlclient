from __future__ import annotations

import httpx
import pytest
import respx
from pytest_mock import MockerFixture

from mlclient.clients import http_client as http_client_module
from mlclient.clients.http_client import AsyncHttpClient
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

RESOURCES = resources_utils.get_test_resources(__file__)


@pytest.mark.asyncio
async def test_connection():
    client = AsyncHttpClient()
    assert not client.is_connected()

    await client.connect()
    assert client.is_connected()

    await client.disconnect()
    assert not client.is_connected()


@pytest.mark.asyncio
async def test_context_mng():
    async with AsyncHttpClient() as client:
        assert client.is_connected()

    assert not client.is_connected()


@pytest.mark.asyncio
@respx.mock
async def test_request_when_disconnected():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(RESOURCES["test-get-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    client = AsyncHttpClient()

    assert not client.is_connected()
    resp = await client.get("/manage/v2/servers")
    assert not client.is_connected()
    assert resp.status_code == httpx.codes.OK
    assert resp.content == RESOURCES["test-get-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@pytest.mark.asyncio
@respx.mock
async def test_get():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(RESOURCES["test-get-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    async with AsyncHttpClient() as client:
        resp = await client.get("/manage/v2/servers")
    assert resp.status_code == httpx.codes.OK
    assert resp.content == RESOURCES["test-get-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@pytest.mark.asyncio
@respx.mock
async def test_get_with_customized_params_and_headers():
    response_body_json = RESOURCES["test-get-with-customized-params-response.json"][
        "json"
    ]
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("custom-header", "custom-value")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(response_body_json)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.mock_get()

    async with AsyncHttpClient() as client:
        resp = await client.get(
            "/manage/v2/servers",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.json() == response_body_json
    assert resp.headers.get("Content-Type") == "application/json; charset=UTF-8"


@pytest.mark.asyncio
@respx.mock
async def test_post():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(RESOURCES["test-post-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_post()

    async with AsyncHttpClient() as client:
        resp = await client.post("/manage/v2/databases/Documents")
    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.content == RESOURCES["test-post-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@pytest.mark.asyncio
@respx.mock
async def test_post_with_customized_params_and_headers_and_body_different_than_json():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": "()"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    async with AsyncHttpClient() as client:
        resp = await client.post(
            "/v1/eval",
            body={"xquery": "()"},
            params={"database": "Documents"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_post_with_customized_params_and_headers_and_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"operation": "clear-database"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.mock_post()

    async with AsyncHttpClient() as client:
        resp = await client.post(
            "/manage/v2/databases/Documents",
            body={"operation": "clear-database"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""
    assert resp.headers.get("Content-Type") == "application/json; charset=UTF-8"


@pytest.mark.asyncio
@respx.mock
async def test_put():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(RESOURCES["test-put-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_put()

    async with AsyncHttpClient() as client:
        resp = await client.put("/v1/documents")
    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.content == RESOURCES["test-put-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@pytest.mark.asyncio
@respx.mock
async def test_put_with_customized_params_and_headers_and_body_different_than_json():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("uri", "/doc.xml")
    ml_mocker.with_request_content_type("application/xml")
    ml_mocker.with_request_body("<document/>")
    ml_mocker.with_response_code(201)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    async with AsyncHttpClient() as client:
        resp = await client.put(
            "/v1/documents",
            body="<document/>",
            params={"database": "Documents", "uri": "/doc.xml"},
            headers={"Content-Type": "application/xml"},
        )
    assert resp.status_code == httpx.codes.CREATED
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_put_with_customized_params_and_headers_and_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("uri", "/doc.json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"document": {}})
    ml_mocker.with_response_code(201)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    async with AsyncHttpClient() as client:
        resp = await client.put(
            "/v1/documents",
            body={"document": {}},
            params={"database": "Documents", "uri": "/doc.json"},
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == httpx.codes.CREATED
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_delete():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncHttpClient() as client:
        resp = await client.delete("/manage/v2/databases/custom-db")
    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_delete_with_customized_params_and_headers():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("custom-header", "custom-value")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    async with AsyncHttpClient() as client:
        resp = await client.delete(
            "/manage/v2/databases/custom-db",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )
    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@pytest.mark.asyncio
@respx.mock
async def test_request_logs_warning_for_restart_location(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(
        "http://localhost:8002/manage/v2/servers/TestServer/properties",
    )
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"port": 8111})
    ml_mocker.with_response_code(202)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_header("Location", "/admin/v1/timestamp")
    ml_mocker.with_response_body(RESOURCES["restart-response.json"]["json"])
    ml_mocker.mock_put()
    logger_warning = mocker.patch.object(http_client_module.logger, "warning")

    async with AsyncHttpClient() as client:
        resp = await client.put(
            "/manage/v2/servers/TestServer/properties",
            body={"port": 8111},
            params={"group-id": "Default", "format": "json"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.status_code == httpx.codes.ACCEPTED
    logger_warning.assert_any_call(
        "MarkLogic accepted %s %s and initiated a restart; "
        "Location [%s]. Wait for restart completion before "
        "sending follow-up requests",
        "PUT",
        "/manage/v2/servers/TestServer/properties",
        "/admin/v1/timestamp",
    )


@pytest.mark.asyncio
@respx.mock
async def test_request_does_not_log_warning_for_non_restart_202(
    mocker: MockerFixture,
):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/forests")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"operation": "attach"})
    ml_mocker.with_response_code(202)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_header("Location", "/manage/v2/tickets/123")
    ml_mocker.with_response_body(
        RESOURCES["non-restart-accepted-response.json"]["json"],
    )
    ml_mocker.mock_put()
    logger_warning = mocker.patch.object(http_client_module.logger, "warning")

    async with AsyncHttpClient() as client:
        resp = await client.put(
            "/manage/v2/forests",
            body={"operation": "attach"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.status_code == httpx.codes.ACCEPTED
    logger_warning.assert_not_called()


@pytest.mark.asyncio
@respx.mock
async def test_request_logs_debug_response_retrieved(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("ok")
    ml_mocker.mock_get()
    logger_debug = mocker.patch.object(http_client_module.logger, "debug")

    async with AsyncHttpClient() as client:
        await client.get("/manage/v2/servers")

    debug_messages = [call.args[0] for call in logger_debug.call_args_list]
    assert "Response retrieved" in debug_messages


@pytest.mark.asyncio
@respx.mock
async def test_request_logs_debug_response_retrieved_no_body(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_response_header("X-Test", "1")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()
    logger_debug = mocker.patch.object(http_client_module.logger, "debug")

    async with AsyncHttpClient() as client:
        await client.delete("/manage/v2/databases/custom-db")

    debug_messages = [call.args[0] for call in logger_debug.call_args_list]
    assert "Response retrieved" in debug_messages


def test_properties():
    client = AsyncHttpClient(
        protocol="https",
        host="ml.example.com",
        port=8123,
        auth_method="digest",
        username="user",
        password="pass",
    )
    assert client.protocol == "https"
    assert client.host == "ml.example.com"
    assert client.port == 8123
    assert client.auth_method == "digest"
    assert client.username == "user"
    assert client.password == "pass"
    assert client.base_url == "https://ml.example.com:8123"
