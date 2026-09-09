"""The Health Command module.

It exports an implementation for 'health' command:
    * HealthCommand
        Reports whether a MarkLogic environment's HealthCheck server is up.
"""

from __future__ import annotations

import time
from collections import deque
from datetime import datetime
from typing import Callable

from cleo.commands.command import Command
from cleo.cursor import Cursor
from cleo.helpers import option
from cleo.io.inputs.option import Option
from httpx import TransportError

from mlclient import MLClient, MLClientManager
from mlclient.exceptions import WrongParametersError

_HEALTHY = "HEALTHY"
_UNHEALTHY = "UNHEALTHY"
_UNREACHABLE = "UNREACHABLE"

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
    it answers with a failure code. A single check exits with 0 when HEALTHY
    and 1 when UNHEALTHY.

    With --watch the command polls until interrupted, printing each status on
    its own line prefixed with the local timestamp. Connection failures are
    shown as UNREACHABLE and polling continues; --interval sets the period.
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
        config = manager.config.provide_config("health")
        with MLClient(config=config, health_config=config) as ml:
            if self.option("watch"):
                return self._watch(ml)
            healthy = ml.healthcheck()
        self.line(_format_status(healthy))
        return 0 if healthy else 1

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
                try:
                    healthy = ml.healthcheck()
                except TransportError:
                    healthy = None
                now = datetime.now().strftime(_TIMESTAMP_FORMAT)
                render(f"{now} {_format_status(healthy)}")
                time.sleep(interval)
        except KeyboardInterrupt:
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


def _format_status(healthy: bool | None) -> str:
    """Colour a health verdict or an unreachable server."""
    if healthy is None:
        status, colour = _UNREACHABLE, "yellow"
    elif healthy:
        status, colour = _HEALTHY, "green"
    else:
        status, colour = _UNHEALTHY, "red"
    return f"<fg={colour};options=bold>{status}</>"


def _out_of_range_message(
    name: str,
    raw: str,
    minimum: int,
    maximum: int,
) -> str:
    return f"--{name} must be an integer between {minimum} and {maximum}, got {raw!r}"
