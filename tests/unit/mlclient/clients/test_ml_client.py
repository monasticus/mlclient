from __future__ import annotations

import httpx
import respx
from pytest_mock import MockerFixture

from mlclient import MLClient
from mlclient.api.rest_api import RestApi
from mlclient.calls import DatabasesGetCall
from mlclient.clients import http_client as http_client_module
from mlclient.clients import ml_client as ml_client_module
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import DocumentsService
from mlclient.services.eval import EvalService
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

RESOURCES = resources_utils.get_test_resources(__file__)


def test_connection():
    client = MLClient()
    assert not client.is_connected()

    client.connect()
    assert client.is_connected()

    client.disconnect()
    assert not client.is_connected()


def test_context_mng():
    with MLClient() as client:
        assert client.is_connected()

    assert not client.is_connected()


@respx.mock
def test_request_when_disconnected():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(RESOURCES["test-get-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    client = MLClient()

    assert not client.is_connected()
    resp = client.http.get("/manage/v2/servers")
    assert not client.is_connected()
    assert resp.status_code == httpx.codes.OK
    assert resp.content == RESOURCES["test-get-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_get():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(RESOURCES["test-get-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_get()

    with MLClient() as client:
        resp = client.http.get("/manage/v2/servers")
    assert resp.status_code == httpx.codes.OK
    assert resp.content == RESOURCES["test-get-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_get_with_customized_params_and_headers():
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

    with MLClient() as client:
        resp = client.http.get(
            "/manage/v2/servers",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.json() == response_body_json
    assert resp.headers.get("Content-Type") == "application/json; charset=UTF-8"


@respx.mock
def test_post():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(RESOURCES["test-post-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_post()

    with MLClient() as client:
        resp = client.http.post("/manage/v2/databases/Documents")
    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.content == RESOURCES["test-post-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_post_with_customized_params_and_headers_and_body_different_than_json():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body({"xquery": "()"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_post()

    with MLClient() as client:
        resp = client.http.post(
            "/v1/eval",
            body={"xquery": "()"},
            params={"database": "Documents"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""


@respx.mock
def test_post_with_customized_params_and_headers_and_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/Documents")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"operation": "clear-database"})
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.mock_post()

    with MLClient() as client:
        resp = client.http.post(
            "/manage/v2/databases/Documents",
            body={"operation": "clear-database"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == httpx.codes.OK
    assert resp.content == b""
    assert resp.headers.get("Content-Type") == "application/json; charset=UTF-8"


@respx.mock
def test_put():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_body(RESOURCES["test-put-response.xml"]["bytes"])
    ml_mocker.with_response_content_type("application/xml; charset=UTF-8")
    ml_mocker.mock_put()

    with MLClient() as client:
        resp = client.http.put("/v1/documents")
    assert resp.status_code == httpx.codes.BAD_REQUEST
    assert resp.content == RESOURCES["test-put-response.xml"]["bytes"]
    assert resp.headers.get("Content-Type") == "application/xml; charset=UTF-8"


@respx.mock
def test_put_with_customized_params_and_headers_and_body_different_than_json():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("uri", "/doc.xml")
    ml_mocker.with_request_content_type("application/xml")
    ml_mocker.with_request_body("<document/>")
    ml_mocker.with_response_code(201)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    with MLClient() as client:
        resp = client.http.put(
            "/v1/documents",
            body="<document/>",
            params={"database": "Documents", "uri": "/doc.xml"},
            headers={"Content-Type": "application/xml"},
        )
    assert resp.status_code == httpx.codes.CREATED
    assert resp.content == b""


@respx.mock
def test_put_with_customized_params_and_headers_and_json_body():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/documents")
    ml_mocker.with_request_param("database", "Documents")
    ml_mocker.with_request_param("uri", "/doc.json")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"document": {}})
    ml_mocker.with_response_code(201)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    with MLClient() as client:
        resp = client.http.put(
            "/v1/documents",
            body={"document": {}},
            params={"database": "Documents", "uri": "/doc.json"},
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == httpx.codes.CREATED
    assert resp.content == b""


@respx.mock
def test_delete():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    with MLClient() as client:
        resp = client.http.delete("/manage/v2/databases/custom-db")
    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@respx.mock
def test_delete_with_customized_params_and_headers():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("custom-header", "custom-value")
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()

    with MLClient() as client:
        resp = client.http.delete(
            "/manage/v2/databases/custom-db",
            params={"format": "json"},
            headers={"custom-header": "custom-value"},
        )
    assert resp.status_code == httpx.codes.NO_CONTENT
    assert resp.content == b""


@respx.mock
def test_request_logs_warning_for_restart_location(mocker: MockerFixture):
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

    with MLClient() as client:
        resp = client.http.put(
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


@respx.mock
def test_request_does_not_log_warning_for_non_restart_202(
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

    with MLClient() as client:
        resp = client.http.put(
            "/manage/v2/forests",
            body={"operation": "attach"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.status_code == httpx.codes.ACCEPTED
    logger_warning.assert_not_called()


@respx.mock
def test_request_logs_debug_response_retrieved(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("ok")
    ml_mocker.mock_get()
    logger_debug = mocker.patch.object(http_client_module.logger, "debug")

    with MLClient() as client:
        client.http.get("/manage/v2/servers")

    debug_messages = [call.args[0] for call in logger_debug.call_args_list]
    assert "Response retrieved" in debug_messages


@respx.mock
def test_request_logs_debug_response_retrieved_no_body(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_response_header("X-Test", "1")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()
    logger_debug = mocker.patch.object(http_client_module.logger, "debug")

    with MLClient() as client:
        client.http.delete("/manage/v2/databases/custom-db")

    debug_messages = [call.args[0] for call in logger_debug.call_args_list]
    assert "Response retrieved" in debug_messages


def test_properties_delegate_to_http_client():
    client = MLClient(
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


def test_rest_property():
    client = MLClient()
    assert isinstance(client.rest, RestApi)


def test_documents_property():
    client = MLClient()
    assert isinstance(client.documents, DocumentsService)


def test_eval_property():
    client = MLClient()
    assert isinstance(client.eval, EvalService)


def test_parser_returns_ml_response_parser():
    client = MLClient()
    assert client.parser is MLResponseParser


@respx.mock
def test_manage_custom_call():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    with MLClient() as client:
        resp = client.manage.call(DatabasesGetCall())

    assert resp.status_code == 200


@respx.mock
def test_admin_uses_main_port_when_already_8001():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    with MLClient(port=8001) as client:
        resp = client.admin.get_timestamp()

    assert resp.status_code == 200


@respx.mock
def test_admin_uses_port_8001_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    with MLClient(port=8000) as client:
        resp = client.admin.get_timestamp()

    assert resp.status_code == 200


@respx.mock
def test_manage_uses_main_port_when_already_8002():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    with MLClient(port=8002) as client:
        resp = client.manage.databases.get_list()

    assert resp.status_code == 200


@respx.mock
def test_manage_uses_port_8002_when_main_port_differs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    with MLClient(port=8000) as client:
        resp = client.manage.databases.get_list()

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

    client = MLClient(port=8000)
    # Force creation of secondary clients before connecting
    _ = client.manage
    _ = client.admin

    client.connect()
    resp_manage = client.manage.databases.get_list()
    resp_admin = client.admin.get_timestamp()
    assert resp_manage.status_code == 200
    assert resp_admin.status_code == 200

    client.disconnect()
    assert not client.is_connected()


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
    ) as client:
        response = httpx.Response(202)
        client.wait_for_restart(
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

    with MLClient() as client:
        client.wait_for_restart(
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
