from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.exceptions import MarkLogicError
from mlclient.services import TraceEvents, TraceEventsService
from tests.utils.ml_mockers import MLRespXMocker

EVAL_URL = "http://localhost:8000/v1/eval"

GATEWAY_503_BODY = (
    "<html>\r\n"
    "<head><title>503 Service Temporarily Unavailable</title></head>\r\n"
    "<body>\r\n"
    "<center><h1>503 Service Temporarily Unavailable</h1></center>\r\n"
    "</body>\r\n"
    "</html>\r\n"
)

MARKLOGIC_500_BODY = (
    '<html xmlns="http://www.w3.org/1999/xhtml">'
    "<head><title>500 Internal Server Error</title></head>"
    '<body><span class="error"><h1>500 Internal Server Error</h1><dl>'
    "<dt>XDMP-NOSUCHGROUP: No such group Nope</dt><dd></dd>"
    "</dl></span></body></html>"
)


@pytest.fixture(autouse=True)
def ml() -> MLClient:
    return MLClient()


@pytest.fixture(autouse=True)
def _setup_and_teardown(ml):
    ml.connect()

    yield

    ml.disconnect()


def _service(ml: MLClient) -> TraceEventsService:
    return TraceEventsService(ml.rest)


def _sent_xquery(route) -> str:
    content = route.calls.last.request.content.decode()
    return parse_qs(content)["xquery"][0]


def _mock_state(activated: bool, events: list[str]) -> MLRespXMocker:
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": activated, "events": events}),
        content_type="application/json",
    )
    return ml_mocker


@respx.mock
def test_get_returns_activation_and_events(ml):
    route = _mock_state(activated=True, events=["A", "B"]).mock_post()

    result = _service(ml).get()

    assert result.activated is True
    assert result.events == ("A", "B")
    code = _sent_xquery(route)
    assert "admin:group-get-trace-events-activated" in code
    assert "admin:group-get-trace-events" in code


@respx.mock
def test_get_targets_the_named_group(ml):
    route = _mock_state(activated=False, events=[]).mock_post()

    result = _service(ml).get(group="Analyzer")

    assert result.activated is False
    assert result.events == ()
    content = route.calls.last.request.content.decode()
    variables = json.loads(parse_qs(content)["vars"][0])
    assert variables["group"] == "Analyzer"


def _xquery_of(route, index: int) -> str:
    content = route.calls[index].request.content.decode()
    return parse_qs(content)["xquery"][0]


def _vars_of(route, index: int) -> dict:
    content = route.calls[index].request.content.decode()
    return json.loads(parse_qs(content)["vars"][0])


@respx.mock
def test_set_activated_saves_configuration_and_returns_fresh_state(ml):
    route = _mock_state(activated=True, events=["A"]).mock_post()

    result = _service(ml).set_activated(value=True)

    assert result == TraceEvents(activated=True, events=("A",))
    mutation = _xquery_of(route, 0)
    assert "admin:group-set-trace-events-activated" in mutation
    assert "admin:save-configuration" in mutation
    assert _vars_of(route, 0)["value"] == "true"
    assert "admin:group-get-trace-events-activated" in _xquery_of(route, 1)


@respx.mock
def test_set_event_enabled_adds_the_event(ml):
    route = _mock_state(activated=True, events=["debug"]).mock_post()

    result = _service(ml).set_event("debug", enabled=True)

    assert result.events == ("debug",)
    mutation = _xquery_of(route, 0)
    assert "admin:group-add-trace-event" in mutation
    assert "admin:group-trace-event" in mutation
    assert "admin:save-configuration" in mutation
    assert _vars_of(route, 0)["event"] == "debug"


@respx.mock
def test_set_event_disabled_deletes_the_event(ml):
    route = _mock_state(activated=True, events=[]).mock_post()

    result = _service(ml).set_event("debug", enabled=False)

    assert result.events == ()
    assert "admin:group-delete-trace-event" in _xquery_of(route, 0)


def _mock_raw(status_code: int, content_type: str, body: str) -> MLRespXMocker:
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(status_code)
    ml_mocker.with_response_content_type(content_type)
    ml_mocker.with_response_body(body)
    return ml_mocker


@respx.mock
def test_get_raises_http_status_error_on_a_gateway_error(ml):
    _mock_raw(503, "text/html", GATEWAY_503_BODY).mock_post()

    with pytest.raises(httpx.HTTPStatusError, match="503"):
        _service(ml).get()


@respx.mock
def test_get_raises_marklogic_error_on_a_server_error(ml):
    _mock_raw(500, "text/html; charset=utf-8", MARKLOGIC_500_BODY).mock_post()

    with pytest.raises(MarkLogicError, match="XDMP-NOSUCHGROUP"):
        _service(ml).get()


@respx.mock
def test_get_raises_marklogic_error_on_a_json_error_response(ml):
    body = json.dumps(
        {
            "errorResponse": {
                "statusCode": 500,
                "status": "Internal Server Error",
                "messageCode": "ADMIN-DUPLICATENAME",
                "message": "ADMIN-DUPLICATENAME: Trace Event already exists",
            },
        },
    )
    _mock_raw(500, "application/json", body).mock_post()

    with pytest.raises(
        MarkLogicError,
        match=r"\[500 Internal Server Error\] \(ADMIN-DUPLICATENAME\)",
    ):
        _service(ml).get()
