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
import sys
from functools import partial
from importlib import import_module
from typing import TYPE_CHECKING, ClassVar, cast

from cleo.application import Application
from cleo.formatters.formatter import Formatter
from cleo.formatters.style import Style
from cleo.io.inputs.argv_input import ArgvInput
from cleo.io.inputs.input import Input
from cleo.io.io import IO
from cleo.io.outputs.output import Output, Verbosity
from cleo.loaders.factory_command_loader import FactoryCommandLoader

from mlclient._version import __version__ as ml_client_version
from mlclient.cli.commands import COMMANDS
from mlclient.cli.commands._waiting_indicator import ERASE_LINE
from mlclient.logging import setup_logger

if TYPE_CHECKING:
    from cleo.commands.command import Command


class MLCLIentApplication(Application):
    """An ML Client Command Line Cleo Application."""

    _APP_NAME = "ml"
    _DISPLAY_NAME = "MLCLIent"

    def __init__(
        self,
    ) -> None:
        """Initialize MLCLIentApplication instance."""
        super().__init__(self._APP_NAME, ml_client_version)
        self.set_display_name(self._DISPLAY_NAME)
        self.set_command_loader(
            FactoryCommandLoader(
                {
                    name: partial(_load_command, target)
                    for name, target in COMMANDS.items()
                },
            ),
        )

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
        logging.FINE: {  # type: ignore[attr-defined]
            "verbosity": Verbosity.DEBUG,
            "style": "mlclient_fine",
        },
    }

    def __init__(
        self,
        io: IO,
        level: int = logging.NOTSET,
    ) -> None:
        """Initialize CleoAppHandler instance."""
        super().__init__(level=level)
        self.io = io

    def emit(
        self,
        record: logging.LogRecord,
    ) -> None:
        """Emit a LogRecord."""
        verbosity = self._LEVELS[record.levelno]["verbosity"]
        style = self._LEVELS[record.levelno]["style"]
        styled_text = f"<{style}>{Formatter.escape(self.format(record))}</>"
        if self.io.error_output.is_decorated():
            # A waiting indicator may occupy the current line of a terminal.
            styled_text = ERASE_LINE + styled_text
        self.io.write_error_line(styled_text, verbosity=verbosity)

    @classmethod
    def setup_for(
        cls,
        io: IO,
    ) -> None:
        """Set up MLClient logs handler and format for an IO.

        Logs go to the error output; their styles are registered on both
        outputs because cleo keeps a separate formatter per stream.
        """
        options = ["italic"]
        for formatter in (io.output.formatter, io.error_output.formatter):
            formatter.set_style(
                "mlclient_fine",
                Style(foreground="cyan", options=options),
            )
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
            formatter.set_style(
                "mlclient_error",
                Style(foreground="red", options=options),
            )
            formatter.set_style(
                "mlclient_critical",
                Style(foreground="light_red", options=options),
            )

        logger = logging.getLogger("mlclient")
        origin_handler = next(h for h in logger.handlers if h.name == "console")
        origin_formatter = origin_handler.formatter

        cleo_handler = cls(io)
        cleo_handler.setFormatter(origin_formatter)

        logger.setLevel(
            logging.FINE,  # type: ignore[attr-defined]
        )
        logger.handlers = [cleo_handler]


def main() -> int:
    """Run an MLCLIent Application."""
    setup_logger()
    return MLCLIentApplication().run(_command_line_input())


def _command_line_input() -> ArgvInput:
    """Read the command line, running ``list`` for a bare ``-h`` or ``--help``.

    cleo would print the help of the ``list`` command instead of the list itself.
    """
    script, *arguments = sys.argv
    if arguments in (["-h"], ["--help"]):
        arguments = ["list"]
    return ArgvInput([script, *arguments])


def _load_command(target: str) -> Command:
    """Import and construct one registered command when Cleo requests it.

    Parameters
    ----------
    target : str
        Fully qualified command class from the command registry.

    Returns
    -------
    Command
        A new instance of the selected command.

    Raises
    ------
    ImportError
        If the registered command module cannot be imported.
    AttributeError
        If its registered class is missing.
    """
    module_name, class_name = target.rsplit(".", 1)
    command = cast("type[Command]", getattr(import_module(module_name), class_name))
    return command()


if __name__ == "__main__":
    main()
