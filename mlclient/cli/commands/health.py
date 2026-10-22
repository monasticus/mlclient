"""The Health Command module.

It exports an implementation for 'health' command:
    * HealthCommand
        Reports whether a MarkLogic environment's HealthCheck server is up.
"""

from __future__ import annotations

import asyncio
import functools
import re
import time
from collections import deque
from contextlib import AsyncExitStack
from datetime import datetime
from typing import TYPE_CHECKING, Callable

from cleo.commands.command import Command
from cleo.cursor import Cursor
from cleo.formatters.formatter import Formatter
from cleo.helpers import option
from cleo.io.inputs.option import Option
from cleo.io.outputs.buffered_output import BufferedOutput
from cleo.io.outputs.output import Type
from cleo.ui.table import Table
from httpx import TransportError

from mlclient._client import MLClient
from mlclient._manager import MLClientManager
from mlclient.cli.commands._multi_env_common import (
    EnvironmentRun,
    UnsuccessfulAnswerError,
    run_all,
    selected_environments,
    time_in_environments,
)
from mlclient.exceptions import WrongParametersError

if TYPE_CHECKING:
    from cleo.io.outputs.output import Output

    from mlclient._client import AsyncMLClient
    from mlclient.models import ClusterHealth

_HEALTHY = "HEALTHY"
_UNHEALTHY = "UNHEALTHY"
_UNREACHABLE = "UNREACHABLE"

_STATUS_STYLES = {
    _HEALTHY: "fg=green;options=bold",
    _UNHEALTHY: "fg=red;options=bold",
    _UNREACHABLE: "fg=yellow;options=bold",
}
_STATUS_LINE = re.compile(rf"({_HEALTHY}|{_UNHEALTHY}|{_UNREACHABLE})(?: (.+))?")

_HOST_COUNT_STYLE = "fg=cyan"
_OVERALL = "(overall)"

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_TIMESTAMP_WIDTH = len("2000-01-01 00:00:00")
# Wide enough for the longest status and a duration below 1000 seconds.
_WATCH_CELL_WIDTH = len(f"{_UNREACHABLE} 999.999 s")
_CLUSTER_WATCH_CELL_WIDTH = len(f"{_UNHEALTHY} {_OVERALL} 999.999 s")

_DEFAULT_INTERVAL_SECONDS = 5
_MIN_INTERVAL_SECONDS = 1
_MAX_INTERVAL_SECONDS = 3600

_DEFAULT_LINES = 3
_MIN_LINES = 1
_MAX_LINES = 100


class HealthCommand(Command):
    """Reports whether a MarkLogic environment's HealthCheck server is up.

    Sends HEAD / to the environment's HealthCheck server and prints a coloured
    status: HEALTHY (green) when it answers with success, UNHEALTHY (red) when
    it answers with a failure code. A single check exits with 0 when HEALTHY
    and 1 when UNHEALTHY.

    With --watch the command polls until interrupted, printing each status on
    its own line prefixed with the local timestamp. Connection failures are
    shown as UNREACHABLE and polling continues; --interval sets the period.
    With --overwrite the poll output is repainted in place, keeping the last
    --lines statuses visible instead of scrolling the terminal.

    With several environments all are checked at the same time, and a table
    with one column per environment shows each status and how long the check
    took; the command exits with 1 unless all are HEALTHY. With --watch every
    poll adds a row with the time it started and, per environment, the status
    and the check duration; --overwrite repaints the table in place, keeping the
    last --lines rows.

    With --cluster every host of the cluster is checked from inside it through
    the environment's REST server, and the status is followed by the number of
    healthy hosts out of all, e.g. HEALTHY 12/12. Unhealthy hosts are listed
    below it, sorted by name with numbers ordered by value; with -v every host
    is. With --watch the unhealthy hosts follow the status on its line, and in a
    table of several environments only the host count is shown. When the
    cluster reports no per-host health (a user without the eval privilege on
    MarkLogic 11 or later), the count is replaced by (overall).

    Usage:
      health [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name; repeat it to check several
            environments (multiple values allowed) [default: ["local"]]
      -w, --watch
            Poll until interrupted instead of checking once
      -i, --interval=INTERVAL
            Seconds between polls in --watch mode [default: 5]
      -o, --overwrite
            Repaint poll output in place instead of scrolling
      -l, --lines=LINES
            Statuses to keep on screen in --overwrite mode [default: 3]
      -c, --cluster
            Check every host of the cluster instead of the HealthCheck server
    """

    name: str = "health"
    description: str = (
        "Reports whether a MarkLogic environment's HealthCheck server is up"
    )
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name; repeat it to check several "
            "environments",
            flag=False,
            multiple=True,
            default=["local"],
        ),
        option(
            "watch",
            "w",
            description="Poll until interrupted instead of checking once",
        ),
        option(
            "interval",
            "i",
            description="Seconds between polls in --watch mode",
            flag=False,
            default=str(_DEFAULT_INTERVAL_SECONDS),
        ),
        option(
            "overwrite",
            "o",
            description="Repaint poll output in place instead of scrolling",
        ),
        option(
            "lines",
            "l",
            description="Statuses to keep on screen in --overwrite mode",
            flag=False,
            default=str(_DEFAULT_LINES),
        ),
        option(
            "cluster",
            "c",
            description="Check every host of the cluster instead of the HealthCheck "
            "server",
        ),
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        environments = selected_environments(self)
        cluster = self.option("cluster")
        if len(environments) > 1:
            if self.option("watch"):
                return self._watch_all(environments)
            return time_in_environments(
                self,
                environments,
                functools.partial(_check_health, cluster=cluster),
                highlight=_highlight,
            )
        manager = MLClientManager(environments[0])
        with manager.get_client(_app_server_id(cluster)) as ml:
            if self.option("watch"):
                return self._watch(ml)
            if cluster:
                return self._report_cluster(ml.cluster_healthcheck())
            healthy = ml.healthcheck()
        self.line(_format_status(healthy))
        return 0 if healthy else 1

    def _report_cluster(
        self,
        health: ClusterHealth,
    ) -> int:
        """Print the cluster status, then its hosts sorted by name.

        Parameters
        ----------
        health : ClusterHealth
            The checked cluster.

        Returns
        -------
        int
            0 when the cluster is healthy, 1 otherwise.
        """
        self.line(_highlight(_cluster_status(health)))
        hosts = health.hosts or {}
        for name in sorted(hosts, key=_host_name_order):
            if not hosts[name] or self.io.is_verbose():
                self.line(_host_line(name, healthy=hosts[name]))
        return 0 if health else 1

    def _watch(self, ml: MLClient) -> int:
        """Poll until interrupted, continuing through transport failures."""
        interval = self._bounded_option(
            "interval",
            _MIN_INTERVAL_SECONDS,
            _MAX_INTERVAL_SECONDS,
        )
        render = self._renderer()
        try:
            while True:
                status = self._poll(ml)
                now = datetime.now().strftime(_TIMESTAMP_FORMAT)
                render(f"{now} {status}")
                time.sleep(interval)
        except KeyboardInterrupt:
            return 0

    def _poll(self, ml: MLClient) -> str:
        """Check the environment once, an unreachable one included.

        Returns
        -------
        str
            The coloured status, followed by the unhealthy hosts of a cluster.
        """
        try:
            if self.option("cluster"):
                return _cluster_watch_status(ml.cluster_healthcheck())
            healthy = ml.healthcheck()
        except TransportError:
            healthy = None
        return _format_status(healthy)

    def _watch_all(
        self,
        environments: list[str],
    ) -> int:
        """Poll every environment at once until interrupted, a table row per poll.

        Parameters
        ----------
        environments : list[str]
            Environment names, one table column each, in the given order.

        Returns
        -------
        int
            0 once interrupted.
        """
        interval = self._bounded_option(
            "interval",
            _MIN_INTERVAL_SECONDS,
            _MAX_INTERVAL_SECONDS,
        )
        kept_rows = None
        if self.option("overwrite"):
            kept_rows = self._bounded_option("lines", _MIN_LINES, _MAX_LINES)
            if not self.io.output.is_decorated():
                kept_rows = None
        cluster = self.option("cluster")
        cell_width = _CLUSTER_WATCH_CELL_WIDTH if cluster else _WATCH_CELL_WIDTH
        table = _WatchTable(self.io.output, environments, kept_rows, cell_width)
        try:
            asyncio.run(
                _poll_until_interrupted(environments, interval, table, cluster=cluster),
            )
        except KeyboardInterrupt:
            table.close()
        return 0

    def _renderer(
        self,
    ) -> Callable[[str], None]:
        """Build the per-poll line writer for the active watch mode."""
        if not self.option("overwrite"):
            return self.line

        lines = self._bounded_option("lines", _MIN_LINES, _MAX_LINES)
        if not self.io.output.is_decorated():
            return self.line
        history: deque[str] = deque(maxlen=lines)
        cursor = Cursor(self.io.output)

        def repaint(line: str) -> None:
            if history:
                cursor.move_up(len(history))
                cursor.clear_output()
            history.append(line)
            for entry in history:
                self.line(entry)

        return repaint

    def _bounded_option(
        self,
        name: str,
        minimum: int,
        maximum: int,
    ) -> int:
        """Parse an integer option and enforce its inclusive bounds."""
        raw = self.option(name)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise WrongParametersError(
                _out_of_range_message(name, raw, minimum, maximum),
            ) from None
        if not minimum <= value <= maximum:
            raise WrongParametersError(
                _out_of_range_message(name, raw, minimum, maximum),
            )
        return value


async def _check_health(environment: str, *, cluster: bool) -> str:
    """Check one environment's HealthCheck server or every host of its cluster.

    Parameters
    ----------
    environment : str
        The environment name.
    cluster : bool
        Whether to check every host of the cluster.

    Returns
    -------
    str
        The HEALTHY status, followed by the host count of a cluster.

    Raises
    ------
    UnsuccessfulAnswerError
        If the server or the cluster is unhealthy or cannot be reached.
    """
    manager = MLClientManager(environment)
    async with manager.get_async_client(_app_server_id(cluster)) as ml:
        status = await _poll(ml, cluster=cluster)
    if not _is_healthy(status):
        raise UnsuccessfulAnswerError(status)
    return status


async def _poll_until_interrupted(
    environments: list[str],
    interval: int,
    table: _WatchTable,
    *,
    cluster: bool,
) -> None:
    """Check every environment at once, again and again, adding table rows.

    Parameters
    ----------
    environments : list[str]
        Environment names, one table column each.
    interval : int
        Seconds between the end of a poll and the start of the next one.
    table : _WatchTable
        The table showing the polls.
    cluster : bool
        Whether to check every host of each cluster.
    """
    async with AsyncExitStack() as stack:
        clients = {
            environment: await stack.enter_async_context(
                MLClientManager(environment).get_async_client(_app_server_id(cluster)),
            )
            for environment in environments
        }

        async def poll(environment: str) -> str:
            return await _poll(clients[environment], cluster=cluster)

        while True:
            started_at = datetime.now().strftime(_TIMESTAMP_FORMAT)
            runs = [EnvironmentRun(environment) for environment in environments]

            refresh = functools.partial(table.show, started_at, runs)
            await run_all(runs, poll, str, refresh)
            table.finish(started_at, runs)
            await asyncio.sleep(interval)


async def _poll(ml: AsyncMLClient, *, cluster: bool) -> str:
    """Check a HealthCheck server or a cluster, an unreachable one included.

    Parameters
    ----------
    ml : AsyncMLClient
        A client of the environment to check.
    cluster : bool
        Whether to check every host of the cluster.

    Returns
    -------
    str
        HEALTHY, UNHEALTHY or UNREACHABLE, followed by the host count of a
        reachable cluster.
    """
    try:
        if cluster:
            return _cluster_status(await ml.cluster_healthcheck())
        healthy = await ml.healthcheck()
    except TransportError:
        healthy = None
    return _status(healthy)


class _WatchTable:
    """Health statuses of several environments, one table row per poll.

    Without kept rows, each poll's row is printed below the previous ones and
    stays; with them, the whole table is repainted in place showing the latest
    polls only. A running poll's row counts its seconds, and the bottom border
    closes the table between polls, while the output is decorated, as only then
    they can be overwritten; otherwise the border is printed once polling stops.

    Parameters
    ----------
    output : Output
        The command output.
    environments : list[str]
        Environment names, one column each after the time column.
    kept_rows : int | None
        How many rows to repaint in place, None to print each row once.
    cell_width : int
        Minimum width of an environment column.
    """

    def __init__(
        self,
        output: Output,
        environments: list[str],
        kept_rows: int | None,
        cell_width: int,
    ):
        self._output = output
        self._environments = environments
        self._kept_rows = kept_rows
        self._cell_width = cell_width
        self._finished_rows: deque[list[str]] = deque(
            maxlen=None if kept_rows is None else kept_rows - 1,
        )
        self._section = output.section()
        self._header_printed = False

    def show(
        self,
        started_at: str,
        runs: list[EnvironmentRun],
        waited: float,
    ) -> None:
        """Show a running poll.

        Parameters
        ----------
        started_at : str
            When the poll started.
        runs : list[EnvironmentRun]
            The poll's runs, one per environment.
        waited : float
            Seconds since the poll started.
        """
        if self._output.is_decorated():
            self._draw(_watch_row(started_at, runs, waited, self._cell_width))

    def finish(
        self,
        started_at: str,
        runs: list[EnvironmentRun],
    ) -> None:
        """Show a finished poll for good.

        Parameters
        ----------
        started_at : str
            When the poll started.
        runs : list[EnvironmentRun]
            The poll's finished runs, one per environment.
        """
        row = _watch_row(started_at, runs, 0, self._cell_width)
        self._draw(row, finished=True)
        self._finished_rows.append(row)

    def close(
        self,
    ) -> None:
        """End the table once polling stops."""
        if self._kept_rows is None and self._header_printed:
            if self._output.is_decorated():
                # The terminal echo of Ctrl+C moves the cursor off the line start.
                self._output.write("\r", type=Type.RAW)
            self._replace_section(self._bottom_border())

    def _draw(
        self,
        row: list[str],
        *,
        finished: bool = False,
    ) -> None:
        """Show the row, in the whole repainted table or below the previous rows.

        Parameters
        ----------
        row : list[str]
            The poll's cells.
        finished : bool
            Whether the poll has finished, so its row stays as it is now.
        """
        if self._kept_rows is not None:
            self._replace_section(self._lines([*self._finished_rows, row]))
            return
        lines = self._lines([row])
        if not self._header_printed:
            top_border_header_and_separator = "\n".join(lines[:3])
            self._output.write_line(top_border_header_and_separator, type=Type.RAW)
            self._header_printed = True
        row_lines, bottom_border = lines[3:-1], lines[-1]
        if not self._output.is_decorated():
            self._output.write_line("\n".join(row_lines), type=Type.RAW)
            return
        if not finished:
            self._replace_section([*row_lines, bottom_border])
            return
        self._replace_section(row_lines)
        self._section = self._output.section()
        self._replace_section([bottom_border])

    def _replace_section(
        self,
        lines: list[str],
    ) -> None:
        """Replace the current section content with formatted lines."""
        self._section.clear()
        self._section.write_line("\n".join(lines), type=Type.RAW)

    def _bottom_border(
        self,
    ) -> list[str]:
        """Render the bottom border of the table."""
        return self._lines([])[-1:]

    def _lines(
        self,
        rows: list[list[str]],
    ) -> list[str]:
        """Render the table with the rows into formatted lines.

        Fixed column widths keep the lines of separately rendered tables aligned.
        """
        buffer = BufferedOutput(
            decorated=self._output.is_decorated(),
            formatter=self._output.formatter,
        )
        table = Table(buffer, style="box")
        table.set_headers(["time", *map(Formatter.escape, self._environments)])
        table.set_rows(rows)
        table.set_column_widths(
            [
                _TIMESTAMP_WIDTH,
                *(max(len(name), self._cell_width) for name in self._environments),
            ],
        )
        table.render()
        return buffer.fetch().splitlines()


def _watch_row(
    started_at: str,
    runs: list[EnvironmentRun],
    waited: float,
    cell_width: int,
) -> list[str]:
    """Describe a poll as watch table cells.

    Parameters
    ----------
    started_at : str
        When the poll started.
    runs : list[EnvironmentRun]
        The poll's runs, one per environment.
    waited : float
        Seconds since the poll started.
    cell_width : int
        Width of an environment cell.

    Returns
    -------
    list[str]
        The start time followed by one cell per environment.
    """
    return [started_at, *(_watch_cell(run, waited, cell_width) for run in runs)]


def _watch_cell(
    run: EnvironmentRun,
    waited: float,
    width: int,
) -> str:
    """Describe a run as a watch table cell: its status, then its duration.

    Parameters
    ----------
    run : EnvironmentRun
        The run to describe.
    waited : float
        Seconds since the poll started, shown while the run is running.
    width : int
        Width of the cell the duration is aligned to the right edge of.

    Returns
    -------
    str
        The coloured status and the duration aligned to the right of the cell.
    """
    duration, duration_style = run.duration(waited)
    status = "" if run.elapsed is None else run.output
    gap = max(width - len(status) - len(duration), 1)
    coloured_status = _highlight(Formatter.escape(status)) if status else ""
    return f"{coloured_status}{' ' * gap}<{duration_style}>{duration}</>"


def _app_server_id(cluster: bool) -> str | None:
    """Select the HealthCheck server, or the REST server that checks a cluster."""
    return None if cluster else "health"


def _cluster_watch_status(health: ClusterHealth) -> str:
    """Colour a cluster status and append the unhealthy hosts, sorted by name."""
    status = _highlight(_cluster_status(health))
    hosts = health.hosts or {}
    unhealthy = [
        Formatter.escape(name)
        for name in sorted(hosts, key=_host_name_order)
        if not hosts[name]
    ]
    if not unhealthy:
        return status
    return f"{status} down: {', '.join(unhealthy)}"


def _cluster_status(health: ClusterHealth) -> str:
    """Name a cluster verdict followed by its healthy hosts out of all."""
    return f"{_status(health.healthy)} {_host_count(health)}"


def _host_count(health: ClusterHealth) -> str:
    """Count the healthy hosts out of all, or mark a verdict without hosts."""
    if health.hosts is None:
        return _OVERALL
    return f"{sum(health.hosts.values())}/{len(health.hosts)}"


def _host_name_order(name: str) -> list[str | int]:
    """Sort key ordering the numbers in host names by value, e.g. ip-10-0-0-5 first."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def _host_line(name: str, *, healthy: bool) -> str:
    """Describe a host as an indented line: its coloured status, then its name."""
    status = _status(healthy)
    padding = " " * (len(_UNHEALTHY) - len(status))
    return f"  {_highlight(status)}{padding}  {Formatter.escape(name)}"


def _is_healthy(status: str) -> bool:
    """Tell whether a status, possibly followed by a host count, is HEALTHY."""
    return status.partition(" ")[0] == _HEALTHY


def _format_status(healthy: bool | None) -> str:
    """Colour a health verdict or an unreachable server."""
    return _highlight(_status(healthy))


def _status(healthy: bool | None) -> str:
    """Name a health verdict, None standing for an unreachable server."""
    if healthy is None:
        return _UNREACHABLE
    return _HEALTHY if healthy else _UNHEALTHY


def _highlight(text: str) -> str:
    """Mark up an escaped status line, any other text as an error.

    The status takes its own colour and the host count after it, if any, the
    host count colour.
    """
    match = _STATUS_LINE.fullmatch(text)
    if match is None:
        return f"<error>{text}</>"
    status, host_count = match.groups()
    coloured_status = f"<{_STATUS_STYLES[status]}>{status}</>"
    if host_count is None:
        return coloured_status
    return f"{coloured_status} <{_HOST_COUNT_STYLE}>{host_count}</>"


def _out_of_range_message(
    name: str,
    raw: str,
    minimum: int,
    maximum: int,
) -> str:
    return f"--{name} must be an integer between {minimum} and {maximum}, got {raw!r}"
