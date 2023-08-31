"""The MLClient CLI module.

This module provides a Command Line Interface for ML Client.
It exports a single function:
    * main()
        Execute a MLCLIent Job using CLI.
"""

from __future__ import annotations

from typing import Iterator

from cleo.application import Application
from cleo.commands.command import Command
from cleo.formatters.style import Style
from cleo.helpers import option
from cleo.io.inputs.input import Input
from cleo.io.io import IO
from cleo.io.outputs.output import Output

from mlclient import MLManager
from mlclient import __version__ as ml_client_version


class CallLogsCommand(Command):
    """
    Sends a GET request to the /manage/v2/logs endpoint

    call logs
        {--e|environment=local : The ML Client environment name}
    """

    name = "call logs"
    description = "Sends a GET request to the /manage/v2/logs endpoint"
    options = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "app-port",
            "p",
            description="The App-Server port to get logs from",
            flag=False,
        ),
        option(
            "rest-server",
            "s",
            description="The ML REST Server environmental id",
            flag=False,
        ),
        # option(
        #     "log-type",
        #     "l",
        #     description="MarkLogic logs type",
        #     flag=False,
        #     default="error",
        # ),
        # option(
        #     "from",
        #     "f",
        #     description="The start time for the error log data",
        #     flag=False,
        #     value_required=False,
        # ),
        # option(
        #     "to",
        #     "t",
        #     description="The end time for the error log data",
        #     flag=False,
        #     value_required=False,
        # ),
        # option(
        #     "regex",
        #     "r",
        #     description="Filters the error log data, based on a regular expression",
        #     flag=False,
        #     value_required=False,
        # ),
    ]

    def handle(
            self,
    ) -> int:
        logs = self._get_logs()
        styled_logs = self._styled_logs(logs)
        self._io.write(styled_logs, new_line=True)
        return 0

    def _get_logs(
            self,
    ) -> Iterator[dict]:
        environment = self.option("environment")
        rest_server = self.option("rest-server")
        app_port = int(self.option("app-port"))
        # start_time = self.option("from")
        # end_time = self.option("to")
        # regex = self.option("regex")
        manager = MLManager(environment)
        with manager.get_logs_client(rest_server) as client:
            self.line(f"Getting [{app_port}] logs using REST App-Server {client.base_url}\n")
            return client.get_logs(
                app_server_port=app_port,
                # start_time=self.option("from"),
                # end_time=self.option("to"),
                # regex=self.option("regex"),
            )

    @staticmethod
    def _styled_logs(
            logs: Iterator[dict],
    ) -> Iterator[str]:
        for log_dict in sorted(logs, key=lambda log: log["timestamp"]):
            timestamp = log_dict["timestamp"]
            level = log_dict["level"].upper()
            msg = log_dict["message"]
            yield f"<time>{timestamp}</> <log-level>{level}</>: {msg}"


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
