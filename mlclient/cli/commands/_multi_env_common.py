"""Shared helpers for commands that send one request to several environments.

The request runs in all environments at once and the answers are shown in a
table with one column per environment, wrapped to fit the terminal width. Each
column header counts the seconds waited so far and shows the final time once
that environment answers. Answers show up as they arrive, cut to the terminal
height until every environment has answered.
"""

from __future__ import annotations

import asyncio
import shutil
import textwrap
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from cleo.formatters.formatter import Formatter
from cleo.ui.table import Table

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from cleo.commands.command import Command
    from cleo.io.outputs.section_output import SectionOutput

_REFRESH_INTERVAL_SECONDS = 0.1
_ERROR_STYLE = "error"

Answer = TypeVar("Answer")


class UnsuccessfulAnswerError(Exception):
    """Raised by a request whose answer counts as a failure, e.g. unhealthy.

    Parameters
    ----------
    message : str
        The answer shown in place of a result.
    style : str
        The cleo style of the answer, e.g. ``fg=red;options=bold``.
    """

    def __init__(
        self,
        message: str,
        style: str = _ERROR_STYLE,
    ):
        super().__init__(message)
        self.style = style


def selected_environments(
    command: Command,
) -> list[str]:
    """Read the environment names given to a command, each one once.

    Parameters
    ----------
    command : Command
        A command with a multiple-value ``environment`` option.

    Returns
    -------
    list[str]
        The environment names in the order first given.
    """
    return list(dict.fromkeys(command.option("environment")))


def time_in_environments(
    command: Command,
    environments: list[str],
    request: Callable[[str], Awaitable[Answer]],
    describe: Callable[[Answer], str] = str,
    highlight: Callable[[str], str] | None = None,
) -> int:
    """Send a request to every environment at once and show the answers.

    Parameters
    ----------
    command : Command
        The command whose output shows the table.
    environments : list[str]
        Environment names, one table column each, in the given order.
    request : Callable[[str], Awaitable[Answer]]
        Sends the request to the named environment. Its duration is what the
        table reports. Any exception it raises is shown as that environment's
        failure.
    describe : Callable[[Answer], str]
        Turns an answer into the plain text shown in the table.
    highlight : Callable[[str], str] | None
        Turns each escaped output line, an answer or an error, into cleo markup;
        None leaves answers unstyled and shows errors in their own style.

    Returns
    -------
    int
        0 when every environment answered successfully, 1 when any failed.
    """
    runs = [
        EnvironmentRun(environment, highlight=highlight) for environment in environments
    ]
    section = command.io.output.section()

    def refresh(waited: float) -> None:
        if section.is_decorated():
            _render(section, runs, waited, fit_screen=True)

    started = time.perf_counter()
    asyncio.run(run_all(runs, request, describe, refresh))
    _render(section, runs, time.perf_counter() - started, fit_screen=False)
    return 1 if any(run.error is not None for run in runs) else 0


@dataclass
class EnvironmentRun:
    """The request sent to one environment: its duration and its outcome.

    ``elapsed`` stays None while the request runs. Once finished, ``output``
    holds the described answer, or the error message when ``error`` is set,
    and ``style`` the cleo style to show it with. ``highlight``, when set,
    marks up each output line instead of ``style``.
    """

    environment: str
    elapsed: float | None = None
    output: str = ""
    error: Exception | None = None
    style: str | None = None
    highlight: Callable[[str], str] | None = None

    def duration(
        self,
        waited: float,
    ) -> tuple[str, str]:
        """Describe how long the request has taken.

        Parameters
        ----------
        waited : float
            Seconds since the requests started, shown while this one runs.

        Returns
        -------
        tuple[str, str]
            The seconds waited with one decimal while running, or the final time
            with three decimals once finished, and the cleo style to show it with.
        """
        if self.elapsed is None:
            return f"{waited:.1f} s", "comment"
        if self.error is not None:
            return f"failed after {self.elapsed:.3f} s", _ERROR_STYLE
        return f"{self.elapsed:.3f} s", "info"

    def header(
        self,
        waited: float,
        width: int,
    ) -> str:
        """Describe the run as a column header.

        Parameters
        ----------
        waited : float
            Seconds since the requests started, shown while this one runs.
        width : int
            Width of the column the duration is aligned to the right edge of.

        Returns
        -------
        str
            The environment name followed by the duration.
        """
        duration, style = self.duration(waited)
        gap = max(width - len(self.environment) - len(duration), 1)
        environment = Formatter.escape(self.environment)
        return f"{environment}{' ' * gap}<{style}>{duration}</{style}>"

    def body(
        self,
        lines: list[str],
        hidden_lines: int,
    ) -> str:
        """Describe the run outcome as a table cell.

        Parameters
        ----------
        lines : list[str]
            The output lines to show, wrapped to the column width.
        hidden_lines : int
            How many output lines follow the shown ones, announced in a last line.

        Returns
        -------
        str
            The answer or the error message, highlighted or in the run's style.
        """
        cell_lines = [Formatter.escape(line) for line in lines]
        if self.highlight is not None:
            cell_lines = [self.highlight(line) for line in cell_lines]
        elif self.style is not None:
            cell_lines = [f"<{self.style}>{line}</>" for line in cell_lines]
        if hidden_lines:
            cell_lines.append(f"<comment>... {hidden_lines} more lines</comment>")
        return "\n".join(cell_lines)


async def run_all(
    runs: list[EnvironmentRun],
    request: Callable[[str], Awaitable[Any]],
    describe: Callable[[Any], str],
    refresh: Callable[[float], None],
) -> None:
    """Send the request to every environment at once.

    Parameters
    ----------
    runs : list[EnvironmentRun]
        The runs to fill, one per environment.
    request : Callable[[str], Awaitable[Any]]
        Sends the request to the named environment.
    describe : Callable[[Any], str]
        Turns an answer into the plain text of the run output.
    refresh : Callable[[float], None]
        Called with the seconds waited so far, every tenth of a second until all
        runs finish.
    """
    started = time.perf_counter()
    all_finished = asyncio.gather(
        *(_run(run, request, describe) for run in runs),
    )
    while not all_finished.done():
        refresh(time.perf_counter() - started)
        await asyncio.wait([all_finished], timeout=_REFRESH_INTERVAL_SECONDS)


async def _run(
    run: EnvironmentRun,
    request: Callable[[str], Awaitable[Any]],
    describe: Callable[[Any], str],
) -> None:
    """Send the request to one environment and record the outcome and duration.

    Parameters
    ----------
    run : EnvironmentRun
        The run to fill.
    request : Callable[[str], Awaitable[Any]]
        Sends the request to the named environment.
    describe : Callable[[Any], str]
        Turns an answer into the plain text of the run output.
    """
    started = time.perf_counter()
    try:
        answer = await request(run.environment)
    except Exception as error:
        run.elapsed = time.perf_counter() - started
        run.error = error
        run.output = str(error)
        run.style = getattr(error, "style", _ERROR_STYLE)
    else:
        run.elapsed = time.perf_counter() - started
        run.output = describe(answer)


def _render(
    section: SectionOutput,
    runs: list[EnvironmentRun],
    waited: float,
    *,
    fit_screen: bool,
) -> None:
    """Replace the section content with a table of the runs.

    Parameters
    ----------
    section : SectionOutput
        The output section holding the table.
    runs : list[EnvironmentRun]
        The runs, one column each.
    waited : float
        Seconds since the requests started.
    fit_screen : bool
        Whether to cut the answers to the terminal height. A table taller than
        the terminal scrolls its top out of reach and cannot be overwritten.
    """
    terminal = shutil.get_terminal_size()
    # The box style takes one border character plus three per column.
    column_width = max((terminal.columns - 1) // len(runs) - 3, 1)
    # Three borders and the header surround the answers. Two more lines stay free:
    # one for the cursor, one so the table never starts at the top-left corner,
    # where some terminals (tmux) copy a full-screen erase into the scrollback.
    visible_lines = max(terminal.lines - 6, 1) if fit_screen else None
    outputs = [_wrap(run.output, column_width) for run in runs]
    table = Table(section, style="box")
    table.set_headers(
        [
            run.header(waited, max(map(len, lines), default=0))
            for run, lines in zip(runs, outputs)
        ],
    )
    if any(outputs):
        table.set_rows(
            [[_cell(run, lines, visible_lines) for run, lines in zip(runs, outputs)]],
        )
    section.clear()
    table.render()


def _cell(
    run: EnvironmentRun,
    lines: list[str],
    visible_lines: int | None,
) -> str:
    """Describe the run outcome as a cell of at most the visible lines.

    Parameters
    ----------
    run : EnvironmentRun
        The run the cell describes.
    lines : list[str]
        All output lines, wrapped to the column width.
    visible_lines : int | None
        Maximum cell height, the announcement of hidden lines included; None for
        no limit.

    Returns
    -------
    str
        The cell content.
    """
    if visible_lines is None or len(lines) <= visible_lines:
        return run.body(lines, 0)
    shown = lines[: visible_lines - 1]
    return run.body(shown, len(lines) - len(shown))


def _wrap(
    text: str,
    width: int,
) -> list[str]:
    """Split text into lines no wider than the width.

    Parameters
    ----------
    text : str
        Text to split, possibly containing line breaks and tabs.
    width : int
        Maximum line width.

    Returns
    -------
    list[str]
        The lines, long ones broken at spaces where possible and tabs expanded;
        empty lines are kept.
    """
    return [
        wrapped
        for line in text.splitlines()
        for wrapped in textwrap.wrap(
            line,
            width,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        or [""]
    ]
