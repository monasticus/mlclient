"""The MLClient CLI module.

This module provides a Command Line Interface for ML Client.
It exports a single function:
    * main()

        Execute a MLCLIent Job using CLI.
"""

from __future__ import annotations

from cleo.application import Application
from cleo.formatters.style import Style
from cleo.io.inputs.input import Input
from cleo.io.io import IO
from cleo.io.outputs.output import Output

from cli.commands import CallLogsCommand
from mlclient import __version__ as ml_client_version


class MLCLIentApplication(Application):
    """An ML Client Command Line Application."""

    _APP_NAME = "MLCLIent"

    def __init__(
            self,
    ):
        """Initialize MLCLIentApplication instance."""
        super().__init__(self._APP_NAME, ml_client_version)
        self.add(CallLogsCommand())

    @property
    def display_name(self) -> str:
        """The application name to display."""
        return self._name

    def create_io(
            self,
            input: Input | None = None,
            output: Output | None = None,
            error_output: Output | None = None,
    ) -> IO:
        io = super().create_io(input, output, error_output)

        formatter = io.output.formatter
        formatter.set_style("time", Style(foreground="green", options=["bold"]))
        formatter.set_style("log-level", Style(foreground="cyan", options=["bold"]))

        return io


def main() -> int:
    """Execute an ML Client Job using CLI."""
    return MLCLIentApplication().run()


if __name__ == "__main__":
    main()
