from __future__ import annotations

import httpx
import respx
from pytest_mock import MockerFixture

from mlclient import (
    MLClient,
)
from mlclient.clients import ml_client as ml_client_module
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
    resp = client.get("/manage/v2/servers")
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
        resp = client.get("/manage/v2/servers")
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
        resp = client.get(
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
        resp = client.post("/manage/v2/databases/Documents")
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
        resp = client.post(
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
        resp = client.post(
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
        resp = client.put("/v1/documents")
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
        resp = client.put(
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
        resp = client.put(
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
        resp = client.delete("/manage/v2/databases/custom-db")
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
        resp = client.delete(
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
    logger_warning = mocker.patch.object(ml_client_module.logger, "warning")

    with MLClient() as client:
        resp = client.put(
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
    logger_warning = mocker.patch.object(ml_client_module.logger, "warning")

    with MLClient() as client:
        resp = client.put(
            "/manage/v2/forests",
            body={"operation": "attach"},
            params={"format": "json"},
            headers={"Content-Type": "application/json"},
        )

    assert resp.status_code == httpx.codes.ACCEPTED
    logger_warning.assert_not_called()


@respx.mock
def test_request_logs_fine_formatted_response_with_body(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("ok")
    ml_mocker.mock_get()
    logger_fine = mocker.patch.object(ml_client_module.logger, "fine")
    mocker.patch.object(ml_client_module.logger, "isEnabledFor", return_value=True)

    with MLClient() as client:
        client.get("/manage/v2/servers")

    assert logger_fine.call_count == 2
    response_log = logger_fine.call_args_list[-1].args[1]
    assert "HTTP/1.1 200 OK" in response_log
    assert "content-type: text/plain" in response_log
    assert response_log.endswith("\n\nok")


@respx.mock
def test_request_logs_fine_formatted_response_without_body(mocker: MockerFixture):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/databases/custom-db")
    ml_mocker.with_response_code(204)
    ml_mocker.with_response_header("X-Test", "1")
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_delete()
    logger_fine = mocker.patch.object(ml_client_module.logger, "fine")
    mocker.patch.object(ml_client_module.logger, "isEnabledFor", return_value=True)

    with MLClient() as client:
        client.delete("/manage/v2/databases/custom-db")

    assert logger_fine.call_count == 2
    response_log = logger_fine.call_args_list[-1].args[1]
    assert "HTTP/1.1 204 No Content" in response_log
    assert "x-test: 1" in response_log


def test_wait_for_restart_completion_builds_restart_waiter_and_uses_default_retry(
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
        client.wait_for_restart_completion(
            response=response,
            timeout=12.0,
            poll_interval=0.5,
        )

    kwargs = restart_waiter_cls.call_args.kwargs
    assert kwargs["protocol"] == "https"
    assert kwargs["host"] == "example.com"
    assert isinstance(kwargs["auth"], httpx.BasicAuth)
    waiter.wait_for_restart_completion.assert_called_once_with(
        response,
        12.0,
        0.5,
        ml_client_module.RESTART_RETRY_STRATEGY,
    )


def test_wait_for_restart_completion_uses_custom_retry(
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
        client.wait_for_restart_completion(
            response=None,
            timeout=12.0,
            poll_interval=0.5,
            retry=custom_retry,
        )

    assert restart_waiter_cls.called
    waiter.wait_for_restart_completion.assert_called_once_with(
        None,
        12.0,
        0.5,
        custom_retry,
    )
