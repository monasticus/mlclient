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

        CliKitHandler.setup_for(io)
        return io


class CliKitHandler(logging.Handler):
    _LEVELS: ClassVar[dict] = {
        logging.CRITICAL: Verbosity.NORMAL,
        logging.ERROR: Verbosity.NORMAL,
        logging.WARNING: Verbosity.NORMAL,
        logging.INFO: Verbosity.VERY_VERBOSE,
        logging.DEBUG: Verbosity.DEBUG,
    }

    def __init__(self, io: IO, level=logging.NOTSET):
        super().__init__(level=level)
        self.io = io

    def emit(self, record: logging.LogRecord):
        text = record.getMessage()
        level = self._LEVELS[record.levelno]
        if record.levelno >= logging.WARNING:
            self.io.write_error_line(text, verbosity=level)
        else:
            self.io.write_line(text, verbosity=level)

    @classmethod
    def setup_for(cls, io: IO):
        log = logging.getLogger("mlclient")
        log.setLevel(logging.DEBUG)
        log.handlers = [cls(io)]


def main() -> int:
    """Run an MLCLIent Application."""
    return MLCLIentApplication().run()


if __name__ == "__main__":
    main()
