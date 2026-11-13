from __future__ import annotations

import logging
import sys

import pytest
from cleo.formatters.style import Style
from cleo.io.buffered_io import BufferedIO
from cleo.io.outputs.buffered_output import BufferedOutput
from cleo.io.outputs.output import Verbosity

import mlclient
from mlclient.cli import MLCLIentApplication, main
from mlclient.cli.app import CleoAppHandler
from mlclient.cli.commands._waiting_indicator import ERASE_LINE


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
