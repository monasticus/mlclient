from __future__ import annotations

import logging
import sys

import pytest
from cleo.formatters.style import Style
from cleo.io.buffered_io import BufferedIO
from cleo.io.outputs.output import Verbosity

import mlclient
from mlclient.cli import MLCLIentApplication, main
from mlclient.cli.app import CleoAppHandler


@pytest.fixture(autouse=True)
def _restore_mlclient_logger():
    logger = logging.getLogger("mlclient")
    handlers, level = logger.handlers[:], logger.level
    yield
    logger.handlers, logger.level = handlers, level


def test_main_sys_exit_1():
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 1


def test_main_sys_exit_0():
    sys.argv = ["ml"]
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 0


def test_app_properties():
    app = MLCLIentApplication()
    assert app.name == "ml"
    assert app.display_name == "MLCLIent"
    assert app.version == mlclient.__version__


def test_emit_preserves_angle_brackets_in_the_message():
    io = BufferedIO()
    io.set_verbosity(Verbosity.DEBUG)
    io.output.formatter.set_style("mlclient_fine", Style(foreground="cyan"))
    handler = CleoAppHandler(io)
    handler.setFormatter(logging.Formatter("%(message)s"))
    record = logging.LogRecord(
        "mlclient",
        logging.FINE,
        __file__,
        1,
        "<head><title>503 Service Unavailable</title></head>",
        None,
        None,
    )

    handler.emit(record)

    output = io.fetch_output()
    assert "</title>" in output
    assert "</head>" in output


@pytest.mark.parametrize("arguments", [["-h"], ["--help"]])
def test_main_prints_command_list_for_help_alone(
    arguments: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(sys, "argv", ["ml", *arguments])
    with pytest.raises(SystemExit) as err:
        main()

    output = capsys.readouterr().out
    assert err.value.args[0] == 0
    assert "Available commands:" in output
    assert "env list" in output


@pytest.mark.parametrize(
    ("command", "description", "endpoint"),
    [
        (
            "eval",
            "Runs XQuery or JavaScript code",
            "Uses the /v1/eval endpoint of a REST App Server.",
        ),
        (
            "invoke",
            "Runs an XQuery or JavaScript module deployed on the server",
            "Uses the /v1/invoke endpoint of a REST App Server.",
        ),
        (
            "logs",
            "Prints MarkLogic log lines or lists log files",
            "Uses the /manage/v2/logs endpoint of the Manage App Server.",
        ),
    ],
)
def test_main_prints_command_help_with_endpoint(
    command: str,
    description: str,
    endpoint: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(sys, "argv", ["ml", command, "--help", "--no-ansi"])
    with pytest.raises(SystemExit) as err:
        main()

    output = capsys.readouterr().out
    assert err.value.args[0] == 0
    assert f"Description:\n  {description}\n" in output
    assert f"Help:\n  {endpoint}\n" in output
    assert "Available commands:" not in output
