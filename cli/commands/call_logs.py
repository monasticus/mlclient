"""The Call Logs Command module.

It exports an implementation for 'call logs' command:
    * CallLogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
"""
from __future__ import annotations

from typing import Iterator

from cleo.commands.command import Command
from cleo.helpers import option
from cleo.io.inputs.option import Option

from mlclient import MLManager
from mlclient.clients import LogType


class CallLogsCommand(Command):
    """Sends a GET request to the /manage/v2/logs endpoint.

    Usage:
      call logs [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -a, --app-server=APP-PORT
            The App-Server (port) to get logs of
      -s, --rest-server=REST-SERVER
            The ML REST Server environmental id (to get logs from)
      -l, --log-type=LOG-TYPE
            MarkLogic log type (error, access or request) [default: "error"]
      -f, --from=FROM
            A start time to search error logs
      -t, --to=TO
            n end time to search error logs
      -r, --regex=REGEX
            A regex to search error logs
      -H, --host=HOST
            The host from which to return the log data.
    """

    name: str = "call logs"
    description: str = "Sends a GET request to the /manage/v2/logs endpoint"
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "app-server",
            "a",
            description="The App-Server (port) to get logs of",
            flag=False,
        ),
        option(
            "rest-server",
            "s",
            description="The ML REST Server environmental id (to get logs from)",
            flag=False,
        ),
        option(
            "log-type",
            "l",
            description="MarkLogic log type (error, access or request)",
            flag=False,
            default="error",
        ),
        option(
            "from",
            "f",
            description="A start time to search error logs",
            flag=False,
        ),
        option(
            "to",
            "t",
            description="n end time to search error logs",
            flag=False,
        ),
        option(
            "regex",
            "r",
            description="A regex to search error logs",
            flag=False,
        ),
        option(
            "host",
            "H",
            description="The host from which to return the log data.",
            flag=False,
        ),
    ]

    def handle(
            self,
    ) -> int:
        """Execute the command."""
        logs = self._get_logs()
        parsed_logs = self._parse_logs(logs)
        self._io.write(parsed_logs, new_line=True)
        return 0

    def _get_logs(
            self,
    ) -> Iterator[dict]:
        """Retrieve logs using LogsClient."""
        environment = self.option("environment")
        rest_server = self.option("rest-server")
        app_port = self.option("app-server")
        log_type = LogType.get(self.option("log-type"))
        start_time = self.option("from")
        end_time = self.option("to")
        regex = self.option("regex")
        host = self.option("host")

        manager = MLManager(environment)
        with manager.get_logs_client(rest_server) as client:
            self.info(f"Getting {app_port}_{log_type.value}.txt logs "
                      f"using REST App-Server {client.base_url}\n")
            return client.get_logs(
                app_server=app_port,
                log_type=log_type,
                start_time=start_time,
                end_time=end_time,
                regex=regex,
                host=host,
            )

    def _parse_logs(
            self,
            logs: Iterator[dict],
    ) -> Iterator[str]:
        """Parse retrieved logs depending on the type."""
        if self.option("log-type").lower() != "error":
            for log_dict in logs:
                yield log_dict["message"]
        else:
            for log_dict in logs:
                timestamp = log_dict["timestamp"]
                level = log_dict["level"].upper()
                msg = log_dict["message"]
                yield f"<time>{timestamp}</> <log-level>{level}</>: {msg}"
