from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient._options import UNSET
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


# --- Read state ---


@respx.mock
def test_get_returns_activation_and_events_sorted(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Default"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": True, "events": ["B", "A", "C"]}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()

    result = TraceEventsService(ml.rest).get()

    assert result.activated is True
    assert result.events == ("A", "B", "C")
    code = _xquery_of(route, -1)
    assert "admin:group-get-trace-events-activated" in code
    assert "admin:group-get-trace-events" in code
    assert "fn:string(*:event-id)" in code


@respx.mock
def test_get_targets_the_named_group(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Analyzer"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": False, "events": []}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()

    result = TraceEventsService(ml.rest).get(group="Analyzer")

    assert result.activated is False
    assert result.events == ()
    content = route.calls.last.request.content.decode()
    variables = json.loads(parse_qs(content)["vars"][0])
    assert variables["group"] == "Analyzer"


@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_get_timeout_and_variables_are_forwarded_without_persisting(timeout):
    builder = MLRespXMocker(use_router=False)
    builder.with_url(EVAL_URL)
    builder.with_response_code(200)
    builder.with_response_body_part(
        "object-node()",
        json.dumps({"activated": False, "events": []}),
        content_type="application/json",
    )
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Default"}),
        },
    )
    route = builder.mock_post()
    with MLClient(timeout=11) as client:
        service = TraceEventsService(client.rest)
        assert service.get(timeout=timeout) == TraceEvents(False, ())
        assert service.get() == TraceEvents(False, ())

    assert route.call_count == 2
    assert (
        route.calls[0].request.extensions["timeout"]
        == httpx.Timeout(
            11 if timeout is UNSET else timeout,
        ).as_dict()
    )
    assert route.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()


@respx.mock
def test_get_transport_failure_propagates_without_a_follow_up_read(ml):
    error = httpx.ReadTimeout("timed out")
    route = respx.post(EVAL_URL).mock(side_effect=error)
    service = TraceEventsService(ml.rest)

    with pytest.raises(httpx.ReadTimeout) as raised:
        service.get()

    assert raised.value is error
    assert route.call_count == 1


@respx.mock
def test_get_raises_http_status_error_on_a_gateway_error(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(503)
    ml_mocker.with_response_content_type("text/html")
    ml_mocker.with_response_body(GATEWAY_503_BODY)
    ml_mocker.mock_post()

    with pytest.raises(httpx.HTTPStatusError, match="503"):
        TraceEventsService(ml.rest).get()


@respx.mock
def test_get_raises_marklogic_error_on_a_server_error(ml):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_content_type("text/html; charset=utf-8")
    ml_mocker.with_response_body(MARKLOGIC_500_BODY)
    ml_mocker.mock_post()

    with pytest.raises(MarkLogicError, match="XDMP-NOSUCHGROUP"):
        TraceEventsService(ml.rest).get()


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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_response_code(500)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(body)
    ml_mocker.mock_post()

    with pytest.raises(
        MarkLogicError,
        match=r"\[500 Internal Server Error\] \(ADMIN-DUPLICATENAME\)",
    ):
        TraceEventsService(ml.rest).get()


# --- Set activation ---


@respx.mock
def test_set_activated_saves_configuration_and_returns_fresh_state(ml):
    mutation_route = respx.post(
        EVAL_URL,
        data={
            "xquery": TraceEventsService._set_activated_code(),
            "vars": json.dumps({"group": "Default", "value": "true"}),
        },
    ).respond(204)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Default"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": True, "events": ["A"]}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()

    result = TraceEventsService(ml.rest).set_activated(value=True)

    assert result == TraceEvents(activated=True, events=("A",))
    mutation = _xquery_of(mutation_route, 0)
    assert "admin:group-set-trace-events-activated" in mutation
    assert "admin:save-configuration" in mutation
    assert _vars_of(mutation_route, 0)["value"] == "true"
    assert "admin:group-get-trace-events-activated" in _xquery_of(route, 0)
    assert mutation_route.call_count == 1
    assert route.call_count == 1


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_set_activated_binds_variables_reads_fresh_state_and_forwards_timeout(
    enabled,
    timeout,
):
    group = 'Group "quoted" & <xml>'
    event = 'Event "quoted" & <xml>'
    variables = {"group": group, "value": "true" if enabled else "false"}
    query = TraceEventsService._set_activated_code()
    mutation = respx.post(
        EVAL_URL,
        data={"xquery": query, "vars": json.dumps(variables)},
    ).respond(204)
    builder = MLRespXMocker(use_router=False)
    builder.with_url(EVAL_URL)
    builder.with_response_code(200)
    builder.with_response_body_part(
        "object-node()",
        json.dumps({"activated": enabled, "events": [event]}),
        content_type="application/json",
    )
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": group}),
        },
    )
    read = builder.mock_post()

    with MLClient(timeout=11) as client:
        service = TraceEventsService(client.rest)
        result = service.set_activated(
            value=enabled,
            group=group,
            timeout=timeout,
        )
        assert result == TraceEvents(enabled, (event,))
        assert service.get(group=group) == result

    assert mutation.call_count == 1
    assert read.call_count == 2
    assert respx.calls[0] == mutation.calls[0]
    expected = httpx.Timeout(11 if timeout is UNSET else timeout).as_dict()
    assert mutation.calls[0].request.extensions["timeout"] == expected
    assert read.calls[0].request.extensions["timeout"] == expected
    assert read.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()
    assert group not in query
    assert event not in query


@pytest.mark.parametrize("failed_request", [0, 1], ids=["mutation", "read-back"])
@respx.mock
def test_set_activated_stops_on_failure_without_reporting_success(
    ml,
    failed_request,
):
    responses = [httpx.Response(204)] * failed_request + [httpx.Response(403)]
    route = respx.post(EVAL_URL).mock(side_effect=responses)
    service = TraceEventsService(ml.rest)

    with pytest.raises(httpx.HTTPStatusError, match="403"):
        service.set_activated(value=True)

    assert route.call_count == failed_request + 1


@respx.mock
def test_set_activated_transport_failure_propagates_without_a_follow_up_read(ml):
    error = httpx.ReadTimeout("timed out")
    route = respx.post(EVAL_URL).mock(side_effect=error)
    service = TraceEventsService(ml.rest)

    with pytest.raises(httpx.ReadTimeout) as raised:
        service.set_activated(value=False)

    assert raised.value is error
    assert route.call_count == 1


# --- Add or remove an event ---


@respx.mock
def test_set_event_enabled_adds_the_event(ml):
    mutation_route = respx.post(
        EVAL_URL,
        data={
            "xquery": TraceEventsService._set_event_code(True),
            "vars": json.dumps({"group": "Default", "event": "debug"}),
        },
    ).respond(204)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Default"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": True, "events": ["debug"]}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()

    result = TraceEventsService(ml.rest).set_event("debug", enabled=True)

    assert result.events == ("debug",)
    mutation = _xquery_of(mutation_route, 0)
    assert "admin:group-add-trace-event" in mutation
    assert "admin:group-trace-event" in mutation
    assert "admin:save-configuration" in mutation
    assert "if (not($exists))" in mutation
    assert _vars_of(mutation_route, 0)["event"] == "debug"
    assert mutation_route.call_count == 1
    assert route.call_count == 1


@respx.mock
def test_set_event_disabled_deletes_the_event(ml):
    mutation_route = respx.post(
        EVAL_URL,
        data={
            "xquery": TraceEventsService._set_event_code(False),
            "vars": json.dumps({"group": "Default", "event": "debug"}),
        },
    ).respond(204)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Default"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": True, "events": []}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()

    result = TraceEventsService(ml.rest).set_event("debug", enabled=False)

    assert result.events == ()
    mutation = _xquery_of(mutation_route, 0)
    assert "admin:group-delete-trace-event" in mutation
    assert "if ($exists)" in mutation
    assert mutation_route.call_count == 1
    assert route.call_count == 1


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("timeout", [UNSET, None, 2, httpx.Timeout(5, read=7)])
@respx.mock
def test_set_event_binds_variables_reads_fresh_state_and_forwards_timeout(
    enabled,
    timeout,
):
    group = 'Group "quoted" & <xml>'
    event = 'Event "quoted" & <xml>'
    variables = {"group": group, "event": event}
    query = TraceEventsService._set_event_code(enabled)
    mutation = respx.post(
        EVAL_URL,
        data={"xquery": query, "vars": json.dumps(variables)},
    ).respond(204)
    builder = MLRespXMocker(use_router=False)
    builder.with_url(EVAL_URL)
    builder.with_response_code(200)
    builder.with_response_body_part(
        "object-node()",
        json.dumps({"activated": enabled, "events": [event]}),
        content_type="application/json",
    )
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": group}),
        },
    )
    read = builder.mock_post()

    with MLClient(timeout=11) as client:
        service = TraceEventsService(client.rest)
        result = service.set_event(
            event,
            enabled=enabled,
            group=group,
            timeout=timeout,
        )
        assert result == TraceEvents(enabled, (event,))
        assert service.get(group=group) == result

    assert mutation.call_count == 1
    assert read.call_count == 2
    assert respx.calls[0] == mutation.calls[0]
    expected = httpx.Timeout(11 if timeout is UNSET else timeout).as_dict()
    assert mutation.calls[0].request.extensions["timeout"] == expected
    assert read.calls[0].request.extensions["timeout"] == expected
    assert read.calls[1].request.extensions["timeout"] == httpx.Timeout(11).as_dict()
    assert group not in query
    assert event not in query


@pytest.mark.parametrize("failed_request", [0, 1], ids=["mutation", "read-back"])
@respx.mock
def test_set_event_stops_on_failure_without_reporting_success(
    ml,
    failed_request,
):
    responses = [httpx.Response(204)] * failed_request + [httpx.Response(403)]
    route = respx.post(EVAL_URL).mock(side_effect=responses)
    service = TraceEventsService(ml.rest)

    with pytest.raises(httpx.HTTPStatusError, match="403"):
        service.set_event("debug", enabled=True)

    assert route.call_count == failed_request + 1


@respx.mock
def test_set_event_transport_failure_propagates_without_a_follow_up_read(ml):
    error = httpx.ReadTimeout("timed out")
    route = respx.post(EVAL_URL).mock(side_effect=error)
    service = TraceEventsService(ml.rest)

    with pytest.raises(httpx.ReadTimeout) as raised:
        service.set_event("debug", enabled=False)

    assert raised.value is error
    assert route.call_count == 1


def _xquery_of(route, index: int) -> str:
    content = route.calls[index].request.content.decode()
    return parse_qs(content)["xquery"][0]


def _vars_of(route, index: int) -> dict:
    content = route.calls[index].request.content.decode()
    return json.loads(parse_qs(content)["vars"][0])
