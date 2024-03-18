"""The MLClient CLI module.

This module provides the ML Client Command Line Application.
It exports a single class and single function:

    * MLCLIentApplication
        An ML Client Command Line Cleo Application.

    * main()
        Run an MLCLIent Application.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from cleo.application import Application
from cleo.formatters.style import Style
from cleo.io.inputs.input import Input
from cleo.io.io import IO
from cleo.io.outputs.output import Output, Verbosity

from mlclient import __version__ as ml_client_version
from mlclient import setup_logger
from mlclient.cli.commands import CallEvalCommand, CallLogsCommand


class MLCLIentApplication(Application):
    """An ML Client Command Line Cleo Application."""

    _APP_NAME = "ml"
    _DISPLAY_NAME = "MLCLIent"

    def __init__(
        self,
    ):
        """Initialize MLCLIentApplication instance."""
        super().__init__(self._APP_NAME, ml_client_version)
        self.set_display_name(self._DISPLAY_NAME)
        self.add(CallLogsCommand())
        self.add(CallEvalCommand())

    def create_io(
        self,
        input: Input | None = None,
        output: Output | None = None,
        error_output: Output | None = None,
    ) -> IO:
        """Initialize io with custom styles."""
        io = super().create_io(input, output, error_output)

        formatter = io.output.formatter
        formatter.set_style("time", Style(foreground="green", options=["bold"]))
        formatter.set_style("log-level", Style(foreground="cyan", options=["bold"]))

        CleoAppHandler.setup_for(io)
        return io


class CleoAppHandler(logging.Handler):
    """A logger handler integrating ML Client  logs with the Cleo Application."""

    _LEVELS: ClassVar[dict] = {
        logging.CRITICAL: {
            "verbosity": Verbosity.NORMAL,
            "style": "mlclient_critical",
        },
        logging.ERROR: {
            "verbosity": Verbosity.NORMAL,
            "style": "mlclient_error",
        },
        logging.WARNING: {
            "verbosity": Verbosity.NORMAL,
            "style": "mlclient_warning",
        },
        logging.INFO: {
            "verbosity": Verbosity.VERBOSE,
            "style": "mlclient_info",
        },
        logging.DEBUG: {
            "verbosity": Verbosity.VERY_VERBOSE,
            "style": "mlclient_debug",
        },
        logging.FINE: {
            "verbosity": Verbosity.DEBUG,
            "style": "mlclient_fine",
        },
    }

    def __init__(
        self,
        io: IO,
        level: int = logging.NOTSET,
    ):
        """Initialize CleoAppHandler instance."""
        super().__init__(level=level)
        self.io = io

    def emit(
        self,
        record: logging.LogRecord,
    ):
        """Emit a LogRecord."""
        verbosity = self._LEVELS[record.levelno]["verbosity"]
        style = self._LEVELS[record.levelno]["style"]
        styled_text = f"<{style}>{self.format(record)}</>"
        self.io.write_line(styled_text, verbosity=verbosity)

    @classmethod
    def setup_for(
        cls,
        io: IO,
    ):
        """Set up MLClient logs handler and format for an IO."""
        options = ["italic"]
        formatter = io.output.formatter
        formatter.set_style("mlclient_fine", Style(foreground="cyan", options=options))
        formatter.set_style(
            "mlclient_debug",
            Style(foreground="light_cyan", options=options),
        )
        formatter.set_style(
            "mlclient_info",
            Style(foreground="light_green", options=options),
        )
        formatter.set_style(
            "mlclient_warning",
            Style(foreground="yellow", options=options),
        )
        formatter.set_style("mlclient_error", Style(foreground="red", options=options))
        formatter.set_style(
            "mlclient_critical",
            Style(foreground="light_red", options=options),
        )

        logger = logging.getLogger("mlclient")
        origin_handler = next(h for h in logger.handlers if h.name == "console")
        origin_formatter = origin_handler.formatter

        cleo_handler = cls(io)
        cleo_handler.setFormatter(origin_formatter)

        logger.setLevel(logging.FINE)
        logger.handlers = [cleo_handler]


def main() -> int:
    """Run an MLCLIent Application."""
    setup_logger()
    return MLCLIentApplication().run()


if __name__ == "__main__":
    main()
