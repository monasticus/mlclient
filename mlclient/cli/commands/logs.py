"""The Logs Command module.

It exports an implementation for 'logs' command:
    * LogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
"""

from __future__ import annotations

import asyncio
import heapq
from collections.abc import Generator, Iterator
from functools import lru_cache
from typing import ClassVar

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import option
from cleo.io.inputs.option import Option
from cleo.io.outputs.output import Type
from dateutil.parser import isoparse

from mlclient._manager import MLClientManager
from mlclient.exceptions import WrongParametersError
from mlclient.models.types import LogType
from mlclient.responses import MLResponseParser
from mlclient.services.logs import AsyncLogsService, LogsService


class LogsCommand(Command):
    """Sends a GET request to the /manage/v2/logs endpoint.

    Usage:
      logs [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -s, --server=APP-PORT
            App Server identifier from the environment or port to read logs for
      -l, --log-type=LOG-TYPE
            MarkLogic log type (error, access or request) [default: "error"]
      -f, --from=FROM
            A start time to search error logs
      -t, --to=TO
            An end time to search error logs
      -r, --regex=REGEX
            A regex to search error logs
      -H, --host=HOST
            The host from which to return the log data.
          --list
            If set, no filename will be passed to the Logs REST API
          --all-hosts
            Aggregate error logs from every cluster host, merged by timestamp
            (error log type only)
    """

    name: str = "logs"
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
            "server",
            "s",
            description="App Server identifier from the environment or port",
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
            description="An end time to search error logs",
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
        option(
            "all-hosts",
            description="Aggregate error logs from every cluster host, "
            "merged by timestamp (error log type only)",
        ),
    ]

    _NONE_SERVER_KEY: str = "AAA"

    # ANSI-256 codes (all >= 16, so disjoint from the app's named styles),
    # ordered for maximum contrast between adjacent hosts. Cycled when a
    # cluster has more hosts than colors.
    _HOST_COLORS: ClassVar[tuple[int, ...]] = (
        208, 38, 205, 149, 99, 214, 75, 211, 79, 135,
        166, 105, 178, 43, 213, 69, 202, 115, 177, 137,
        174, 141, 101, 209, 172,
    )

    def handle(
        self,
    ) -> int:
        """Execute the selected log operation.

        Raises
        ------
        WrongParametersError
            If --all-hosts is combined with --host, --list or a non-error log type.
        """
        if self.option("all-hosts") and (
            self.option("host") is not None or self.option("list")
        ):
            msg = "The --all-hosts option cannot be combined with --host or --list"
            raise WrongParametersError(msg)
        if self.option("list") is True:
            self._print_log_files()
        elif self.option("all-hosts") is True:
            self._print_logs_all_hosts()
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
        """Retrieve logs list using the Logs service."""
        host = self.option("host")
        with _get_cached_client(self.option("environment")) as ml:
            self.info(f"Getting logs list using REST App-Server {ml.http.base_url}")
            return LogsService(ml.manage).list(host)

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

        ml_url = _get_cached_client(self.option("environment")).http.base_url

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

    def _print_logs_all_hosts(
        self,
    ):
        """Print error logs from every cluster host, merged by timestamp.

        Each host is shown in parentheses between the log level and the
        message, colored by host on a decorated output. Restricted to the
        error log type: access, request and audit logs are served as a single
        opaque message stream that carries no timestamp to merge on.

        Raises
        ------
        WrongParametersError
            If the requested log type is not error.
        """
        if self.option("log-type").lower() != "error":
            msg = "The --all-hosts option supports the error log type only"
            raise WrongParametersError(msg)
        colors, per_host_logs = asyncio.run(self._collect_all_hosts_logs())
        self.line("")
        for log_dict in heapq.merge(
            *per_host_logs,
            key=lambda log: isoparse(log["timestamp"]),
        ):
            timestamp = log_dict["timestamp"]
            level = log_dict["level"].upper()
            host = self._format_host(log_dict["host"], colors[log_dict["host"]])
            info = f"<time>{timestamp}</> <log-level>{level}</> {host}: "
            self._io.write(info)
            self._io.write(log_dict["message"], new_line=True, type=Type.RAW)

    async def _collect_all_hosts_logs(
        self,
    ) -> tuple[dict[str, int], list[Iterator[dict]]]:
        """Fetch error logs from every cluster host concurrently.

        Cancel and await outstanding reads before closing the shared client,
        including when a host fails or the operation is interrupted.

        Returns
        -------
        tuple[dict[str, int], list[Iterator[dict]]]
            A host-to-color mapping and one per-host generator of error logs,
            each already sorted by timestamp and tagged with its host name.
        """
        env = self.option("environment")
        app_port = self._get_app_port()
        async with MLClientManager(env).get_async_client("manage") as ml:
            self.info(
                f"Getting error logs from every host using "
                f"REST App-Server {ml.http.base_url}",
            )
            hosts = await self._get_hosts(ml)
            self._warn_if_unfiltered(hosts)
            colors = {
                host: self._HOST_COLORS[index % len(self._HOST_COLORS)]
                for index, host in enumerate(hosts)
            }
            return colors, await self._fetch_hosts_logs(ml, hosts, app_port)

    @staticmethod
    async def _get_hosts(
        ml,
    ) -> list[str]:
        """Return every host name in the cluster.

        Parameters
        ----------
        ml : AsyncMLClient
            A connected async client targeting the manage App Server.

        Returns
        -------
        list[str]
            Host names as reported by /manage/v2/hosts.

        Raises
        ------
        MarkLogicError
            If MarkLogic rejects host discovery.
        """
        resp = await ml.manage.hosts.get_list(data_format="json")
        MLResponseParser.raise_for_status(resp)
        body = resp.json()
        list_items = body["host-default-list"]["list-items"].get("list-item", [])
        return [item["nameref"] for item in list_items]

    def _warn_if_unfiltered(
        self,
        hosts: list[str],
    ):
        """Warn when reading unfiltered error logs from more than one host.

        An unfiltered read fetches every error entry from every host, which can
        be a large volume and may time out. A single host is left alone -- it is
        the same load as a plain ``logs`` call.

        Parameters
        ----------
        hosts : list[str]
            The cluster host names about to be queried.
        """
        has_filter = any(
            self.option(name) is not None for name in ("from", "to", "regex")
        )
        if len(hosts) > 1 and not has_filter:
            self.line_error(
                f"Reading unfiltered error logs from {len(hosts)} hosts may "
                "return a large volume and can time out. Consider narrowing "
                "with --from, --to or --regex.",
                style="fg=yellow;options=dark",
            )

    async def _fetch_hosts_logs(
        self,
        ml,
        hosts: list[str],
        app_port: int | str | None,
    ) -> list[Iterator[dict]]:
        """Read host logs concurrently, cancelling outstanding reads on failure.

        Parameters
        ----------
        ml : AsyncMLClient
            The connected client shared by all reads.
        hosts : list[str]
            The hosts to read error logs from.
        app_port : int | str | None
            The resolved App Server port or TaskServer; None selects ErrorLog.txt.

        Returns
        -------
        list[Iterator[dict]]
            Sorted, host-tagged logs in the same order as the requested hosts.

        Raises
        ------
        BaseException
            Propagates the original failure or cancellation after awaiting cleanup.
        """
        tasks = [
            asyncio.create_task(self._fetch_host_logs(ml, host, app_port))
            for host in hosts
        ]
        try:
            return await asyncio.gather(*tasks)
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    async def _fetch_host_logs(
        self,
        ml,
        host: str,
        app_port: int | str | None,
    ) -> Iterator[dict]:
        """Fetch error logs from a single host, tagged with the host name.

        Parameters
        ----------
        ml : AsyncMLClient
            A connected async client targeting the manage App Server.
        host : str
            The host to read error logs from.
        app_port : int | str | None
            The resolved App Server port or TaskServer; None selects ErrorLog.txt.

        Returns
        -------
        Iterator[dict]
            Error logs sorted by timestamp, each carrying a ``host`` key.
        """
        logs = await AsyncLogsService(ml.manage).get(
            app_port,
            LogType.ERROR,
            start_time=self.option("from"),
            end_time=self.option("to"),
            regex=self.option("regex"),
            host=host,
        )
        return ({**log, "host": host} for log in logs)

    def _format_host(
        self,
        host: str,
        color: int,
    ) -> str:
        """Render the parenthesized host tag, colored on a decorated output.

        The parentheses take the host color; the host name itself is italic to
        sit quietly beside the message. On a non-decorated output (a pipe, a
        file or a test) the raw escapes would survive as literal text -- cleo
        strips its own tags but not arbitrary escapes -- so a plain ``(host)``
        is returned instead.

        Parameters
        ----------
        host : str
            The host name to render.
        color : int
            An ANSI-256 foreground color code.

        Returns
        -------
        str
            The parenthesized host tag, colored when the output is decorated.
        """
        host = Formatter.escape(host)
        if not self._io.output.is_decorated():
            return f"({host})"
        return f"\x1b[38;5;{color}m(\x1b[3m{host}\x1b[23m)\x1b[39m"

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
        """Retrieve logs using the Logs service."""
        app_port = self._get_app_port()
        log_type = LogType.get(self.option("log-type"))
        start_time = self.option("from")
        end_time = self.option("to")
        regex = self.option("regex")
        host = self.option("host")

        with _get_cached_client(self.option("environment")) as ml:
            if app_port is None:
                file_name = f"{log_type.value}.txt"
            else:
                file_name = f"{app_port}_{log_type.value}.txt"
            self.info(
                f"Getting {file_name} logs using REST App-Server {ml.http.base_url}",
            )
            return LogsService(ml.manage).get(
                app_port,
                log_type,
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
    ) -> int | str | None:
        """Identify app port to be used."""
        env = self.option("environment")
        app_port = self.option("server")
        mgr = MLClientManager(env)
        if app_port in {"0", "TaskServer"}:
            app_port = "TaskServer"
        elif app_port is not None and not app_port.isnumeric():
            app_port = mgr.get_config(app_port).port
        return app_port


@lru_cache
def _get_cached_client(
    env_name: str,
):
    # Cached to avoid re-reading config and re-creating the client on every
    # call -- _get_client() is invoked multiple times (e.g. in --list loops).
    return MLClientManager(env_name).get_client()
