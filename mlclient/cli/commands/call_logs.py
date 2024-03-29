"""The Call Logs Command module.

It exports an implementation for 'call logs' command:
    * CallLogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Generator, Iterator

from cleo.commands.command import Command
from cleo.helpers import option
from cleo.io.inputs.option import Option
from cleo.io.outputs.output import Type

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
          --list
            If set, no filename will be passed to the Logs REST API
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
        option(
            "list",
            description="If set, no filename will be passed to the Logs REST API",
        ),
    ]

    _NONE_SERVER_KEY: str = "AAA"

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        if self.option("list") is True:
            self._print_log_files()
        else:
            self._print_logs()
        return 0

    def _print_log_files(
        self,
    ):
        """Print MarkLogic log files in a table."""
        logs_list = self._get_logs_list()
        logs_hosts = sorted(host for host in logs_list["grouped"])
        app_port = self._get_app_port()
        self.line("")
        for logs_host in logs_hosts:
            rows = list(self._get_log_files_rows(logs_list, logs_host, app_port))
            self._render_log_files_table(logs_host, rows)

    def _get_logs_list(
        self,
    ) -> dict:
        """Retrieve logs list using LogsClient."""
        host = self.option("host")
        with self._get_logs_client() as client:
            self.info(f"Getting logs list using REST App-Server {client.base_url}")
            return client.get_logs_list(host)

    def _get_log_files_rows(
        self,
        logs_list: dict,
        host: str,
        app_port: int | str,
    ) -> Generator[list[str]]:
        """Get rows to build a table with log files."""
        grouped_logs = logs_list["grouped"]

        servers = sorted(
            server if server is not None else self._NONE_SERVER_KEY
            for server in grouped_logs[host]
            if app_port is None or str(app_port) == server
        )
        for server_index, server_key in enumerate(servers):
            server = None if server_key == self._NONE_SERVER_KEY else server_key
            yield from self._populate_rows_from_server_lvl(logs_list, host, server)

            if server_index < len(servers) - 1:
                yield self.table_separator()

    def _populate_rows_from_server_lvl(
        self,
        logs_list: dict,
        host: str,
        server: str | None,
    ) -> Generator[list[str]]:
        """Get rows with server log files."""
        grouped_logs = logs_list["grouped"]

        server_logs = grouped_logs[host][server]
        log_types = sorted(server_logs.keys())
        for log_type_index, log_type in enumerate(log_types):
            yield from self._populate_rows_from_log_type_lvl(
                logs_list,
                host,
                server,
                log_type,
            )

            if log_type_index < len(log_types) - 1:
                yield ["", ""]

    def _populate_rows_from_log_type_lvl(
        self,
        logs_list: dict,
        host: str,
        server: str | None,
        log_type: LogType,
    ) -> Generator[list[str]]:
        """Get rows with server log files of a specific type."""
        source_logs = logs_list["source"]
        grouped_logs = logs_list["grouped"]

        ml_url = self._get_logs_client().base_url

        server_logs = grouped_logs[host][server]
        type_logs = server_logs[log_type]
        for days in sorted(type_logs):
            file_name = type_logs[days]
            endpoint = next(
                log["uriref"]
                for log in source_logs
                if log["nameref"] == file_name and log["roleref"] == host
            )
            url = f"{ml_url}{endpoint}"
            yield [file_name, url]

    def _render_log_files_table(
        self,
        host: str,
        rows: list[list[str]],
    ):
        """Render a table with MarkLogic log files."""
        if len(rows) > 0:
            table = self.table()
            table.set_header_title(f"MARKLOGIC LOG FILES ({host})")
            table.set_headers(["FILENAME", "URL"])
            table.set_style("box")
            table.set_rows(rows)
            table.render()
        else:
            self.line_error("No log files found")

    def _print_logs(
        self,
    ):
        """Print MarkLogic logs."""
        logs = self._get_logs()
        parsed_logs = self._parse_logs(logs)
        self.line("")
        for info, msg in parsed_logs:
            self._io.write(info)
            self._io.write(msg, new_line=True, type=Type.RAW)

    def _get_logs(
        self,
    ) -> Iterator[dict]:
        """Retrieve logs using LogsClient."""
        app_port = self._get_app_port()
        log_type = LogType.get(self.option("log-type"))
        start_time = self.option("from")
        end_time = self.option("to")
        regex = self.option("regex")
        host = self.option("host")

        with self._get_logs_client() as client:
            if app_port is None:
                file_name = f"{log_type.value}.txt"
            else:
                file_name = f"{app_port}_{log_type.value}.txt"
            self.info(
                f"Getting {file_name} logs using REST App-Server {client.base_url}",
            )
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
    ) -> Iterator[tuple[str, str]]:
        """Parse retrieved logs depending on the log type."""
        if self.option("log-type").lower() != "error":
            for log_dict in logs:
                yield "", log_dict["message"]
        else:
            for log_dict in logs:
                timestamp = log_dict["timestamp"]
                level = log_dict["level"].upper()
                msg = log_dict["message"]
                yield f"<time>{timestamp}</> <log-level>{level}</>: ", msg

    def _get_app_port(
        self,
    ) -> int | str:
        """Identify app port to be used."""
        environment = self.option("environment")
        app_port = self.option("app-server")
        manager = MLManager(environment)
        if app_port == "0":
            app_port = "TaskServer"
        elif app_port is not None and not app_port.isnumeric():
            named_app_port = next(
                (
                    app_server.port
                    for app_server in manager.config.app_servers
                    if app_server.identifier == app_port
                ),
                None,
            )
            if named_app_port is not None:
                app_port = named_app_port
        return app_port

    def _get_logs_client(
        self,
    ):
        """Get LogsClient instance."""
        environment = self.option("environment")
        rest_server = self.option("rest-server")
        return _get_cached_logs_client(environment, rest_server)


@lru_cache
def _get_cached_logs_client(
    environment: str,
    rest_server: str,
):
    """Get cached LogsClient instance."""
    manager = MLManager(environment)
    return manager.get_logs_client(rest_server)
