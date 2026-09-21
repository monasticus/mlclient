"""The Trace Events Command module.

It exports an implementation for 'trace-events' command:
    * TraceEventsCommand
        Shows or sets a MarkLogic group's diagnostic trace events.
"""

from __future__ import annotations

import questionary
from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient._manager import MLClientManager
from mlclient.cli.connection import get_client
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.services.trace_events import TraceEvents, TraceEventsService

_TRUE_TOKENS = frozenset({"true", "on", "1", "yes"})
_FALSE_TOKENS = frozenset({"false", "off", "0", "no"})


class TraceEventsCommand(Command):
    """Shows or sets a MarkLogic group's diagnostic trace events.

    Without a value it shows the group's state: whether trace events are
    activated and which events are enabled. With a value it sets the master
    activation switch, or, when ``--event`` is given, adds the event (a truthy
    value) or removes it (a falsy value). With only ``--event`` it shows that
    one event's status. Boolean values accept true/false, on/off, 1/0 or
    yes/no.

    Evaluates the Admin functions on the connected REST App-Server.

    Usage:
      trace-events [options] [<value>]

    Arguments:
      value
            A boolean. Sets trace events activated, or with --event adds or
            removes the event. Omit to show the current state.

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
      -g, --group=GROUP
            The group to target [default: "Default"]
      --event=EVENT
            A single trace event to show or, with a value, add or remove
      -i, --interactive
            Choose the activation switch and enabled events at prompts
    """

    name: str = "trace-events"
    description: str = "Shows or sets a MarkLogic group's diagnostic trace events"
    arguments: list[Argument] = [
        argument(
            "value",
            description=(
                "A boolean. Sets trace events activated, or with --event adds "
                "or removes the event. Omit to show the current state."
            ),
            optional=True,
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "connection",
            "c",
            description="Connection identifier from the environment or TCP port",
            flag=False,
        ),
        option(
            "group",
            "g",
            description="The group to target",
            flag=False,
            default="Default",
        ),
        option(
            "event",
            description="A single trace event to show or, with a value, add or remove",
            flag=False,
        ),
        option(
            "interactive",
            "i",
            description="Choose the activation switch and enabled events at prompts",
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        group = self.option("group")
        event = self.option("event")
        value = self.argument("value")
        interactive = self.option("interactive")
        enabled = None
        if not interactive:
            try:
                enabled = _parse_bool(value) if value is not None else None
            except WrongParametersError as exc:
                self.line_error(Formatter.escape(str(exc)))
                return 1

        manager = MLClientManager(self.option("environment"))
        with get_client(manager, self.option("connection")) as ml:
            service = TraceEventsService(ml.rest)
            try:
                if interactive:
                    return self._interactive(service, group)
                result = self._run(service, group, event, enabled)
            except (MarkLogicError, WrongParametersError) as exc:
                self.line_error(Formatter.escape(str(exc)))
                return 1

        self._print(group, event, result, list_all=value is None and event is None)
        return 0

    def _interactive(
        self,
        service: TraceEventsService,
        group: str,
    ) -> int:
        """Prompt for the activation switch and enabled events, then apply changes.

        The event prompt offers the currently enabled events, all pre-selected;
        unselecting one removes it. The activation switch and each unselected
        event are saved only when they differ from the current state.

        Parameters
        ----------
        service : TraceEventsService
            The service bound to the connected REST App-Server
        group : str
            The group to target

        Returns
        -------
        int
            0 on success, 1 when a prompt is cancelled
        """
        current = service.get(group=group)
        activated = questionary.confirm(
            "Activate trace events?",
            default=current.activated,
        ).ask()
        kept = questionary.checkbox(
            "Enabled trace events",
            choices=[questionary.Choice(e, checked=True) for e in current.events],
        ).ask()
        if activated is None or kept is None:
            self.line_error("Cancelled.")
            return 1

        result = current
        if activated != current.activated:
            result = service.set_activated(value=activated, group=group)
        for event in current.events:
            if event not in kept:
                result = service.set_event(event, enabled=False, group=group)

        self._print(group, None, result, list_all=True)
        return 0

    @staticmethod
    def _run(
        service: TraceEventsService,
        group: str,
        event: str | None,
        enabled: bool | None,
    ) -> TraceEvents:
        """Read or change the trace-event state according to the parsed inputs.

        Parameters
        ----------
        service : TraceEventsService
            The service bound to the connected REST App-Server
        group : str
            The group to target
        event : str | None
            A single trace event to add or remove, or None
        enabled : bool | None
            The parsed boolean value, or None for a read

        Returns
        -------
        TraceEvents
            The resulting trace-event state
        """
        if enabled is None:
            return service.get(group=group)
        if event is not None:
            return service.set_event(event, enabled=enabled, group=group)
        return service.set_activated(value=enabled, group=group)

    def _print(
        self,
        group: str,
        event: str | None,
        result: TraceEvents,
        *,
        list_all: bool,
    ) -> None:
        """Print the group, the activation switch and the relevant event lines.

        Parameters
        ----------
        group : str
            Group name displayed literally
        event : str | None
            The single event whose status is shown, or None
        result : TraceEvents
            The trace-event state to render
        list_all : bool
            Whether to list every enabled event (a plain show with no --event)
        """
        self.line(f"Group: <options=bold>{Formatter.escape(group)}</>")
        self.line(f"Trace Events Activated: {_styled_bool(result.activated)}")
        if event is not None:
            status = _styled_status(event in result.events)
            self.line(f"{Formatter.escape(event)}: {status}")
        elif list_all:
            for enabled_event in result.events:
                self.line(f"{Formatter.escape(enabled_event)}: {_styled_status(True)}")


def _parse_bool(
    value: str,
) -> bool:
    """Parse a command-line boolean, accepting common truthy and falsy tokens.

    Parameters
    ----------
    value : str
        The raw value argument

    Returns
    -------
    bool
        The parsed boolean

    Raises
    ------
    WrongParametersError
        If the value is not a recognized boolean token
    """
    token = value.strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    msg = f"Expected a boolean value (true/false, on/off, 1/0, yes/no), got {value!r}."
    raise WrongParametersError(msg)


def _styled_bool(
    value: bool,
) -> str:
    """Render a boolean as coloured ``true``/``false``.

    Parameters
    ----------
    value : bool
        The value to render

    Returns
    -------
    str
        Cleo-tagged ``true`` in green or ``false`` in red
    """
    return "<fg=green>true</>" if value else "<fg=red>false</>"


def _styled_status(
    enabled: bool,
) -> str:
    """Render an event's membership as coloured ``on``/``off``.

    Parameters
    ----------
    enabled : bool
        Whether the event is enabled

    Returns
    -------
    str
        Cleo-tagged ``on`` in green or ``off`` in red
    """
    return "<fg=green>on</>" if enabled else "<fg=red>off</>"
