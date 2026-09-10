from __future__ import annotations

import httpx
import pytest
import respx
from httpx_retries import Retry
from pytest_mock import MockerFixture

from mlclient.api.rest_api import AsyncRestApi
from mlclient.calls import DatabasesGetCall, TimestampGetCall
from mlclient.clients import http_client as http_client_module
from mlclient.clients import ml_client as ml_client_module
from mlclient.clients.ml_client import AsyncMLClient
from mlclient.connection import CloudConfig
from mlclient.exceptions import MarkLogicError
from mlclient.http_config import DEFAULT_RETRY_STRATEGY, HTTPConfig
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import AsyncDocumentsService
from mlclient.services.eval import AsyncEvalService
from mlclient.services.logs import AsyncLogsService
from tests.utils.ml_mockers import MLRespXMocker


def test_properties_delegate_to_http_client():
    ml = AsyncMLClient(
        protocol="https",
        host="ml.example.com",
        port=8123,
        auth="digest",
        username="user",
        password="pass",
    )
    assert ml.http.config.protocol == "https"
    assert ml.http.config.host == "ml.example.com"
    assert ml.http.config.port == 8123
    assert isinstance(ml.http.config.auth, httpx.DigestAuth)
    assert ml.http.config.username == "user"
    assert ml.http.config.password == "pass"
    assert ml.http.base_url == "https://ml.example.com:8123"


def test_rest_property():
    ml = AsyncMLClient()
    assert isinstance(ml.rest, AsyncRestApi)


def test_documents_property():
    ml = AsyncMLClient()
    assert isinstance(ml.documents, AsyncDocumentsService)


def test_eval_property():
    ml = AsyncMLClient()
    assert isinstance(ml.eval, AsyncEvalService)


def test_logs_property():
    ml = AsyncMLClient()
    assert isinstance(ml.logs, AsyncLogsService)


def test_parser_returns_ml_response_parser():
    ml = AsyncMLClient()
    assert ml.parser is MLResponseParser


@pytest.mark.asyncio
@respx.mock
async def test_manage_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        resp = await ml.manage.call(DatabasesGetCall())

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_admin_custom_call():
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
async def test_admin_uses_main_port_when_already_8001():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    async with AsyncMLClient(port=8001) as ml:
        resp = await ml.admin.get_timestamp()

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_admin_uses_port_8001_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    async with AsyncMLClient(port=8000) as ml:
        resp = await ml.admin.get_timestamp()

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_manage_uses_main_port_when_already_8002():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    async with AsyncMLClient(port=8002) as ml:
        resp = await ml.manage.databases.get_list()

    assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_manage_uses_port_8002_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    async with AsyncMLClient(port=8000) as ml:
        resp = await ml.manage.databases.get_list()

    assert resp.status_code == 200


def test_config_supersedes_connection_kwargs():
    config = HTTPConfig.resolve(host="resolved.example.com", port=8123)

    ml = AsyncMLClient(host="ignored.example.com", port=9999, config=config)

    assert ml.http.config is config
    assert ml.http.base_url == "http://resolved.example.com:8123"


@pytest.mark.asyncio
@respx.mock
async def test_derived_secondaries_use_injected_primary_host():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://primary.example.com:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    ml_mocker.with_url("http://primary.example.com:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    config = HTTPConfig.resolve(host="primary.example.com", port=8100)
    async with AsyncMLClient(config=config) as ml:
        assert (await ml.manage.databases.get_list()).status_code == 200
        assert (await ml.admin.get_timestamp()).status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_only_manage_config_given_admin_still_derived():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://manage.example.com:9002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    manage_config = HTTPConfig.resolve(host="manage.example.com", port=9002)
    async with AsyncMLClient(port=8000, manage_config=manage_config) as ml:
        manage_resp = await ml.manage.databases.get_list()
        admin_resp = await ml.admin.get_timestamp()

    assert manage_resp.status_code == 200
    assert admin_resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_only_admin_config_given_manage_still_derived():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://admin.example.com:9001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    admin_config = HTTPConfig.resolve(host="admin.example.com", port=9001)
    async with AsyncMLClient(port=8000, admin_config=admin_config) as ml:
        admin_resp = await ml.admin.get_timestamp()
        manage_resp = await ml.manage.databases.get_list()

    assert admin_resp.status_code == 200
    assert manage_resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_both_manage_and_admin_configs_given():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://manage.example.com:9002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    ml_mocker.with_url("http://admin.example.com:9001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    manage_config = HTTPConfig.resolve(host="manage.example.com", port=9002)
    admin_config = HTTPConfig.resolve(host="admin.example.com", port=9001)
    async with AsyncMLClient(
        port=8000,
        manage_config=manage_config,
        admin_config=admin_config,
    ) as ml:
        manage_resp = await ml.manage.databases.get_list()
        admin_resp = await ml.admin.get_timestamp()

    assert manage_resp.status_code == 200
    assert admin_resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_version_from_eval():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "12.0.1")
    ml_mocker.mock_post()

    async with AsyncMLClient() as ml:
        assert (await ml.version()).parts == (12, 0, 1, None)


@pytest.mark.asyncio
@respx.mock
async def test_version_falls_back_to_manage_when_eval_forbidden():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"version": "12.0.1"})
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        assert (await ml.version()).parts == (12, 0, 1, None)


@pytest.mark.asyncio
@respx.mock
async def test_version_falls_back_to_admin_when_manage_forbidden():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:8001/admin/v1/server-config")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/xml")
    ml_mocker.with_response_body(
        '<host xmlns="http://marklogic.com/manage"><version>12.0.1</version></host>',
    )
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        assert (await ml.version()).parts == (12, 0, 1, None)


@pytest.mark.asyncio
@respx.mock
async def test_version_reraises_eval_error_when_all_sources_fail():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:8001/admin/v1/server-config")
    ml_mocker.with_response_code(403)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    async with AsyncMLClient() as ml:
        with pytest.raises(MarkLogicError):
            await ml.version()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12.0.1", (12, 0, 1, None)),
        ("10.0-9.5", (10, 0, 9, 5)),
        ("12.0", (12, 0, None, None)),
        (" 12.0.1 ", (12, 0, 1, None)),
    ],
)
@respx.mock
async def test_version_normalizes_release_formats(raw, expected):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", raw)
    ml_mocker.mock_post()

    async with AsyncMLClient(retry=Retry(total=0)) as ml:
        assert (await ml.version()).parts == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", ["unknown", "error 12.0.1", "12", ""])
@respx.mock
async def test_version_rejects_invalid_eval_result(raw):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", raw)
    ml_mocker.mock_post()

    async with AsyncMLClient(retry=Retry(total=0)) as ml:
        with pytest.raises(ValueError, match="Invalid MarkLogic version"):
            _ = await ml.version()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "manage_body",
    ["not json", "{}", "[]", '{"version": null}', '{"version": "unknown"}'],
)
@respx.mock
async def test_version_skips_invalid_manage_response(manage_body):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(manage_body)
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:8001/admin/v1/server-config")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(
        '<m:host xmlns:m="http://marklogic.com/manage"><m:version>12.0</m:version></m:host>',
    )
    ml_mocker.mock_get()

    async with AsyncMLClient(retry=Retry(total=0)) as ml:
        assert (await ml.version()).parts == (12, 0, None, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "admin_body",
    [
        "not xml",
        "<host/>",
        "<host><version/></host>",
        "<host><version>unknown</version></host>",
    ],
)
@respx.mock
async def test_version_preserves_eval_error_when_fallbacks_unusable(admin_body):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_get_side_effect(httpx.ConnectError("Manage unavailable"))

    ml_mocker.with_url("http://localhost:8001/admin/v1/server-config")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(admin_body)
    ml_mocker.mock_get()

    async with AsyncMLClient(retry=Retry(total=0)) as ml:
        with pytest.raises(MarkLogicError):
            _ = await ml.version()


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_uses_port_7997_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    async with AsyncMLClient(port=8000) as ml:
        assert await ml.healthcheck() is True


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_uses_main_port_when_already_7997():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    async with AsyncMLClient(port=7997) as ml:
        assert await ml.healthcheck() is True


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_returns_false_on_unhealthy_status():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    async with AsyncMLClient(port=8000) as ml:
        assert await ml.healthcheck() is False
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_defaults_to_health_timeout():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    async with AsyncMLClient(port=8000) as ml:
        await ml.healthcheck()
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 5.0,
        "read": 5.0,
        "write": 5.0,
        "pool": 5.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_per_call_timeout_reaches_transport():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    async with AsyncMLClient(port=8000) as ml:
        await ml.healthcheck(timeout=2)
    assert route.calls.last.request.extensions["timeout"] == {
        "connect": 2.0,
        "read": 2.0,
        "write": 2.0,
        "pool": 2.0,
    }


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_uses_injected_health_config():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://health.example.com:9997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    health_config = HTTPConfig.resolve(host="health.example.com", port=9997, auth=None)
    async with AsyncMLClient(port=8000, health_config=health_config) as ml:
        assert await ml.healthcheck() is True


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_derived_connection_sends_no_authorization():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    async with AsyncMLClient(protocol="https", port=8000, auth="basic") as ml:
        assert await ml.healthcheck() is True
    assert "Authorization" not in route.calls.last.request.headers


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_returns_false_with_injected_config_on_server_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://health.example.com:9997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    health_config = HTTPConfig.resolve(host="health.example.com", port=9997, auth=None)
    async with AsyncMLClient(port=8000, health_config=health_config) as ml:
        assert await ml.healthcheck() is False
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_propagates_explicit_retry_from_injected_config():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://health.example.com:9997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    health_config = HTTPConfig.resolve(
        host="health.example.com",
        port=9997,
        auth=None,
        retry=Retry(total=1, backoff_factor=0),
    )
    async with AsyncMLClient(port=8000, health_config=health_config) as ml:
        assert await ml.healthcheck() is False
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_raises_on_client_error_instead_of_reporting_unhealthy():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(401)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    async with AsyncMLClient(port=8000) as ml:
        with pytest.raises(httpx.HTTPStatusError):
            await ml.healthcheck()


@pytest.mark.parametrize("port", [8000, 7997])
@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_derived_config_overrides_auth_and_retry(port):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://localhost:7997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    async with AsyncMLClient(
        protocol="https",
        port=port,
        auth="basic",
        retry=Retry(total=2),
    ) as ml:
        assert await ml.healthcheck() is False

    assert route.call_count == 1
    assert "Authorization" not in route.calls.last.request.headers


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_preserves_injected_auth_and_explicit_default_retry(mocker):
    mocker.patch.object(Retry, "asleep")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://health.example.com:9997/")
    ml_mocker.with_request_header("Authorization", "Basic cmVhZGVyOnB3")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
    config = HTTPConfig.resolve(
        protocol="https",
        host="health.example.com",
        port=9997,
        auth="basic",
        username="reader",
        password="pw",
        retry=DEFAULT_RETRY_STRATEGY,
    )

    async with AsyncMLClient(health_config=config) as ml:
        assert await ml.healthcheck() is False

    assert route.call_count == 6


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_uses_no_retry_for_cloned_unspecified_config():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
    config = HTTPConfig.resolve().clone(port=7997, auth=None)

    async with AsyncMLClient(health_config=config) as ml:
        assert await ml.healthcheck() is False

    assert route.call_count == 1


@pytest.mark.parametrize("injected", [False, True])
@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_cloud_uses_no_retry_and_preserves_gateway(injected):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://x.marklogic.cloud:443/token")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"access_token": "tok-1"})
    ml_mocker.mock_post()
    ml_mocker.with_url("https://x.marklogic.cloud:443/ml/example/manage/")
    ml_mocker.with_request_header("Authorization", "Bearer tok-1")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()
    config = HTTPConfig.resolve(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )

    async with AsyncMLClient(
        config=config,
        health_config=config if injected else None,
    ) as ml:
        assert await ml.healthcheck() is False

    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_sessions_open_on_requests_and_reopen_with_cached_apis(mocker):
    opened = mocker.spy(http_client_module, "AsyncClient")
    closed = mocker.spy(httpx.AsyncClient, "aclose")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()
    ml = AsyncMLClient()
    manage, admin = ml.manage, ml.admin
    assert opened.call_count == 0

    for cycle in range(2):
        async with ml:
            await ml.connect()
            assert opened.call_count == cycle * 4 + 1
            await manage.call(DatabasesGetCall())
            assert opened.call_count == cycle * 4 + 2
            await admin.call(TimestampGetCall())
            assert opened.call_count == cycle * 4 + 3
            assert await ml.healthcheck()
            assert await ml.healthcheck()
            assert opened.call_count == cycle * 4 + 4
        assert closed.call_count == (cycle + 1) * 4
        assert not ml.is_connected()


@pytest.mark.asyncio
@respx.mock
async def test_cached_auxiliary_uses_ad_hoc_session_after_context_exception(mocker):
    opened = mocker.spy(http_client_module, "AsyncClient")
    closed = mocker.spy(httpx.AsyncClient, "aclose")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_get_side_effect([ValueError("failure"), httpx.Response(200)])
    ml = AsyncMLClient()
    admin = ml.admin

    with pytest.raises(ValueError, match="failure"):
        async with ml:
            await admin.call(TimestampGetCall())
    assert opened.call_count == closed.call_count == 2
    assert not ml.is_connected()
    await admin.call(TimestampGetCall())
    assert opened.call_count == 3
    assert opened.spy_return.is_closed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tier", "call"),
    [("manage", DatabasesGetCall()), ("admin", TimestampGetCall())],
)
@respx.mock
async def test_matching_injected_config_reuses_primary_session(mocker, tier, call):
    opened = mocker.spy(http_client_module, "AsyncClient")
    closed = mocker.spy(httpx.AsyncClient, "aclose")
    config = HTTPConfig.resolve(port=9002, auth="basic")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:9002" + call.endpoint)
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()

    async with AsyncMLClient(config=config, **{f"{tier}_config": config.clone()}) as ml:
        await getattr(ml, tier).call(call)
        assert opened.call_count == 1
    assert closed.call_count == 1



@pytest.mark.asyncio
@respx.mock
async def test_secondary_clients_connect_and_disconnect_with_main():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    ml = AsyncMLClient(port=8000)
    # Force creation of secondary clients before connecting
    _ = ml.manage
    _ = ml.admin

    await ml.connect()
    resp_manage = await ml.manage.databases.get_list()
    resp_admin = await ml.admin.get_timestamp()
    assert resp_manage.status_code == 200
    assert resp_admin.status_code == 200

    await ml.disconnect()
    assert not ml.is_connected()


@pytest.mark.asyncio
async def test_wait_for_restart_builds_restart_waiter_and_uses_default_retry(
    mocker: MockerFixture,
):
    waiter = mocker.MagicMock()
    waiter.async_wait_for_restart_completion = mocker.AsyncMock()
    restart_waiter_cls = mocker.patch.object(
        ml_client_module,
        "RestartWaiter",
        autospec=True,
        return_value=waiter,
    )

    async with AsyncMLClient(
        protocol="https",
        host="example.com",
        port=8123,
        username="user",
        password="pass",
    ) as ml:
        response = httpx.Response(202)
        await ml.wait_for_restart(
            response,
            timeout=12.0,
            poll_interval=0.5,
        )

    config = restart_waiter_cls.call_args.args[0]
    assert config.protocol == "https"
    assert config.host == "example.com"
    assert isinstance(config.auth, httpx.DigestAuth)
    assert config.retry is DEFAULT_RETRY_STRATEGY
    waiter.async_wait_for_restart_completion.assert_called_once_with(
        response,
        timeout=12.0,
        poll_interval=0.5,
        retry=ml_client_module.RESTART_RETRY_STRATEGY,
    )


@pytest.mark.asyncio
async def test_wait_for_restart_uses_custom_retry(
    mocker: MockerFixture,
):
    waiter = mocker.MagicMock()
    waiter.async_wait_for_restart_completion = mocker.AsyncMock()
    restart_waiter_cls = mocker.patch.object(
        ml_client_module,
        "RestartWaiter",
        autospec=True,
        return_value=waiter,
    )
    custom_retry = object()

    async with AsyncMLClient() as ml:
        await ml.wait_for_restart(
            response=None,
            timeout=12.0,
            poll_interval=0.5,
            retry=custom_retry,
        )

    assert restart_waiter_cls.called
    waiter.async_wait_for_restart_completion.assert_called_once_with(
        None,
        timeout=12.0,
        poll_interval=0.5,
        retry=custom_retry,
    )
