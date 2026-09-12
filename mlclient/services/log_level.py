"""Isolated log-level service (LogLevelService).

Reads or changes a MarkLogic file/system log level. It evaluates the Admin
module functions on the connected REST App-Server first and, only when that
fails because the connecting user lacks the required privileges, falls back to
the equivalent Management REST resource.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from xml.etree.ElementTree import ParseError

from httpx import RequestError

from mlclient.connection import UNSET
from mlclient.exceptions import MarkLogicError, WrongParametersError
from mlclient.ml_response_parser import MLResponseParser

if TYPE_CHECKING:
    from httpx import Response

    from mlclient.api.manage_api import ManageApi
    from mlclient.api.rest_api import RestApi

logger = logging.getLogger(__name__)

SUPPORTED_LEVELS = (
    "finest",
    "finer",
    "fine",
    "debug",
    "config",
    "info",
    "notice",
    "warning",
    "error",
    "critical",
    "alert",
    "emergency",
)
SUPPORTED_TYPES = ("file", "system")

_PRIVILEGE_MESSAGE_CODES = ("SEC-PRIV", "SEC-NOPRIV", "SEC-NOADMIN")
_PRIVILEGE_STATUS_CODES = (401, 403)

_ADMIN_MODULE_IMPORT = (
    'xquery version "1.0-ml"; '
    'import module namespace admin = "http://marklogic.com/xdmp/admin" '
    'at "/MarkLogic/admin.xqy"; '
)


class LogLevelService:
    """Get or set a group/App-Server log level, eval-first with Manage fallback."""

    def __init__(
        self,
        rest: RestApi,
        manage: ManageApi,
    ):
        """Initialize the service with REST and Manage API handles.

        Parameters
        ----------
        rest : RestApi
            Connected REST API used for Admin-module evaluation
        manage : ManageApi
            Management API used when eval lacks privileges
        """
        self._rest = rest
        self._manage = manage

    def get(
        self,
        *,
        group: str = "Default",
        server: str | None = None,
        log_type: str = "file",
        timeout=UNSET,
    ) -> str:
        """Return the current log level, falling back to Manage on privilege errors.

        Parameters
        ----------
        group : str, default "Default"
            The group whose log level is read, or that owns the App Server.
        server : str | None, default None
            An App Server name. When omitted the group log level is read.
        log_type : str, default "file"
            Either "file" or "system". App Servers expose only "file".
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset preserves each client's configured
            timeout; None disables it; a number applies to all four components;
            an httpx.Timeout sets them independently. An explicit override also
            applies to any Manage fallback request, not to the whole operation.

        Returns
        -------
        str
            The current log level.

        Raises
        ------
        WrongParametersError
            If the requested log type, target combination or level is invalid
        MarkLogicError
            If eval fails without a privilege error, or Management fallback fails
        RequestError
            If HTTP transport fails; transport errors do not trigger fallback
        """
        self._validate(server, log_type, level=None)
        logger.debug("Log-level get: attempting eval using the Admin module")
        try:
            resp = self._rest.eval.post(
                xquery=self._get_code(server, log_type),
                variables=self._vars(group, server),
                timeout=timeout,
            )
        except RequestError as exc:
            logger.debug("Log-level eval transport failure; no fallback: %s", exc)
            raise
        if resp.is_success:
            logger.debug("Log-level eval succeeded")
            return MLResponseParser.parse(resp)
        _raise_unless_privilege_error(resp)
        return self._manage_get(group, server, log_type, timeout=timeout)

    def set(
        self,
        level: str,
        *,
        group: str = "Default",
        server: str | None = None,
        log_type: str = "file",
        timeout=UNSET,
    ) -> str:
        """Change the log level, falling back to Manage on privilege errors.

        Parameters
        ----------
        level : str
            The new log level. Must be one of :data:`SUPPORTED_LEVELS`.
        group : str, default "Default"
            The group whose log level is changed, or that owns the App Server.
        server : str | None, default None
            An App Server name. When omitted the group log level is changed.
        log_type : str, default "file"
            Either "file" or "system". App Servers expose only "file".
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset preserves each client's configured
            timeout; None disables it; a number applies to all four components;
            an httpx.Timeout sets them independently. An explicit override also
            applies to any Manage fallback request, not to the whole operation.

        Returns
        -------
        str
            The level that was set.

        Raises
        ------
        WrongParametersError
            If the requested log type, target combination or level is invalid
        MarkLogicError
            If eval fails without a privilege error, or Management fallback fails
        RequestError
            If HTTP transport fails; transport errors do not trigger fallback
        """
        self._validate(server, log_type, level=level)
        logger.debug("Log-level set: attempting eval using the Admin module")
        try:
            resp = self._rest.eval.post(
                xquery=self._set_code(server, log_type),
                variables=self._vars(group, server, level),
                timeout=timeout,
            )
        except RequestError as exc:
            logger.debug("Log-level eval transport failure; no fallback: %s", exc)
            raise
        if resp.is_success:
            logger.debug("Log-level eval succeeded")
            return level
        _raise_unless_privilege_error(resp)
        return self._manage_set(group, server, log_type, level, timeout=timeout)

    def _manage_get(
        self,
        group: str,
        server: str | None,
        log_type: str,
        *,
        timeout=UNSET,
    ) -> str:
        """Read a group or App Server log level through Management REST.

        Parameters
        ----------
        group : str
            Group name
        server : str | None
            App Server name, or None to target the group
        log_type : str
            Validated file or system log selector
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset preserves each client's configured
            timeout; None disables it; a number applies to all four components;
            an httpx.Timeout sets them independently. An explicit override also
            applies to any Manage fallback request, not to the whole operation.

        Returns
        -------
        str
            The configured level

        Raises
        ------
        MarkLogicError
            If the Management request fails
        RequestError
            If HTTP transport fails
        """
        logger.debug("Log-level get: attempting Manage REST")
        try:
            if server is None:
                resp = self._manage.groups.get_properties(
                    group,
                    data_format="json",
                    timeout=timeout,
                )
            else:
                resp = self._manage.servers.get_properties(
                    server,
                    group,
                    data_format="json",
                    timeout=timeout,
                )
        except RequestError as exc:
            logger.debug(
                "Log-level Manage transport failure; no further fallback: %s", exc,
            )
            raise
        _raise_if_manage_failed(
            resp,
            role="manage-admin" if server is None else "manage-user",
        )
        return resp.json()[f"{log_type}-log-level"]

    def _manage_set(
        self,
        group: str,
        server: str | None,
        log_type: str,
        level: str,
        *,
        timeout=UNSET,
    ) -> str:
        """Update only the requested log-level property through Management REST.

        Parameters
        ----------
        group : str
            Group name
        server : str | None
            App Server name, or None to target the group
        log_type : str
            Validated file or system log selector
        level : str
            Validated log level
        timeout : httpx.Timeout | float | None, default unset
            Per-request HTTP timeout. Unset preserves each client's configured
            timeout; None disables it; a number applies to all four components;
            an httpx.Timeout sets them independently. An explicit override also
            applies to any Manage fallback request, not to the whole operation.

        Returns
        -------
        str
            The level successfully submitted to the server

        Raises
        ------
        MarkLogicError
            If the Management request fails
        RequestError
            If HTTP transport fails
        """
        body = {f"{log_type}-log-level": level}
        logger.debug("Log-level set: attempting Manage REST")
        try:
            if server is None:
                resp = self._manage.groups.put_properties(
                    group, body=body, timeout=timeout,
                )
            else:
                resp = self._manage.servers.put_properties(
                    server,
                    group,
                    body=body,
                    timeout=timeout,
                )
        except RequestError as exc:
            logger.debug(
                "Log-level Manage transport failure; no further fallback: %s", exc,
            )
            raise
        _raise_if_manage_failed(resp, role="manage-admin")
        return level

    @staticmethod
    def _get_code(
        server: str | None,
        log_type: str,
    ) -> str:
        """Build the Admin-module query for reading a log level.

        Parameters
        ----------
        server : str | None
            App Server name, or None to target a group
        log_type : str
            Validated file or system log selector

        Returns
        -------
        str
            XQuery using external variables for target names
        """
        if server is None:
            return (
                f"{_ADMIN_MODULE_IMPORT}"
                "declare variable $group external; "
                "let $cfg := admin:get-configuration() "
                f"return admin:group-get-{log_type}-log-level("
                "$cfg, admin:group-get-id($cfg, $group))"
            )
        return (
            f"{_ADMIN_MODULE_IMPORT}"
            "declare variable $group external; "
            "declare variable $server external; "
            "let $cfg := admin:get-configuration() "
            "return admin:appserver-get-file-log-level($cfg, "
            "admin:appserver-get-id($cfg, admin:group-get-id($cfg, $group), $server))"
        )

    @staticmethod
    def _set_code(
        server: str | None,
        log_type: str,
    ) -> str:
        """Build the Admin-module query for setting and saving a log level.

        Parameters
        ----------
        server : str | None
            App Server name, or None to target a group
        log_type : str
            Validated file or system log selector

        Returns
        -------
        str
            XQuery using external variables for target names and the level
        """
        if server is None:
            return (
                f"{_ADMIN_MODULE_IMPORT}"
                "declare variable $group external; "
                "declare variable $level external; "
                "let $cfg := admin:get-configuration() "
                f"return admin:group-set-{log_type}-log-level("
                "$cfg, admin:group-get-id($cfg, $group), $level) "
                "=> admin:save-configuration()"
            )
        return (
            f"{_ADMIN_MODULE_IMPORT}"
            "declare variable $group external; "
            "declare variable $server external; "
            "declare variable $level external; "
            "let $cfg := admin:get-configuration() "
            "return admin:appserver-set-file-log-level($cfg, "
            "admin:appserver-get-id($cfg, admin:group-get-id($cfg, $group), $server), "
            "$level) "
            "=> admin:save-configuration()"
        )

    @staticmethod
    def _vars(
        group: str,
        server: str | None,
        level: str | None = None,
    ) -> dict:
        """Build external variables without interpolating user input into XQuery.

        Parameters
        ----------
        group : str
            Group name
        server : str | None
            Optional App Server name
        level : str | None
            Optional level for a write operation

        Returns
        -------
        dict
            Variables required by the selected query
        """
        variables = {"group": group}
        if server is not None:
            variables["server"] = server
        if level is not None:
            variables["level"] = level
        return variables

    @staticmethod
    def _validate(
        server: str | None,
        log_type: str,
        level: str | None,
    ):
        """Validate log selectors and any proposed level before making requests.

        Parameters
        ----------
        server : str | None
            Optional App Server name
        log_type : str
            File or system log selector
        level : str | None
            Proposed level, or None for a read

        Raises
        ------
        WrongParametersError
            If a selector or level is unsupported, or system targets an App Server
        """
        if log_type not in SUPPORTED_TYPES:
            supported = ", ".join(SUPPORTED_TYPES)
            msg = (
                f"Unsupported log type: {log_type!r}. Supported types are: {supported}."
            )
            raise WrongParametersError(msg)
        if server is not None and log_type == "system":
            msg = (
                "App Servers have no system log level. "
                'Use log_type="file", or omit server to target the group.'
            )
            raise WrongParametersError(msg)
        if level is not None and level not in SUPPORTED_LEVELS:
            supported = ", ".join(SUPPORTED_LEVELS)
            msg = (
                f"Unsupported log level: {level!r}. Supported levels are: {supported}."
            )
            raise WrongParametersError(msg)


def _error_body(resp: Response) -> dict | str:
    """Decode a MarkLogic error, retaining raw text for unstructured failures.

    Parameters
    ----------
    resp : Response
        Failed HTTP response, possibly produced by an authentication proxy

    Returns
    -------
    dict | str
        The MarkLogic error object or the original response text
    """
    content_type = resp.headers.get("content-type", "")
    if "json" not in content_type and "xml" not in content_type:
        return resp.text
    try:
        parsed = MLResponseParser.parse(resp)
    except (ValueError, ParseError, AttributeError):
        return resp.text
    if isinstance(parsed, dict):
        error = parsed.get("errorResponse", parsed)
        if isinstance(error, dict):
            return error
    return resp.text


def _is_privilege_error(resp: Response, error: dict | str) -> bool:
    """Identify authorization errors by HTTP status or MarkLogic message code.

    Parameters
    ----------
    resp : Response
        Failed HTTP response
    error : dict | str
        Decoded MarkLogic error or raw response text

    Returns
    -------
    bool
        Whether the response indicates missing authentication or privileges
    """
    return resp.status_code in _PRIVILEGE_STATUS_CODES or (
        isinstance(error, dict) and error.get("messageCode") in _PRIVILEGE_MESSAGE_CODES
    )


def _raise_unless_privilege_error(resp: Response) -> None:
    """Allow Manage fallback only for an eval authorization failure.

    Parameters
    ----------
    resp : Response
        Failed eval response

    Raises
    ------
    MarkLogicError
        If the error does not indicate missing authentication or privileges
    """
    error = _error_body(resp)
    if not _is_privilege_error(resp, error):
        logger.debug(
            "Log-level eval failed (HTTP %s); no fallback: %s", resp.status_code, error,
        )
        raise MarkLogicError(error)
    logger.debug(
        "Log-level eval authorization failure (HTTP %s); falling back to Manage: %s",
        resp.status_code,
        error,
    )


def _raise_if_manage_failed(resp: Response, *, role: str) -> None:
    """Preserve Manage errors and add a role hint only for authorization errors.

    Parameters
    ----------
    resp : Response
        Management API response
    role : str
        Role granting access to the specific Management endpoint

    Raises
    ------
    MarkLogicError
        If Manage failed, including its original error and any role hint
    """
    if resp.is_success:
        logger.debug("Log-level Manage succeeded")
        return
    error = _error_body(resp)
    logger.debug(
        "Log-level Manage failed (HTTP %s); no further fallback: %s",
        resp.status_code,
        error,
    )
    if _is_privilege_error(resp, error):
        msg = (
            f"Log-level access denied. The Manage fallback requires '{role}' "
            f"or equivalent privileges. Manage responded: {MarkLogicError(error)}"
        )
        raise MarkLogicError(msg)
    raise MarkLogicError(error)
