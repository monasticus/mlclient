from __future__ import annotations

import httpx
import pytest
import respx
from httpx_retries import Retry
from pytest_mock import MockerFixture

from mlclient import MLClient
from mlclient.api.rest_api import RestApi
from mlclient.calls import DatabasesGetCall, TimestampGetCall
from mlclient.clients import ml_client as ml_client_module
from mlclient.http_config import DEFAULT_RETRY_STRATEGY, HTTPConfig
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import DocumentsService
from mlclient.services.eval import EvalService
from tests.utils.ml_mockers import MLRespXMocker


def test_properties_delegate_to_http_client():
    ml = MLClient(
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
    ml = MLClient()
    assert isinstance(ml.rest, RestApi)


def test_documents_property():
    ml = MLClient()
    assert isinstance(ml.documents, DocumentsService)


def test_eval_property():
    ml = MLClient()
    assert isinstance(ml.eval, EvalService)


def test_parser_returns_ml_response_parser():
    ml = MLClient()
    assert ml.parser is MLResponseParser


@respx.mock
def test_manage_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.manage.call(DatabasesGetCall())

    assert resp.status_code == 200


@respx.mock
def test_admin_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    with MLClient() as ml:
        resp = ml.admin.call(TimestampGetCall())

    assert resp.status_code == 200


@respx.mock
def test_admin_uses_main_port_when_already_8001():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    with MLClient(port=8001) as ml:
        resp = ml.admin.get_timestamp()

    assert resp.status_code == 200


@respx.mock
def test_admin_uses_port_8001_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    with MLClient(port=8000) as ml:
        resp = ml.admin.get_timestamp()

    assert resp.status_code == 200


@respx.mock
def test_manage_uses_main_port_when_already_8002():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    with MLClient(port=8002) as ml:
        resp = ml.manage.databases.get_list()

    assert resp.status_code == 200


@respx.mock
def test_manage_uses_port_8002_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    with MLClient(port=8000) as ml:
        resp = ml.manage.databases.get_list()

    assert resp.status_code == 200


def test_config_supersedes_connection_kwargs():
    config = HTTPConfig.resolve(host="resolved.example.com", port=8123)

    ml = MLClient(host="ignored.example.com", port=9999, config=config)

    assert ml.http.config is config
    assert ml.http.base_url == "http://resolved.example.com:8123"


@respx.mock
def test_derived_secondaries_use_injected_primary_host():
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
    with MLClient(config=config) as ml:
        assert ml.manage.databases.get_list().status_code == 200
        assert ml.admin.get_timestamp().status_code == 200


@respx.mock
def test_only_manage_config_given_admin_still_derived():
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
    with MLClient(port=8000, manage_config=manage_config) as ml:
        manage_resp = ml.manage.databases.get_list()
        admin_resp = ml.admin.get_timestamp()

    assert manage_resp.status_code == 200
    assert admin_resp.status_code == 200


@respx.mock
def test_only_admin_config_given_manage_still_derived():
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
    with MLClient(port=8000, admin_config=admin_config) as ml:
        admin_resp = ml.admin.get_timestamp()
        manage_resp = ml.manage.databases.get_list()

    assert admin_resp.status_code == 200
    assert manage_resp.status_code == 200


@respx.mock
def test_both_manage_and_admin_configs_given():
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
    with MLClient(
        port=8000,
        manage_config=manage_config,
        admin_config=admin_config,
    ) as ml:
        manage_resp = ml.manage.databases.get_list()
        admin_resp = ml.admin.get_timestamp()

    assert manage_resp.status_code == 200
    assert admin_resp.status_code == 200


@respx.mock
def test_healthcheck_uses_port_7997_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    with MLClient(port=8000) as ml:
        assert ml.healthcheck() is True


@respx.mock
def test_healthcheck_uses_main_port_when_already_7997():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    with MLClient(port=7997) as ml:
        assert ml.healthcheck() is True


@respx.mock
def test_healthcheck_returns_false_on_unhealthy_status():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    with MLClient(port=8000) as ml:
        assert ml.healthcheck() is False
    assert route.call_count == 1


@respx.mock
def test_healthcheck_uses_injected_health_config():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://health.example.com:9997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    health_config = HTTPConfig.resolve(host="health.example.com", port=9997, auth=None)
    with MLClient(port=8000, health_config=health_config) as ml:
        assert ml.healthcheck() is True


@respx.mock
def test_healthcheck_derived_connection_sends_no_authorization():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    with MLClient(protocol="https", port=8000, auth="basic") as ml:
        assert ml.healthcheck() is True
    assert "Authorization" not in route.calls.last.request.headers


@respx.mock
def test_healthcheck_returns_false_with_injected_config_on_server_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://health.example.com:9997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    route = ml_mocker.mock_head()

    health_config = HTTPConfig.resolve(host="health.example.com", port=9997, auth=None)
    with MLClient(port=8000, health_config=health_config) as ml:
        assert ml.healthcheck() is False
    assert route.call_count == 1


@respx.mock
def test_healthcheck_propagates_explicit_retry_from_injected_config():
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
    with MLClient(port=8000, health_config=health_config) as ml:
        assert ml.healthcheck() is False
    assert route.call_count == 2


@respx.mock
def test_healthcheck_raises_on_client_error_instead_of_reporting_unhealthy():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(401)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    with MLClient(port=8000) as ml, pytest.raises(httpx.HTTPStatusError):
        ml.healthcheck()


@respx.mock
def test_secondary_clients_connect_and_disconnect_with_main():
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

    ml = MLClient(port=8000)
    # Force creation of secondary clients before connecting
    _ = ml.manage
    _ = ml.admin

    ml.connect()
    resp_manage = ml.manage.databases.get_list()
    resp_admin = ml.admin.get_timestamp()
    assert resp_manage.status_code == 200
    assert resp_admin.status_code == 200

    ml.disconnect()
    assert not ml.is_connected()


def test_wait_for_restart_builds_restart_waiter_and_uses_default_retry(
    mocker: MockerFixture,
):
    waiter = mocker.MagicMock()
    restart_waiter_cls = mocker.patch.object(
        ml_client_module,
        "RestartWaiter",
        autospec=True,
        return_value=waiter,
    )

    with MLClient(
        protocol="https",
        host="example.com",
        port=8123,
        username="user",
        password="pass",
    ) as ml:
        response = httpx.Response(202)
        ml.wait_for_restart(
            response,
            timeout=12.0,
            poll_interval=0.5,
        )

    config = restart_waiter_cls.call_args.args[0]
    assert config.protocol == "https"
    assert config.host == "example.com"
    assert isinstance(config.auth, httpx.DigestAuth)
    assert config.retry is DEFAULT_RETRY_STRATEGY
    waiter.wait_for_restart_completion.assert_called_once_with(
        response,
        timeout=12.0,
        poll_interval=0.5,
        retry=ml_client_module.RESTART_RETRY_STRATEGY,
    )


def test_wait_for_restart_uses_custom_retry(
    mocker: MockerFixture,
):
    waiter = mocker.MagicMock()
    restart_waiter_cls = mocker.patch.object(
        ml_client_module,
        "RestartWaiter",
        autospec=True,
        return_value=waiter,
    )
    custom_retry = object()

    with MLClient() as ml:
        ml.wait_for_restart(
            response=None,
            timeout=12.0,
            poll_interval=0.5,
            retry=custom_retry,
        )

    assert restart_waiter_cls.called
    waiter.wait_for_restart_completion.assert_called_once_with(
        None,
        timeout=12.0,
        poll_interval=0.5,
        retry=custom_retry,
    )
