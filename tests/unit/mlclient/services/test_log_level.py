from __future__ import annotations

import json
import logging
from urllib.parse import parse_qs

import httpx
import pytest
import respx
from httpx_retries import Retry

from mlclient import MLClient
from mlclient.connection import UNSET
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.http_config import HTTPConfig
from mlclient.services import LogLevelService
from tests.utils.ml_mockers import MLRespXMocker

EVAL_URL = "http://localhost:8000/v1/eval"
GROUP_PROPS_URL = "http://localhost:8002/manage/v2/groups/Default/properties"
SERVER_PROPS_URL = "http://localhost:8002/manage/v2/servers/App-Services/properties"


@pytest.fixture(autouse=True)
def ml() -> MLClient:
    return MLClient()


@pytest.fixture(autouse=True)
def _setup_and_teardown(ml):
    ml.connect()

    yield

    ml.disconnect()


def _service(ml: MLClient) -> LogLevelService:
    return LogLevelService(ml.rest, ml.manage)


def _sent_xquery(route) -> str:
    content = route.calls.last.request.content.decode()
    return parse_qs(content)["xquery"][0]


@respx.mock
def test_get_group_file_level_uses_eval(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "info")
    route = ml_mocker.mock_post()

    assert _service(ml).get() == "info"
    assert "admin:group-get-file-log-level" in _sent_xquery(route)


@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_get_timeout_reaches_eval_without_changing_client(timeout):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "info")
    route = ml_mocker.mock_post()

    with MLClient(timeout=11) as client:
        service = LogLevelService(client.rest, client.manage)
        assert service.get(timeout=timeout) == "info"
        assert service.get() == "info"

    expected = httpx.Timeout(11 if timeout is UNSET else timeout).as_dict()
    assert route.calls[0].request.extensions["timeout"] == expected
    assert route.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()
    variables = json.loads(parse_qs(route.calls[0].request.content.decode())["vars"][0])
    assert "timeout" not in variables


@respx.mock
def test_get_group_system_level_uses_eval(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "debug")
    route = ml_mocker.mock_post()

    assert _service(ml).get(group="Analyzer", log_type="system") == "debug"
    assert "admin:group-get-system-log-level" in _sent_xquery(route)


@respx.mock
def test_get_server_file_level_uses_appserver_eval(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "warning")
    route = ml_mocker.mock_post()

    assert _service(ml).get(server="App-Services") == "warning"
    assert "admin:appserver-get-file-log-level" in _sent_xquery(route)


@respx.mock
def test_set_group_level_saves_configuration_and_returns_level(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "error")
    route = ml_mocker.mock_post()

    assert _service(ml).set("error") == "error"
    code = _sent_xquery(route)
    assert "admin:group-set-file-log-level" in code
    assert "admin:save-configuration" in code


@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_set_timeout_reaches_eval_without_changing_client(timeout):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "info")
    route = ml_mocker.mock_post()

    with MLClient(timeout=11) as client:
        service = LogLevelService(client.rest, client.manage)
        assert service.set("info", timeout=timeout) == "info"
        assert service.set("info") == "info"

    expected = httpx.Timeout(11 if timeout is UNSET else timeout).as_dict()
    assert route.calls[0].request.extensions["timeout"] == expected
    assert route.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()
    variables = json.loads(parse_qs(route.calls[0].request.content.decode())["vars"][0])
    assert "timeout" not in variables


@respx.mock
def test_set_server_level_uses_appserver_eval(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "error")
    route = ml_mocker.mock_post()

    assert _service(ml).set("error", server="App-Services") == "error"
    code = _sent_xquery(route)
    assert "admin:appserver-set-file-log-level" in code
    assert "admin:save-configuration" in code


@respx.mock
def test_get_group_falls_back_to_manage_on_privilege_error(ml, caplog):
    caplog.set_level(logging.DEBUG, logger="mlclient.services.log_level")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"file-log-level": "notice"})
    ml_mocker.mock_get()

    assert _service(ml).get() == "notice"

    messages = caplog.messages
    attempt = next(
        i for i, message in enumerate(messages) if "attempting eval" in message
    )
    fallback = next(
        i for i, message in enumerate(messages) if "falling back to Manage" in message
    )
    manage = next(
        i for i, message in enumerate(messages) if "attempting Manage" in message
    )
    assert attempt < fallback < manage
    assert "Log-level Manage succeeded" in messages


@pytest.mark.parametrize("server", [None, "App-Services"])
@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_get_timeout_reaches_manage_fallback(server, timeout):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_body("Forbidden")
    eval_route = ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL if server is None else SERVER_PROPS_URL)
    if server is not None:
        ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"file-log-level": "info"})
    manage_route = ml_mocker.mock_get()

    with MLClient(
        timeout=11,
        manage_config=HTTPConfig.resolve(port=8002, timeout=13),
    ) as client:
        service = LogLevelService(client.rest, client.manage)
        assert service.get(server=server, timeout=timeout) == "info"
        assert service.get(server=server) == "info"

    eval_timeout = 11 if timeout is UNSET else timeout
    manage_timeout = 13 if timeout is UNSET else timeout
    assert (
        eval_route.calls[0].request.extensions["timeout"]
        == httpx.Timeout(eval_timeout).as_dict()
    )
    assert (
        manage_route.calls[0].request.extensions["timeout"]
        == httpx.Timeout(manage_timeout).as_dict()
    )
    assert (
        eval_route.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()
    )
    assert (
        manage_route.calls[1].request.extensions["timeout"]
        == httpx.Timeout(13).as_dict()
    )


@respx.mock
def test_get_server_falls_back_to_manage_servers_on_privilege_error(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(SERVER_PROPS_URL)
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"file-log-level": "notice"})
    ml_mocker.mock_get()

    assert _service(ml).get(server="App-Services") == "notice"


@respx.mock
def test_set_group_falls_back_to_manage_put_on_privilege_error(ml, caplog):
    caplog.set_level(logging.DEBUG, logger="mlclient.services.log_level")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"file-log-level": "error"})
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    assert _service(ml).set("error") == "error"

    messages = caplog.messages
    attempt = next(
        i for i, message in enumerate(messages) if "attempting eval" in message
    )
    fallback = next(
        i for i, message in enumerate(messages) if "falling back to Manage" in message
    )
    manage = next(
        i for i, message in enumerate(messages) if "attempting Manage" in message
    )
    assert attempt < fallback < manage
    assert "Log-level Manage succeeded" in messages


@pytest.mark.parametrize("server", [None, "App-Services"])
@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_set_timeout_reaches_manage_fallback(server, timeout):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_body("Forbidden")
    eval_route = ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL if server is None else SERVER_PROPS_URL)
    if server is not None:
        ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"file-log-level": "info"})
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    manage_route = ml_mocker.mock_put()

    with MLClient(
        timeout=11,
        manage_config=HTTPConfig.resolve(port=8002, timeout=13),
    ) as client:
        service = LogLevelService(client.rest, client.manage)
        assert service.set("info", server=server, timeout=timeout) == "info"
        assert service.set("info", server=server) == "info"

    eval_timeout = 11 if timeout is UNSET else timeout
    manage_timeout = 13 if timeout is UNSET else timeout
    assert (
        eval_route.calls[0].request.extensions["timeout"]
        == httpx.Timeout(eval_timeout).as_dict()
    )
    assert (
        manage_route.calls[0].request.extensions["timeout"]
        == httpx.Timeout(manage_timeout).as_dict()
    )
    assert (
        eval_route.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()
    )
    assert (
        manage_route.calls[1].request.extensions["timeout"]
        == httpx.Timeout(13).as_dict()
    )


@respx.mock
def test_set_server_falls_back_to_manage_servers_put_on_privilege_error(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(SERVER_PROPS_URL)
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"file-log-level": "error"})
    ml_mocker.with_response_code(204)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_put()

    assert _service(ml).set("error", server="App-Services") == "error"


@respx.mock
def test_non_privilege_eval_error_is_reraised(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "XDMP-CAST"}})
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError, match="XDMP-CAST"):
        _service(ml).get()


@pytest.mark.parametrize("operation", ["get", "set"])
@respx.mock
def test_eval_timeout_propagates_without_manage_fallback(operation):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_post_side_effect(httpx.ReadTimeout("read timed out"))

    with MLClient(retry=Retry(total=0)) as client:
        service = LogLevelService(client.rest, client.manage)
        call = getattr(service, operation)
        args = () if operation == "get" else ("info",)
        with pytest.raises(httpx.ReadTimeout, match="read timed out"):
            call(*args, timeout=0.1)


@pytest.mark.parametrize("operation", ["get", "set"])
@respx.mock
def test_manage_timeout_is_logged_and_propagated(operation, caplog):
    caplog.set_level(logging.DEBUG, logger="mlclient.services.log_level")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_body("Forbidden")
    ml_mocker.mock_post()
    route = respx.route(
        method="GET" if operation == "get" else "PUT", url=GROUP_PROPS_URL,
    )
    route.mock(side_effect=httpx.ReadTimeout("manage timed out"))
    with MLClient(retry=Retry(total=0)) as client:
        service = LogLevelService(client.rest, client.manage)
        call = getattr(service, operation)
        args = () if operation == "get" else ("info",)
        with pytest.raises(httpx.ReadTimeout, match="manage timed out"):
            call(*args)
    assert any(
        "Manage transport failure" in message and "manage timed out" in message
        for message in caplog.messages
    )


@respx.mock
def test_non_standard_eval_error_body_is_reraised(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(json.dumps(["unexpected", "shape"]))
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError):
        _service(ml).get()


@respx.mock
def test_manage_fallback_failure_names_required_role(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError, match="manage-admin"):
        _service(ml).get()


@respx.mock
def test_manage_set_fallback_failure_names_manage_admin_role(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_content_type("application/json")
    ml_mocker.with_request_body({"file-log-level": "error"})
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_put()

    with pytest.raises(MarkLogicError, match="manage-admin"):
        _service(ml).set("error")


def test_server_with_system_type_is_rejected(ml):
    with pytest.raises(WrongParametersError, match="system log level"):
        _service(ml).get(server="App-Services", log_type="system")


def test_unsupported_log_type_is_rejected(ml):
    with pytest.raises(WrongParametersError, match="Unsupported log type"):
        _service(ml).get(log_type="audit")


def test_unsupported_level_is_rejected(ml):
    with pytest.raises(WrongParametersError, match="Unsupported log level"):
        _service(ml).set("verbose")


@pytest.mark.parametrize("marker", ["SEC-PRIV", "SEC-NOPRIV", "SEC-NOADMIN"])
@respx.mock
def test_privilege_error_detection_by_message_code(ml, marker: str):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": marker}})
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"file-log-level": "info"})
    ml_mocker.mock_get()

    assert _service(ml).get() == "info"


@pytest.mark.parametrize("status_code", [401, 403])
@respx.mock
def test_privilege_error_detection_by_status_code(ml, status_code: int):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(status_code)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "OTHER-CODE"}})
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"file-log-level": "info"})
    ml_mocker.mock_get()

    assert _service(ml).get() == "info"


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("text/plain", "Forbidden"),
        ("text/html", "<html><body>Forbidden</body></html>"),
        ("text/plain", ""),
        ("application/json", "not json"),
        ("application/xml", "not xml"),
        ("application/xml", "<unexpected/>"),
        ("application/json", '{"errorResponse": null}'),
    ],
)
@respx.mock
def test_unstructured_auth_error_still_falls_back(ml, content_type, body):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body({"file-log-level": "info"})
    ml_mocker.mock_get()

    assert _service(ml).get() == "info"


@respx.mock
def test_manage_non_privilege_error_preserves_cause(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_body("Forbidden")
    ml_mocker.mock_post()

    ml_mocker.with_url(GROUP_PROPS_URL)
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(
        {"errorResponse": {"messageCode": "MANAGE-NOSUCHGROUP"}},
    )
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError, match="MANAGE-NOSUCHGROUP") as error:
        _service(ml).get()
    assert "requires" not in str(error.value)


@respx.mock
def test_server_read_auth_error_names_manage_user(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_body("Forbidden")
    ml_mocker.mock_post()

    ml_mocker.with_url(SERVER_PROPS_URL)
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(403)
    ml_mocker.with_response_body("Forbidden")
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError, match="manage-user"):
        _service(ml).get(server="App-Services")
