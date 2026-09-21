"""Isolated trace-events service (TraceEventsService).

Reads or changes the group-level diagnostic trace events shown on the Admin
Interface Diagnostics page: the master "trace events activated" switch and the
set of enabled trace events. It evaluates the Admin module functions on the
connected REST App-Server.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mlclient._options import UNSET
from mlclient.exceptions import MarkLogicError
from mlclient.responses import MLResponseParser

if TYPE_CHECKING:
    from httpx import Response

    from mlclient.api.rest import RestApi

logger = logging.getLogger(__name__)

_ADMIN_MODULE_IMPORT = (
    'xquery version "1.0-ml"; '
    'import module namespace admin = "http://marklogic.com/xdmp/admin" '
    'at "/MarkLogic/admin.xqy"; '
)


@dataclass(frozen=True)
class TraceEvents:
    """A group's trace-event state.

    Attributes
    ----------
    activated : bool
        Whether the group's master trace-events switch is on.
    events : tuple[str, ...]
        The names of the enabled trace events, in the order the server reports.
    """

    activated: bool
    events: tuple[str, ...]


class TraceEventsService:
    """Read the trace-event state of a group by evaluating the Admin module."""

    def __init__(
        self,
        rest: RestApi,
    ):
        """Initialize the service with a REST API handle.

        Parameters
        ----------
        rest : RestApi
            Connected REST API used for Admin-module evaluation
        """
        self._rest = rest

    def get(
        self,
        *,
        group: str = "Default",
        timeout=UNSET,
    ) -> TraceEvents:
        """Return the group's trace-events activation and enabled events.

        Parameters
        ----------
        group : str, default "Default"
            The group whose trace-event state is read.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset preserves the client's configured
            timeout; None disables it; a number applies to all four components;
            an httpx.Timeout sets them independently.

        Returns
        -------
        TraceEvents
            The activation flag and the enabled trace-event names.

        Raises
        ------
        RequestError
            If HTTP transport fails
        """
        resp = self._eval(self._get_code(), {"group": group}, timeout)
        state = MLResponseParser.parse(resp)
        return TraceEvents(
            activated=state["activated"],
            events=tuple(state["events"]),
        )

    def set_activated(
        self,
        *,
        value: bool,
        group: str = "Default",
        timeout=UNSET,
    ) -> TraceEvents:
        """Turn the group's master trace-events switch on or off.

        Parameters
        ----------
        value : bool
            The activation state to save.
        group : str, default "Default"
            The group whose switch is changed.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout applied to both the mutation and the
            follow-up read. Unset preserves the client's configured timeout;
            None disables it; a number applies to all four components; an
            httpx.Timeout sets them independently.

        Returns
        -------
        TraceEvents
            The group's trace-event state after the change.

        Raises
        ------
        RequestError
            If HTTP transport fails
        """
        variables = {"group": group, "value": "true" if value else "false"}
        return self._mutate(self._set_activated_code(), variables, group, timeout)

    def set_event(
        self,
        event: str,
        *,
        enabled: bool,
        group: str = "Default",
        timeout=UNSET,
    ) -> TraceEvents:
        """Add or remove a single trace event from the group's enabled set.

        Parameters
        ----------
        event : str
            The trace-event name to enable or disable.
        enabled : bool
            True adds the event to the enabled set; False removes it.
        group : str, default "Default"
            The group whose enabled events are changed.
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout applied to both the mutation and the
            follow-up read. Unset preserves the client's configured timeout;
            None disables it; a number applies to all four components; an
            httpx.Timeout sets them independently.

        Returns
        -------
        TraceEvents
            The group's trace-event state after the change.

        Raises
        ------
        RequestError
            If HTTP transport fails
        """
        variables = {"group": group, "event": event}
        return self._mutate(self._set_event_code(enabled), variables, group, timeout)

    def _mutate(
        self,
        xquery: str,
        variables: dict,
        group: str,
        timeout,
    ) -> TraceEvents:
        """Evaluate a config-saving mutation, then read the resulting state.

        The saved configuration only becomes visible to a fresh
        ``admin:get-configuration`` in a later transaction, so the state is read
        back with a separate request rather than in the mutation query.

        Parameters
        ----------
        xquery : str
            The mutation query, which must save the configuration.
        variables : dict
            External variables the mutation query requires.
        group : str
            The group to read back after the mutation.
        timeout : httpx.Timeout | float | None
            Per-request HTTP timeout for both requests.

        Returns
        -------
        TraceEvents
            The group's trace-event state after the mutation.

        Raises
        ------
        RequestError
            If HTTP transport fails
        """
        self._eval(xquery, variables, timeout)
        return self.get(group=group, timeout=timeout)

    def _eval(
        self,
        xquery: str,
        variables: dict,
        timeout,
    ) -> Response:
        """Evaluate a query and fail loudly when the server does not answer OK.

        Parameters
        ----------
        xquery : str
            The query to evaluate.
        variables : dict
            External variables the query requires.
        timeout : httpx.Timeout | float | None
            Per-request HTTP timeout.

        Returns
        -------
        Response
            The successful HTTP response.

        Raises
        ------
        MarkLogicError
            If MarkLogic answered with an error it described.
        HTTPStatusError
            If a non-success status carried no MarkLogic error body, as when a
            gateway answers because the server is down or unreachable.
        RequestError
            If HTTP transport fails.
        """
        resp = self._rest.eval.post(xquery=xquery, variables=variables, timeout=timeout)
        if not resp.is_success:
            error = MLResponseParser.parse(resp)
            if error:
                raise MarkLogicError(error)
            resp.raise_for_status()
        return resp

    @staticmethod
    def _get_code() -> str:
        """Build the Admin-module query reading activation and enabled events.

        Returns
        -------
        str
            XQuery returning a JSON object with an ``activated`` boolean and an
            ``events`` array of trace-event names, using an external group name.
        """
        return (
            f"{_ADMIN_MODULE_IMPORT}"
            "declare variable $group external; "
            "let $cfg := admin:get-configuration() "
            "let $gid := admin:group-get-id($cfg, $group) "
            "return object-node { "
            '"activated": admin:group-get-trace-events-activated($cfg, $gid), '
            '"events": array-node { '
            "admin:group-get-trace-events($cfg, $gid) ! fn:string(.) } }"
        )

    @staticmethod
    def _set_activated_code() -> str:
        """Build the Admin-module query saving the master activation switch.

        Returns
        -------
        str
            XQuery using external ``group`` and ``value`` variables.
        """
        return (
            f"{_ADMIN_MODULE_IMPORT}"
            "declare variable $group external; "
            "declare variable $value external; "
            "let $cfg := admin:get-configuration() "
            "let $gid := admin:group-get-id($cfg, $group) "
            "return admin:group-set-trace-events-activated("
            "$cfg, $gid, xs:boolean($value)) "
            "=> admin:save-configuration()"
        )

    @staticmethod
    def _set_event_code(
        enabled: bool,
    ) -> str:
        """Build the Admin-module query adding or removing one trace event.

        Parameters
        ----------
        enabled : bool
            True builds an add query; False builds a delete query.

        Returns
        -------
        str
            XQuery using external ``group`` and ``event`` variables.
        """
        action = "add" if enabled else "delete"
        return (
            f"{_ADMIN_MODULE_IMPORT}"
            "declare variable $group external; "
            "declare variable $event external; "
            "let $cfg := admin:get-configuration() "
            "let $gid := admin:group-get-id($cfg, $group) "
            f"return admin:group-{action}-trace-event("
            "$cfg, $gid, admin:group-trace-event($event)) "
            "=> admin:save-configuration()"
        )
