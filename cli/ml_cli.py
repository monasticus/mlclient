"""The MLClient CLI module.

This module provides a Command Line Interface for ML Client.
It exports a single function:
    * main()
        Execute a MLCLIent Job using CLI.
"""

from __future__ import annotations

from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import option

from mlclient import __version__ as ml_client_version, MLManager


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
            "app-server",
            "s",
            description="The ML Client environment name",
            flag=False,
            default="manage",
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
        #     description="The start time for the log data",
        #     flag=False,
        #     value_required=False,
        # ),
        # option(
        #     "to",
        #     "t",
        #     description="The end time for the log data",
        #     flag=False,
        #     value_required=False,
        # ),
        # option(
        #     "regex",
        #     "r",
        #     description="Filters the log data, based on a regular expression",
        #     flag=False,
        #     value_required=False,
        # ),
    ]

    def handle(
            self,
    ) -> int:
        logs = self._get_logs()
        self._io.write(self._styled_logs(logs), new_line=True)
        return 0

    def _get_logs(
            self,
    ) -> list[dict]:
        manager = MLManager(self.option("environment"))
        with manager.get_resource_client(self.option("app-server")) as client:
            self.line(f"Getting logs from {client.base_url}\n")
            resp = client.get_logs(
                filename=f"{client.port}_ErrorLog.txt",
                data_format="json",
                # start_time=self.option("from"),
                # end_time=self.option("to"),
                # regex=self.option("regex"),
            )
            return resp.json()["logfile"]["log"]

    def _styled_logs(
            self,
            logs: list[dict],
    ) -> str:
        self.add_style("time", fg="green", options=["bold"])
        self.add_style("level", fg="cyan", options=["bold"])
        for log in sorted(logs, key=lambda l: l["timestamp"]):
            timestamp = log['timestamp']
            level = log['level'].upper()
            msg = log['message']
            yield f"<time>{timestamp}</> <level>{level}</>: {msg}"


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


def main() -> int:
    """Execute an ML Client Job using CLI."""
    return MLCLIentApplication().run()


if __name__ == "__main__":
    main()
