"""The Health Command module.

It exports an implementation for 'health' command:
    * HealthCommand
        Reports whether a MarkLogic environment's HealthCheck server is up.
"""

from __future__ import annotations

import time
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING, Callable

from cleo.commands.command import Command
from cleo.cursor import Cursor
from cleo.helpers import option
from cleo.io.inputs.option import Option

from mlclient import MLClientManager
from mlclient.exceptions import WrongParametersError

if TYPE_CHECKING:
    from mlclient import MLClient

_HEALTHY = "HEALTHY"
_UNHEALTHY = "UNHEALTHY"

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

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
    it answers with a failure code. A server that cannot be reached raises the
    underlying transport error. The exit code is 0 only when HEALTHY.

    With --watch the command polls until interrupted, printing each status on
    its own line prefixed with the local timestamp; --interval sets the period.
    With --overwrite the poll output is repainted in place, keeping the last
    --lines statuses visible instead of scrolling the terminal.

    Usage:
      health [options]

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -w, --watch
            Poll until interrupted instead of checking once
      -i, --interval=INTERVAL
            Seconds between polls in --watch mode [default: 5]
      -o, --overwrite
            Repaint poll output in place instead of scrolling
      -l, --lines=LINES
            Statuses to keep on screen in --overwrite mode [default: 3]
    """

    name: str = "health"
    description: str = (
        "Reports whether a MarkLogic environment's HealthCheck server is up"
    )
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
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
    ]

    def handle(
        self,
    ) -> int:
        """Execute the command."""
        manager = MLClientManager(self.option("environment"))
        if self.option("watch"):
            return self._watch(manager)
        with manager.get_client() as ml:
            status = self._status(ml)
        self.line(self._format(status))
        return _exit_code(status)

    def _watch(
        self,
        manager: MLClientManager,
    ) -> int:
        """Poll the HealthCheck server until the user interrupts."""
        interval = self._interval()
        render = self._renderer()
        with manager.get_client() as ml:
            try:
                while True:
                    now = datetime.now().strftime(_TIMESTAMP_FORMAT)
                    render(f"{now} {self._format(self._status(ml))}")
                    time.sleep(interval)
            except KeyboardInterrupt:
                return 0

    def _renderer(
        self,
    ) -> Callable[[str], None]:
        """Build the per-poll line writer for the active watch mode."""
        if not self.option("overwrite"):
            return self.line

        history: deque[str] = deque(maxlen=self._lines())
        cursor = Cursor(self.io.output)
        rendered = 0

        def repaint(line: str) -> None:
            nonlocal rendered
            history.append(line)
            if rendered:
                cursor.move_up(rendered)
                cursor.clear_output()
            for entry in history:
                self.line(entry)
            rendered = len(history)

        return repaint

    def _status(
        self,
        ml: MLClient,
    ) -> str:
        """Probe the server and map the outcome to a status label."""
        return _HEALTHY if ml.healthcheck() else _UNHEALTHY

    def _format(
        self,
        status: str,
    ) -> str:
        """Wrap the status label in its colour markup."""
        colour = "green" if status == _HEALTHY else "red"
        return f"<fg={colour};options=bold>{status}</>"

    def _interval(
        self,
    ) -> int:
        """Read and validate the --interval option."""
        return self._bounded_option(
            "interval",
            _MIN_INTERVAL_SECONDS,
            _MAX_INTERVAL_SECONDS,
        )

    def _lines(
        self,
    ) -> int:
        """Read and validate the --lines option."""
        return self._bounded_option("lines", _MIN_LINES, _MAX_LINES)

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


def _exit_code(
    status: str,
) -> int:
    return 0 if status == _HEALTHY else 1


def _out_of_range_message(
    name: str,
    raw: str,
    minimum: int,
    maximum: int,
) -> str:
    return (
        f"--{name} must be an integer between {minimum} and {maximum}, "
        f"got {raw!r}"
    )
