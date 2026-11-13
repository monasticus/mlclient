"""The Logs Command module.

It exports an implementation for 'logs' command:
    * LogsCommand
        Sends a GET request to the /manage/v2/logs endpoint.
"""

from __future__ import annotations

import asyncio
import heapq
from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING, ClassVar

from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import option
from cleo.io.inputs.option import Option
from cleo.io.outputs.output import Type
from dateutil.parser import isoparse
from httpx import HTTPError

from mlclient._manager import MLClientManager
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.models.types import LogType
from mlclient.responses import MLResponseParser
from mlclient.services.diagnostics.logs import AsyncLogsService, LogsService


if TYPE_CHECKING:
    from cleo.ui.table_separator import TableSeparator

    from mlclient._client import AsyncMLClient


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

    _MISSING_LOG_HINT: str = (
        "No {file_name} yet - MarkLogic creates it when the server first logs "
        "something. Run 'ml logs --list' to see the existing log files."
    )

    # ANSI-256 codes (all >= 16, so disjoint from the app's named styles),
    # ordered for maximum contrast between adjacent hosts. Cycled when a
    # cluster has more hosts than colors.
    _HOST_COLORS: ClassVar[tuple[int, ...]] = (
        208,
        38,
        205,
        149,
        99,
        214,
        75,
        211,
        79,
        135,
        166,
        105,
        178,
        43,
        213,
        69,
        202,
        115,
        177,
        137,
        174,
        141,
        101,
        209,
        172,
    )

    def handle(
        self,
    ) -> int:
        """Execute the selected log operation.

        Returns
        -------
        int
            0 for a complete result, 1 when the log file does not exist yet
            or all-host logs are incomplete.

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
            return self._print_logs_all_hosts()
        else:
            return self._print_logs()
        return 0

    def _print_log_files(
        self,
    ) -> None:
        """Print MarkLogic log files and their Management API download URLs."""
        manager = MLClientManager(self.option("environment"))
        with manager.get_client("manage") as ml:
            self.info(f"Getting logs list using Manage App-Server {ml.http.base_url}")
            logs_list = LogsService(ml.manage).list(self.option("host"))
            base_url = ml.http.base_url
        app_port = self._get_app_port(manager)
        self.line("")
        for host in sorted(logs_list["grouped"]):
            rows = list(self._get_log_files_rows(logs_list, host, app_port, base_url))
            self._render_log_files_table(host, rows)

    def _get_log_files_rows(
        self,
        logs_list: dict,
        host: str,
        app_port: int | str | None,
        base_url: str,
    ) -> Generator[list[str] | TableSeparator]:
        """Build a host's file rows, keeping the server sections separated.

        Parameters
        ----------
        logs_list : dict
            Parsed source entries and grouped log files from the Logs service.
        host : str
            The host whose files to show.
        app_port : int | str | None
            Selected App Server port or TaskServer; None includes all servers.
        base_url : str
            Base URL of the connection used to retrieve the files.

        Yields
        ------
        list[str] | TableSeparator
            Filename and URL cells, with separators between server sections.
        """
        grouped_logs = logs_list["grouped"][host]
        log_urls = {}
        for log in logs_list["source"]:
            if log["roleref"] == host:
                log_urls.setdefault(log["nameref"], f"{base_url}{log['uriref']}")
        servers = sorted(
            server if server is not None else self._NONE_SERVER_KEY
            for server in grouped_logs
            if app_port is None or str(app_port) == server
        )
        for index, server_key in enumerate(servers):
            server = None if server_key == self._NONE_SERVER_KEY else server_key
            yield from self._get_server_log_rows(grouped_logs[server], log_urls)
            if index < len(servers) - 1:
                yield self.table_separator()

    @staticmethod
    def _get_server_log_rows(
        server_logs: dict,
        log_urls: dict[str, str],
    ) -> Generator[list[str]]:
        """Build a server's file rows, separating the log types with blank rows.

        Parameters
        ----------
        server_logs : dict
            Files grouped by log type and rotation day.
        log_urls : dict[str, str]
            Download URLs indexed by filename for the selected host.

        Yields
        ------
        list[str]
            Filename and URL cells, or a blank row between log types.
        """
        log_types = sorted(server_logs)
        for index, log_type in enumerate(log_types):
            files = server_logs[log_type]
            for day in sorted(files):
                filename = files[day]
                yield [filename, log_urls[filename]]
            if index < len(log_types) - 1:
                yield ["", ""]

    def _render_log_files_table(
        self,
        host: str,
        rows: list[list[str] | TableSeparator],
    ) -> None:
        """Render a host's file table or report that no matching files exist.

        Parameters
        ----------
        host : str
            Host name shown in the table title.
        rows : list[list[str] | TableSeparator]
            Filename/URL rows and separators between server sections.
        """
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
    ) -> int:
        """Print error logs from every cluster host, merged by timestamp.

        Each host is shown in parentheses between the log level and the
        message, colored by host on a decorated output. Restricted to the
        error log type: access, request and audit logs are served as a single
        opaque message stream that carries no timestamp to merge on.

        Returns
        -------
        int
            0 when every host was read, 1 when some host logs are missing.

        Raises
        ------
        WrongParametersError
            If the requested log type is not error.
        """
        if self.option("log-type").lower() != "error":
            msg = "The --all-hosts option supports the error log type only"
            raise WrongParametersError(msg)
        manager = MLClientManager(self.option("environment"))
        app_port = self._get_app_port(manager)
        colors, per_host_logs, failures = asyncio.run(
            self._collect_all_hosts_logs(manager, app_port),
        )
        self._write_merged_logs(colors, per_host_logs)
        if failures:
            self.line_error("\nLogs are incomplete; missing hosts:", style="fg=yellow")
            for host, reason in failures.items():
                self.line_error(
                    f"  {Formatter.escape(host)}: {Formatter.escape(reason)}",
                    style="fg=yellow",
                )
        if any(self._is_missing_log(reason) for reason in failures.values()):
            self._hint_missing_log(self._log_file_name(app_port, LogType.ERROR))
        return 1 if failures else 0

    def _write_merged_logs(
        self,
        colors: dict[str, int],
        per_host_logs: list[Iterator[dict]],
    ) -> None:
        """Write the available host logs as one timeline.

        Parameters
        ----------
        colors : dict[str, int]
            The color assigned to each host.
        per_host_logs : list[Iterator[dict]]
            Timestamp-sorted entries tagged with their host names.
        """
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
        manager: MLClientManager,
        app_port: int | str | None,
    ) -> tuple[dict[str, int], list[Iterator[dict]], dict[str, str]]:
        """Collect available host logs and reasons for missing hosts.

        Expected host errors do not interrupt other reads. Unexpected failures
        and cancellation still cancel and await outstanding requests before
        closing the shared client.

        Parameters
        ----------
        manager : MLClientManager
            The manager used for this command's connection.
        app_port : int | str | None
            The resolved App Server port or TaskServer; None selects ErrorLog.txt.

        Returns
        -------
        tuple[dict[str, int], list[Iterator[dict]], dict[str, str]]
            Host colors, sorted and host-tagged logs from successful reads,
            and failed host names mapped to their error messages.
        """
        async with manager.get_async_client("manage") as ml:
            self.info(
                f"Getting error logs from every host using "
                f"Manage App-Server {ml.http.base_url}",
            )
            hosts = await self._get_hosts(ml)
            self._warn_if_unfiltered(hosts)
            colors = {
                host: self._HOST_COLORS[index % len(self._HOST_COLORS)]
                for index, host in enumerate(hosts)
            }
            results = await self._fetch_hosts_logs(ml, hosts, app_port)
            per_host_logs = []
            failures = {}
            for host, result in zip(hosts, results):
                if isinstance(result, (HTTPError, MarkLogicError)):
                    failures[host] = str(result) or type(result).__name__
                else:
                    per_host_logs.append(result)
            return colors, per_host_logs, failures

    @staticmethod
    async def _get_hosts(
        ml: AsyncMLClient,
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
    ) -> None:
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
        ml: AsyncMLClient,
        hosts: list[str],
        app_port: int | str | None,
    ) -> list[Iterator[dict] | HTTPError | MarkLogicError]:
        """Read hosts concurrently, retaining expected per-host errors.

        Unexpected failures or cancellation cancel and await outstanding reads.

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
        list[Iterator[dict] | HTTPError | MarkLogicError]
            Host-tagged logs or a request error, in requested host order.

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
        ml: AsyncMLClient,
        host: str,
        app_port: int | str | None,
    ) -> Iterator[dict] | HTTPError | MarkLogicError:
        """Fetch a host's tagged logs, retaining expected request failures.

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
        Iterator[dict] | HTTPError | MarkLogicError
            Sorted, host-tagged logs, or the HTTP/MarkLogic error for this host.
        """
        try:
            logs = await AsyncLogsService(ml.manage).get(
                app_port,
                LogType.ERROR,
                start_time=self.option("from"),
                end_time=self.option("to"),
                regex=self.option("regex"),
                host=host,
            )
        except (HTTPError, MarkLogicError) as error:
            return error
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
    ) -> int:
        """Print MarkLogic logs.

        Returns
        -------
        int
            0 when the logs were printed, 1 when the log file does not exist yet.

        Raises
        ------
        HTTPError
            If the HTTP request fails.
        MarkLogicError
            If MarkLogic rejects the log read for another reason than a missing
            log file.
        """
        manager = MLClientManager(self.option("environment"))
        app_port = self._get_app_port(manager)
        file_name = self._log_file_name(app_port, LogType.get(self.option("log-type")))
        try:
            logs = self._get_logs(manager, app_port, file_name)
        except MarkLogicError as error:
            if not self._is_missing_log(str(error)):
                raise
            self.application.render_error(error, self._io)
            self._hint_missing_log(file_name)
            return 1
        formatted_logs = self._format_logs(logs)
        self.line("")
        for info, msg in formatted_logs:
            self._io.write(info)
            self._io.write(msg, new_line=True, type=Type.RAW)
        return 0

    @staticmethod
    def _log_file_name(
        app_port: int | str | None,
        log_type: LogType,
    ) -> str:
        """Return the name of the log file to read.

        Parameters
        ----------
        app_port : int | str | None
            The resolved App Server port or TaskServer; None selects the main log.
        log_type : LogType
            The log type to read.

        Returns
        -------
        str
            The log file name, e.g. 8002_ErrorLog.txt.
        """
        if app_port is None:
            return f"{log_type.value}.txt"
        return f"{app_port}_{log_type.value}.txt"

    @staticmethod
    def _is_missing_log(
        error_message: str,
    ) -> bool:
        """Return True for MarkLogic's 404 MANAGE-NOSUCHLOG error message.

        Parameters
        ----------
        error_message : str
            A MarkLogicError message.

        Returns
        -------
        bool
            True when the requested log file does not exist.
        """
        return (
            error_message.startswith("[404 ") and "(MANAGE-NOSUCHLOG)" in error_message
        )

    def _hint_missing_log(
        self,
        file_name: str,
    ) -> None:
        """Explain on stderr that a missing log file is not an error of its own.

        Parameters
        ----------
        file_name : str
            The requested log file name.
        """
        self.line_error(
            Formatter.escape(self._MISSING_LOG_HINT.format(file_name=file_name)),
        )

    def _get_logs(
        self,
        manager: MLClientManager,
        app_port: int | str | None,
        file_name: str,
    ) -> Iterator[dict]:
        """Retrieve parsed entries through the environment's Manage connection.

        Parameters
        ----------
        manager : MLClientManager
            The manager used for this command's connection.
        app_port : int | str | None
            The resolved App Server port or TaskServer; None selects the main log.
        file_name : str
            The log file name, shown in the progress message.

        Returns
        -------
        Iterator[dict]
            Entries parsed by the Logs service.

        Raises
        ------
        HTTPError
            If the HTTP request fails.
        MarkLogicError
            If MarkLogic rejects the log read.
        """
        log_type = LogType.get(self.option("log-type"))
        start_time = self.option("from")
        end_time = self.option("to")
        regex = self.option("regex")
        host = self.option("host")

        with manager.get_client("manage") as ml:
            self.info(
                f"Getting {file_name} logs using Manage App-Server {ml.http.base_url}",
            )
            return LogsService(ml.manage).get(
                app_port,
                log_type,
                start_time=start_time,
                end_time=end_time,
                regex=regex,
                host=host,
            )

    def _format_logs(
        self,
        logs: Iterator[dict],
    ) -> Iterator[tuple[str, str]]:
        """Format retrieved entries for terminal output.

        Parameters
        ----------
        logs : Iterator[dict]
            Entries already parsed by the Logs service.

        Yields
        ------
        tuple[str, str]
            The styled prefix and literal message to write.
        """
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
        manager: MLClientManager,
    ) -> int | str | None:
        """Resolve the log target using this invocation's environment.

        Parameters
        ----------
        manager : MLClientManager
            The manager used for this command's connection and server lookup.

        Returns
        -------
        int | str | None
            Port, TaskServer or None for the main log.

        Raises
        ------
        mlclient.exceptions.NoSuchAppServerError
            If the selected server identifier is not configured.
        """
        app_port = self.option("server")
        if app_port in {"0", "TaskServer"}:
            app_port = "TaskServer"
        elif app_port is not None and not app_port.isnumeric():
            app_port = manager.get_config(app_port).port
        return app_port
