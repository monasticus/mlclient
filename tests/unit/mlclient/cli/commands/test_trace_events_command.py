from __future__ import annotations

import json
from urllib.parse import parse_qs

import pytest
import respx
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands.trace_events import _ACTIVATION_TOGGLE
from mlclient.env import MLEnvironment
from mlclient.exceptions import MarkLogicError
from mlclient.services import TraceEvents
from tests.utils.ml_mockers import MLRespXMocker

EVAL_URL = "http://localhost:8002/v1/eval"


@pytest.fixture(autouse=True)
def ml_config() -> MLEnvironment:
    config = {
        "app-name": "my-marklogic-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app-servers": [
            {"id": "manage", "port": 8002, "auth": "basic", "rest": True},
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("trace-events"))


def _mock_state(activated: bool, events: list[str]):
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
def test_shows_activation_and_every_enabled_event():
    _mock_state(activated=True, events=["A", "B"]).mock_post()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\nA: on\nB: on\n"
    )


@respx.mock
def test_sets_trace_events_activated():
    route = _mock_state(activated=False, events=[]).mock_post()

    tester = _get_tester()
    status = tester.execute("-e test false")

    assert status == 0
    assert tester.io.fetch_output() == "Group: Default\nTrace Events Activated: false\n"
    variables = json.loads(parse_qs(route.calls[0].request.content.decode())["vars"][0])
    assert variables["value"] == "false"


@respx.mock
def test_shows_a_single_event_status_when_event_option_given():
    _mock_state(activated=True, events=["A"]).mock_post()

    tester = _get_tester()
    status = tester.execute("-e test --event B")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\nB: off\n"
    )


@respx.mock
def test_adds_a_trace_event_and_shows_its_status():
    _mock_state(activated=True, events=["debug"]).mock_post()

    tester = _get_tester()
    status = tester.execute("-e test --event debug on")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\ndebug: on\n"
    )


@respx.mock
def test_targets_the_named_group():
    _mock_state(activated=True, events=[]).mock_post()

    tester = _get_tester()
    status = tester.execute("-e test -g Analyzer")

    assert status == 0
    assert tester.io.fetch_output().startswith("Group: Analyzer\n")


def test_rejects_a_non_boolean_value():
    tester = _get_tester()
    status = tester.execute("-e test maybe")

    assert status == 1
    assert "boolean" in tester.io.fetch_error()


def _fake_service(mocker, get, set_activated=None, set_event=None):
    fake = mocker.Mock()
    fake.get.return_value = get
    fake.set_activated.return_value = set_activated
    fake.set_event.return_value = set_event
    mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
        return_value=fake,
    )
    return fake


def _select(mocker, selected):
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = selected
    return checkbox


@respx.mock
def test_interactive_toggles_activation_and_removes_unchecked_events(mocker):
    fake = _fake_service(
        mocker,
        get=TraceEvents(activated=True, events=("A", "B")),
        set_activated=TraceEvents(activated=False, events=("A", "B")),
        set_event=TraceEvents(activated=False, events=("A",)),
    )
    _select(mocker, ["A"])

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    fake.set_activated.assert_called_once_with(value=False, group="Default")
    fake.set_event.assert_called_once_with("B", enabled=False, group="Default")
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: false\nA: on\n"
    )


@respx.mock
def test_interactive_applies_no_changes_when_selection_matches(mocker):
    fake = _fake_service(mocker, get=TraceEvents(activated=True, events=("A",)))
    _select(mocker, [_ACTIVATION_TOGGLE, "A"])

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    fake.set_activated.assert_not_called()
    fake.set_event.assert_not_called()
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\nA: on\n"
    )


@respx.mock
def test_interactive_activation_toggle_leads_the_checkbox(mocker):
    _fake_service(mocker, get=TraceEvents(activated=False, events=()))
    checkbox = _select(mocker, [])

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    choices = checkbox.call_args.kwargs["choices"]
    assert choices[0].value is _ACTIVATION_TOGGLE
    assert choices[0].checked is False


@respx.mock
def test_interactive_activates_without_events(mocker):
    fake = _fake_service(
        mocker,
        get=TraceEvents(activated=False, events=()),
        set_activated=TraceEvents(activated=True, events=()),
    )
    _select(mocker, [_ACTIVATION_TOGGLE])

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    fake.set_activated.assert_called_once_with(value=True, group="Default")
    fake.set_event.assert_not_called()


@respx.mock
def test_interactive_cancels_without_changes(mocker):
    fake = _fake_service(mocker, get=TraceEvents(activated=True, events=("A",)))
    _select(mocker, None)

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 1
    fake.set_activated.assert_not_called()
    fake.set_event.assert_not_called()
    assert "Cancelled" in tester.io.fetch_error()


@respx.mock
def test_reports_a_marklogic_error(mocker):
    fake = _fake_service(mocker, get=None)
    fake.get.side_effect = MarkLogicError("Insufficient privileges")

    tester = _get_tester()
    status = tester.execute("-e test", decorated=True)

    assert status == 1
    error = tester.io.fetch_error()
    assert "Insufficient privileges" in error
    assert "\x1b[31" in error
