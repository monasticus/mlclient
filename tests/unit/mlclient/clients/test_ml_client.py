from __future__ import annotations

import httpx
import respx
from pytest_mock import MockerFixture

from mlclient import MLClient
from mlclient.api.rest_api import RestApi
from mlclient.calls import DatabasesGetCall, TimestampGetCall
from mlclient.clients import ml_client as ml_client_module
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import DocumentsService
from mlclient.services.eval import EvalService
from tests.utils.ml_mockers import MLRespXMocker


def test_properties_delegate_to_http_client():
    ml = MLClient(
        protocol="https",
        host="ml.example.com",
        port=8123,
        auth_method="digest",
        username="user",
        password="pass",
    )
    assert ml.http.protocol == "https"
    assert ml.http.host == "ml.example.com"
    assert ml.http.port == 8123
    assert ml.http.auth_method == "digest"
    assert ml.http.username == "user"
    assert ml.http.password == "pass"
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

    kwargs = restart_waiter_cls.call_args.kwargs
    assert kwargs["protocol"] == "https"
    assert kwargs["host"] == "example.com"
    assert isinstance(kwargs["auth"], httpx.BasicAuth)
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
