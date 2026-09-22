from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest
import questionary
import respx
from cleo.testers.command_tester import CommandTester
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands.trace_events import _ACTIVATION_TOGGLE
from mlclient.env import MLEnvironment
from mlclient.exceptions import MarkLogicError
from mlclient.services import TraceEvents, TraceEventsService
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


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("trace-events"))


# --- Show state and output ---


@respx.mock
def test_shows_activation_and_every_enabled_event(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
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
        json.dumps({"activated": True, "events": ["A", "B"]}),
        content_type="application/json",
    )
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\n\nA: on\nB: on\n"
    )


@pytest.mark.parametrize("event_option", ["--event", "-E"])
@respx.mock
def test_shows_a_single_event_status_when_event_option_given(
    event_option,
    mocker,
    ml_config,
):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
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
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute(f"-e test {event_option} B")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\nB: off\n"
    )


@pytest.mark.parametrize("single", [False, True])
@respx.mock
def test_output_preserves_literal_markup(single, mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(EVAL_URL)
    ml_mocker.with_request_content_type("application/x-www-form-urlencoded")
    ml_mocker.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "<error>group</error>"}),
        },
    )
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part(
        "object-node()",
        json.dumps({"activated": True, "events": ["<info>A</info>"]}),
        content_type="application/json",
    )
    ml_mocker.mock_post()
    tester = _get_tester()
    arguments = '-g "<error>group</error>"'
    if single:
        arguments += ' --event "<info>A</info>"'

    assert tester.execute(arguments) == 0

    output = tester.io.fetch_output()
    assert "Group: <error>group</error>" in output
    assert "<info>A</info>: on" in output


# --- Set activation ---


@respx.mock
def test_sets_trace_events_activated(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    mutation = respx.post(
        EVAL_URL,
        data={
            "xquery": TraceEventsService._set_activated_code(),
            "vars": json.dumps({"group": "Default", "value": "false"}),
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
        json.dumps({"activated": False, "events": []}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("-e test false")

    assert status == 0
    assert tester.io.fetch_output() == "Group: Default\nTrace Events Activated: false\n"
    variables = json.loads(
        parse_qs(mutation.calls[0].request.content.decode())["vars"][0],
    )
    assert variables["value"] == "false"
    assert mutation.call_count == 1
    assert route.call_count == 1


@pytest.mark.parametrize(
    ("token", "enabled"),
    [
        ("true", True),
        ("ON", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("OFF", False),
        ("0", False),
        ("no", False),
        ('" true "', True),
    ],
)
@respx.mock
def test_boolean_aliases_reach_the_service(token, enabled, mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    mutation = respx.post(
        EVAL_URL,
        data={
            "xquery": TraceEventsService._set_activated_code(),
            "vars": json.dumps({"group": "Default", "value": str(enabled).lower()}),
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
        json.dumps({"activated": enabled, "events": []}),
        content_type="application/json",
    )
    route = ml_mocker.mock_post()
    tester = _get_tester()

    assert tester.execute(token) == 0

    variables = json.loads(
        parse_qs(mutation.calls[0].request.content.decode())["vars"][0],
    )
    assert variables == {"group": "Default", "value": str(enabled).lower()}
    assert route.call_count == 1
    assert mutation.call_count == 1


# --- Add or remove an event ---


@pytest.mark.parametrize("event_option", ["--event", "-E"])
@respx.mock
def test_adds_a_trace_event_and_shows_its_status(event_option, mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    mutation = respx.post(
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

    tester = _get_tester()
    status = tester.execute(f"-e test {event_option} debug on")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\ndebug: on\n"
    )
    assert mutation.call_count == 1
    assert route.call_count == 1


@pytest.mark.parametrize("event_option", ["--event", "-E"])
@respx.mock
def test_removes_event_without_changing_activation(event_option, mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    mutation = respx.post(
        EVAL_URL,
        data={
            "xquery": TraceEventsService._set_event_code(False),
            "vars": json.dumps({"group": "Default", "event": "XDMP Deadlock"}),
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
    tester = _get_tester()

    assert tester.execute(f'{event_option} "XDMP Deadlock" off') == 0

    variables = json.loads(
        parse_qs(mutation.calls[0].request.content.decode())["vars"][0],
    )
    assert variables == {"group": "Default", "event": "XDMP Deadlock"}
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\nXDMP Deadlock: off\n"
    )
    assert mutation.call_count == 1
    assert route.call_count == 1


# --- Connection and group selection ---


@pytest.mark.parametrize("connection_option", ["-c", "--connection"])
@pytest.mark.parametrize("connection", ["manage", "8100"])
@respx.mock
def test_connection_selection_routes_to_the_selected_port(
    connection,
    mocker,
    ml_config,
    connection_option,
):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    builder = MLRespXMocker(use_router=False)
    builder.with_url(EVAL_URL)
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": TraceEventsService._get_code(),
            "vars": json.dumps({"group": "Default"}),
        },
    )
    builder.with_response_code(200)
    builder.with_response_body_part(
        "object-node()",
        json.dumps({"activated": False, "events": []}),
        content_type="application/json",
    )
    port = 8002 if connection == "manage" else 8100
    builder.with_url(f"http://localhost:{port}/v1/eval")
    route = builder.mock_post()

    assert _get_tester().execute(f"{connection_option} {connection}") == 0
    assert route.call_count == 1


@pytest.mark.parametrize("group_option", ["-g", "--group"])
@respx.mock
def test_targets_the_named_group(mocker, ml_config, group_option):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
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
        json.dumps({"activated": True, "events": []}),
        content_type="application/json",
    )
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute(f"-e test {group_option} Analyzer")

    assert status == 0
    assert tester.io.fetch_output().startswith("Group: Analyzer\n")


# --- Input validation ---


def test_rejects_a_non_boolean_value(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    tester = _get_tester()
    status = tester.execute("-e test maybe")

    assert status == 1
    assert "boolean" in tester.io.fetch_error()


@pytest.mark.parametrize("arguments", ["-i on", "-i --event A", "-i --event A off"])
def test_interactive_rejects_conflicting_arguments_before_connecting(
    mocker,
    arguments,
    ml_config,
):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    manager = mocker.patch("mlclient.cli.commands.trace_events.MLClientManager")
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = []
    tester = _get_tester()

    assert tester.execute(arguments) == 1

    assert "cannot be combined" in tester.io.fetch_error()
    manager.assert_not_called()
    checkbox.assert_not_called()


def test_interactive_rejects_disabled_interaction_before_connecting(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    manager = mocker.patch("mlclient.cli.commands.trace_events.MLClientManager")
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = []
    tester = _get_tester()

    assert tester.execute("-i", interactive=False) == 1

    assert "interactive terminal" in tester.io.fetch_error()
    manager.assert_not_called()
    checkbox.assert_not_called()


# --- Interactive selection ---


@respx.mock
def test_interactive_toggles_activation_and_removes_unchecked_events(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(activated=True, events=("A", "B"))
    fake.set_activated.return_value = TraceEvents(activated=False, events=("A", "B"))
    fake.set_event.return_value = TraceEvents(activated=False, events=("A",))
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = ["A"]

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    assert fake.method_calls == [
        mocker.call.get(group="Default"),
        mocker.call.set_activated(value=False, group="Default"),
        mocker.call.set_event("B", enabled=False, group="Default"),
    ]
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: false\n\nA: on\n"
    )


@respx.mock
def test_interactive_applies_no_changes_when_selection_matches(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(activated=True, events=("A",))
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = [_ACTIVATION_TOGGLE, "A"]

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    fake.set_activated.assert_not_called()
    fake.set_event.assert_not_called()
    assert tester.io.fetch_output() == (
        "Group: Default\nTrace Events Activated: true\n\nA: on\n"
    )


@pytest.mark.parametrize("activated", [False, True])
@pytest.mark.parametrize("events", [(), ("A", "Trace Events Activated")])
@respx.mock
def test_interactive_activation_toggle_leads_the_checkbox(
    mocker,
    ml_config,
    activated,
    events,
):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(activated=activated, events=events)
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = (
        [_ACTIVATION_TOGGLE, *events] if activated else list(events)
    )

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    choices = checkbox.call_args.kwargs["choices"]
    assert choices[0].value is _ACTIVATION_TOGGLE
    assert choices[0].checked is activated
    if events:
        assert isinstance(choices[1], questionary.Separator)
        assert [choice.value for choice in choices[2:]] == list(events)
        assert all(choice.checked for choice in choices[2:])
    else:
        assert len(choices) == 1
    fake.set_activated.assert_not_called()
    fake.set_event.assert_not_called()


@respx.mock
def test_interactive_activates_without_events(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(activated=False, events=())
    fake.set_activated.return_value = TraceEvents(activated=True, events=())
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = [_ACTIVATION_TOGGLE]

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 0
    fake.set_activated.assert_called_once_with(value=True, group="Default")
    fake.set_event.assert_not_called()


@respx.mock
def test_interactive_cancels_without_changes(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(activated=True, events=("A",))
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = None

    tester = _get_tester()
    status = tester.execute("-e test -i")

    assert status == 1
    fake.set_activated.assert_not_called()
    fake.set_event.assert_not_called()
    assert "Cancelled" in tester.io.fetch_error()


@respx.mock
def test_interactive_removes_events_before_activation(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(activated=False, events=("A", "B"))
    fake.set_event.return_value = TraceEvents(activated=False, events=("A",))
    fake.set_activated.return_value = TraceEvents(activated=True, events=("A",))
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = [_ACTIVATION_TOGGLE, "A"]

    assert _get_tester().execute("-i") == 0

    assert fake.method_calls == [
        mocker.call.get(group="Default"),
        mocker.call.set_event("B", enabled=False, group="Default"),
        mocker.call.set_activated(value=True, group="Default"),
    ]


@respx.mock
def test_interactive_does_not_remove_events_after_deactivation_failure(
    mocker,
    ml_config,
):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(True, ("A",))
    fake.set_activated.side_effect = MarkLogicError("denied")
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = []
    tester = _get_tester()

    assert tester.execute("-i") == 1

    fake.set_activated.assert_called_once_with(value=False, group="Default")
    fake.set_event.assert_not_called()
    assert tester.io.fetch_output() == ""
    assert "denied" in tester.io.fetch_error()


@respx.mock
def test_interactive_does_not_activate_after_removal_failure(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(False, ("A", "B"))
    fake.set_event.side_effect = MarkLogicError("denied <info>change</info>")
    checkbox = mocker.patch("questionary.checkbox")
    checkbox.return_value.ask.return_value = [_ACTIVATION_TOGGLE]
    tester = _get_tester()

    assert tester.execute("-i") == 1

    fake.set_event.assert_called_once_with("A", enabled=False, group="Default")
    fake.set_activated.assert_not_called()
    assert tester.io.fetch_output() == ""
    assert "denied <info>change</info>" in tester.io.fetch_error()


@respx.mock
def test_real_checkbox_applies_keyboard_selection(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = TraceEvents(False, ("A",))
    fake.set_event.return_value = TraceEvents(False, ())
    fake.set_activated.return_value = TraceEvents(True, ())
    checkbox = questionary.checkbox
    with create_pipe_input() as pipe:
        mocker.patch(
            "mlclient.cli.commands.trace_events.questionary.checkbox",
            side_effect=lambda *args, **kwargs: checkbox(
                *args,
                input=pipe,
                output=DummyOutput(),
                **kwargs,
            ),
        )
        pipe.send_text(" \x1b[B \r")
        tester = _get_tester()
        assert tester.execute("-i") == 0

    assert fake.method_calls == [
        mocker.call.get(group="Default"),
        mocker.call.set_event("A", enabled=False, group="Default"),
        mocker.call.set_activated(value=True, group="Default"),
    ]
    assert "Trace Events Activated: true" in tester.io.fetch_output()


# --- Failures ---


@respx.mock
def test_reports_a_marklogic_error(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    fake = mocker.patch(
        "mlclient.cli.commands.trace_events.TraceEventsService",
    ).return_value
    fake.get.return_value = None
    fake.get.side_effect = MarkLogicError("Insufficient privileges")

    tester = _get_tester()
    status = tester.execute("-e test", decorated=True)

    assert status == 1
    error = tester.io.fetch_error()
    assert "Insufficient privileges" in error
    assert "\x1b[31" in error


@respx.mock
def test_reports_bodyless_http_failure_without_success_output(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    respx.post(EVAL_URL).respond(403)
    tester = _get_tester()

    assert tester.execute("") == 1

    assert "403" in tester.io.fetch_error()
    assert tester.io.fetch_output() == ""


@respx.mock
def test_reports_transport_failure_without_success_output(mocker, ml_config):
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=ml_config)
    respx.post(EVAL_URL).mock(side_effect=httpx.ReadTimeout("timed out"))
    tester = _get_tester()

    assert tester.execute("") == 1

    assert "timed out" in tester.io.fetch_error()
    assert tester.io.fetch_output() == ""
