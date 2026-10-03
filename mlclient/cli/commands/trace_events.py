"""The Trace Events Command module.

It exports an implementation for 'trace-events' command:
    * TraceEventsCommand
        Shows or sets a MarkLogic group's diagnostic trace events.
"""

from __future__ import annotations

import httpx
import questionary
from cleo.commands.command import Command
from cleo.formatters.formatter import Formatter
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient._manager import MLClientManager
from mlclient.cli.connection import get_client
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.services.diagnostics.trace_events import TraceEvents, TraceEventsService

_TRUE_TOKENS = frozenset({"true", "on", "1", "yes"})
_FALSE_TOKENS = frozenset({"false", "off", "0", "no"})

# Sentinel checkbox value marking the activation toggle apart from event names.
_ACTIVATION_TOGGLE = object()

_PROMPT_STYLE = questionary.Style(
    [
        ("qmark", "fg:#00d787 bold"),
        ("question", "bold"),
        ("instruction", "fg:#808080"),
        ("pointer", "fg:#00afff bold"),
        ("highlighted", "fg:#00afff bold"),
        ("selected", "fg:#00d787 bold"),
        ("separator", "fg:#5f5f5f"),
        ("disabled", "fg:#5f5f5f italic"),
    ],
)


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
      -E, --event=EVENT
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
            "E",
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
        """Validate command inputs, then execute the requested operation."""
        try:
            enabled = self._parse_value()
        except WrongParametersError as exc:
            self.line_error(f"<error>{Formatter.escape(str(exc))}</error>")
            return 1

        return self._execute(enabled)

    def _parse_value(self) -> bool | None:
        """Validate interactive inputs and parse the optional boolean argument.

        Returns
        -------
        bool | None
            The requested state, or None when no value was supplied.

        Raises
        ------
        WrongParametersError
            If the value is invalid or interactive inputs are incompatible.
        """
        value = self.argument("value")
        if self.option("interactive"):
            self._validate_interactive(value, self.option("event"))
        return _parse_bool(value) if value is not None else None

    def _execute(self, enabled: bool | None) -> int:
        """Connect, dispatch the operation and report its result.

        Parameters
        ----------
        enabled : bool | None
            The validated boolean argument, or None for a read or prompt.

        Returns
        -------
        int
            0 on success, 1 on cancellation or an operation error.

        Notes
        -----
        Connection setup errors propagate to the application. Service errors
        are reported on stderr without printing a successful result.
        """
        group = self.option("group")
        event = self.option("event")
        manager = MLClientManager(self.option("environment"))
        with get_client(manager, self.option("connection")) as ml:
            service = TraceEventsService(ml.rest)
            try:
                if self.option("interactive"):
                    return self._interactive(service, group)
                result = self._run(service, group, event, enabled)
            except (MarkLogicError, WrongParametersError, httpx.HTTPError) as exc:
                self.line_error(f"<error>{Formatter.escape(str(exc))}</error>")
                return 1

        self._print(group, event, result, list_all=enabled is None and event is None)
        return 0

    def _validate_interactive(self, value: str | None, event: str | None) -> None:
        """Reject incompatible interactive inputs before any network requests.

        Parameters
        ----------
        value : str | None
            The optional boolean argument.
        event : str | None
            The optional single-event selector.

        Raises
        ------
        WrongParametersError
            If explicit inputs conflict with the prompt or interaction is disabled.
        """
        if value is not None or event is not None:
            msg = "--interactive cannot be combined with a value or --event."
            raise WrongParametersError(msg)
        if not self.io.is_interactive():
            msg = "--interactive requires an interactive terminal (without -n)."
            raise WrongParametersError(msg)

    def _interactive(
        self,
        service: TraceEventsService,
        group: str,
    ) -> int:
        """Prompt for the activation switch and enabled events, then apply changes.

        A single checkbox lists the activation toggle first, then every
        currently enabled event, all pre-checked. Unchecking the toggle
        deactivates trace events; unchecking an event removes it. Changes are
        saved only where the selection differs from the current state.

        Parameters
        ----------
        service : TraceEventsService
            The service bound to the connected REST App-Server
        group : str
            The group to target

        Returns
        -------
        int
            0 on success, 1 when the prompt is cancelled
        """
        current = service.get(group=group)
        selected = self._ask_selection(current)
        if selected is None:
            self.line_error("Cancelled.")
            return 1

        selected = set(selected)
        activated = _ACTIVATION_TOGGLE in selected
        result = current
        if current.activated and not activated:
            result = service.set_activated(value=False, group=group)
        for event in current.events:
            if event not in selected:
                result = service.set_event(event, enabled=False, group=group)
        if activated and not current.activated:
            result = service.set_activated(value=True, group=group)

        self._print(group, None, result, list_all=True)
        return 0

    @staticmethod
    def _ask_selection(current: TraceEvents) -> list[object] | None:
        """Ask which activation state and currently enabled events to retain.

        Parameters
        ----------
        current : TraceEvents
            Current state used to preselect the activation toggle and events.

        Returns
        -------
        list[object] | None
            Selected event names and activation sentinel, or None on cancellation.
        """
        choices = [
            questionary.Choice(
                "Trace Events Activated",
                value=_ACTIVATION_TOGGLE,
                checked=current.activated,
            ),
        ]
        if current.events:
            choices.append(questionary.Separator("Enabled events"))
            choices.extend(
                questionary.Choice(event, checked=True) for event in current.events
            )
        return questionary.checkbox(
            "Trace events",
            choices=choices,
            style=_PROMPT_STYLE,
            pointer="❯",  # noqa: RUF001
            instruction="(space toggles, enter confirms)",
        ).ask()

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
        elif list_all and result.events:
            self.line("")
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
