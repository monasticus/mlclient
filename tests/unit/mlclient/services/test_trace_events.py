from __future__ import annotations

import json
from urllib.parse import parse_qs

import pytest
import respx

from mlclient import MLClient
from mlclient.services import TraceEvents, TraceEventsService
from tests.utils.ml_mockers import MLRespXMocker

EVAL_URL = "http://localhost:8000/v1/eval"


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
