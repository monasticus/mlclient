from __future__ import annotations

import logging
import subprocess
import sys

import pytest
from cleo.formatters.style import Style
from cleo.io.buffered_io import BufferedIO
from cleo.io.outputs.buffered_output import BufferedOutput
from cleo.io.outputs.output import Verbosity

import mlclient
from mlclient.cli import MLCLIentApplication, commands, main
from mlclient.cli.app import CleoAppHandler
from mlclient.cli.commands._waiting_indicator import ERASE_LINE


@pytest.fixture(autouse=True)
def _restore_mlclient_logger():
    logger = logging.getLogger("mlclient")
    handlers, level = logger.handlers[:], logger.level
    yield
    logger.handlers, logger.level = handlers, level


def test_main_sys_exit_1(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ml", "--unknown-option"])
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 1


def test_main_sys_exit_0(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ml"])
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
    io.error_output.formatter.set_style("mlclient_fine", Style(foreground="cyan"))
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

    output = io.fetch_error()
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


def test_emit_writes_to_the_error_output():
    io = BufferedIO()
    handler = CleoAppHandler(io)
    handler.setFormatter(logging.Formatter("%(message)s"))

    handler.emit(_record(logging.WARNING, "Something to know"))

    assert io.fetch_output() == ""
    assert "Something to know" in io.fetch_error()


def test_emit_shows_info_records_only_when_verbose():
    io = BufferedIO()
    handler = CleoAppHandler(io)
    handler.setFormatter(logging.Formatter("%(message)s"))

    handler.emit(_record(logging.INFO, "Hidden"))
    io.set_verbosity(Verbosity.VERBOSE)
    handler.emit(_record(logging.INFO, "Shown"))

    error = io.fetch_error()
    assert "Shown" in error
    assert "Hidden" not in error


def test_emit_erases_the_current_line_on_a_decorated_error_output():
    io = BufferedIO(decorated=True)
    handler = CleoAppHandler(io)
    handler.setFormatter(logging.Formatter("%(message)s"))

    handler.emit(_record(logging.WARNING, "Something to know"))

    assert io.fetch_error().startswith(ERASE_LINE)


def test_create_io_styles_logs_written_to_the_error_output(mlclient_logger):
    io = MLCLIentApplication().create_io(
        output=BufferedOutput(decorated=True),
        error_output=BufferedOutput(decorated=True),
    )

    mlclient_logger.warning("Something to know")

    error = io.error_output.fetch()
    assert "Something to know" in error
    assert "\x1b[33;3m" in error
    assert "mlclient_warning" not in error


def _record(level: int, message: str) -> logging.LogRecord:
    return logging.LogRecord("mlclient", level, __file__, 1, message, None, None)


@pytest.mark.parametrize(
    ("arguments", "allowed"),
    [(["--version"], None), (["env", "list", "--help"], "env_list")],
)
def test_cli_only_imports_the_requested_command(arguments, allowed):
    script = """
import importlib.abc
import sys

class SelectedCommandOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("mlclient.cli.commands."):
            module = fullname.rsplit(".", 1)[-1]
            if not module.startswith("_") and module != ALLOWED:
                raise RuntimeError("Unselected command imported: " + fullname)
        return None

sys.meta_path.insert(0, SelectedCommandOnly())
from mlclient.cli import main
sys.argv = ["ml", *ARGUMENTS]
main()
"""
    script = f"ALLOWED = {allowed!r}\nARGUMENTS = {arguments!r}\n" + script
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if allowed is None:
        assert result.stdout == f"MLCLIent (version {mlclient.__version__})\n"
    else:
        assert "env list" in result.stdout


def test_command_package_preserves_class_exports_and_discovery():
    expected = [
        "EnvCompareCommand",
        "EnvCopyCommand",
        "EnvEditCommand",
        "EnvInitCommand",
        "EnvListCommand",
        "EnvRemoveCommand",
        "EnvShowCommand",
        "EvalCommand",
        "HealthCommand",
        "HttpCommand",
        "InvokeCommand",
        "LogLevelCommand",
        "LogsCommand",
        "SampleCommand",
        "UrlCommand",
        "VersionCommand",
    ]
    assert commands.__all__ == expected
    for name in expected:
        assert name in dir(commands)
        command_type = getattr(commands, name)
        command = command_type()
        assert type(MLCLIentApplication().find(command.name)) is command_type

    with pytest.raises(AttributeError, match="MissingCommand") as error:
        _ = commands.MissingCommand
    assert str(error.value) == (
        "module 'mlclient.cli.commands' has no attribute 'MissingCommand'"
    )
