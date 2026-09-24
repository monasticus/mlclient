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
