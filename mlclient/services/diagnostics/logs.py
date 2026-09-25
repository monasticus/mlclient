"""Diagnostic Logs service (LogsService / AsyncLogsService).

Provides parsed log retrieval from MarkLogic.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

from dateutil.parser import isoparse

from mlclient._options import UNSET
from mlclient.exceptions import MarkLogicError
from mlclient.models.types import LogType
from mlclient.responses import MLResponseParser

if TYPE_CHECKING:
    from mlclient.api.manage import AsyncManageApi, ManageApi


class LogsService:
    """Higher-level service for /manage/v2/logs endpoint."""

    _LOG_TYPES_RE = "|".join(t.value[:-3] for t in LogType)
    _FILENAME_RE = re.compile(rf"((.+)_)?({_LOG_TYPES_RE})Log(_([1-6]))?\.txt")

    def __init__(self, manage: ManageApi):
        self._manage = manage

    def get(
        self,
        app_server: int | str | None = None,
        log_type: LogType | str = LogType.ERROR,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        regex: str | None = None,
        host: str | None = None,
        timeout=UNSET,
    ) -> Iterator[dict]:
        """Return logs from a MarkLogic server.

        Parameters
        ----------
        app_server : int | str | None, default None
            An app server (port) with logs to retrieve
        log_type : LogType | str, default LogType.ERROR
            A log type (enum or string: "error", "access", "request", "audit")
        start_time : str | None, default None
            A start time to search error logs
        end_time : str | None, default None
            An end time to search error logs
        regex : str | None, default None
            A regex to search error logs
        host : str | None, default None
            A host name with logs to retrieve
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them.

        Returns
        -------
        Iterator[dict]
            A log details generator.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        """
        if isinstance(log_type, str):
            log_type = LogType.get(log_type)
        is_error = log_type == LogType.ERROR
        resp = self._manage.logs.get(
            self._filename(app_server, log_type),
            data_format="json",
            host=host,
            start_time=start_time if is_error else None,
            end_time=end_time if is_error else None,
            regex=regex if is_error else None,
            timeout=timeout,
        )
        MLResponseParser.raise_for_status(resp)
        return self._parse_logs(log_type, resp.json())

    def list(
        self,
        host: str | None = None,
        *,
        timeout=UNSET,
    ) -> dict:
        """Return a logs list from a MarkLogic server.

        Parameters
        ----------
        host : str | None, default None
            A host name with log files to retrieve
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them.

        Returns
        -------
        dict
            A parsed list of log files in the MarkLogic server

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        """
        resp = self._manage.logs.get(
            filename=None,
            data_format="json",
            host=host,
            timeout=timeout,
        )
        resp_body = resp.json()
        if "errorResponse" in resp_body:
            raise MarkLogicError(resp_body["errorResponse"])

        return self._parse_logs_list(resp_body)

    @staticmethod
    def _filename(
        app_server: int | str | None,
        log_type: LogType,
    ) -> str:
        """Build the log file name from an app server and log type."""
        if app_server in [0, "0"]:
            app_server = "TaskServer"
        if app_server is None:
            return f"{log_type.value}.txt"
        return f"{app_server}_{log_type.value}.txt"

    @staticmethod
    def _parse_logs(
        log_type: LogType,
        resp_body: dict,
    ) -> Iterator[dict]:
        """Parse MarkLogic logs depending on their type."""
        logfile = resp_body["logfile"]
        if log_type == LogType.ERROR:
            logs = logfile.get("log", ())
            return iter(
                sorted(
                    logs,
                    key=lambda log: isoparse(log["timestamp"]),
                ),
            )
        if "message" not in logfile:
            return iter([])
        return ({"message": log} for log in logfile["message"].split("\n"))

    @classmethod
    def _parse_logs_list(
        cls,
        resp_body: dict,
    ) -> dict:
        """Parse MarkLogic logs list."""
        count = resp_body["log-default-list"]["list-items"]["list-count"]["value"]
        if count > 0:
            source_items = resp_body["log-default-list"]["list-items"]["list-item"]
            parsed = [cls._parse_log_file(log_item) for log_item in source_items]
            grouped = cls._group_log_files(parsed)
        else:
            source_items = []
            parsed = []
            grouped = {}

        return {
            "source": source_items,
            "parsed": parsed,
            "grouped": grouped,
        }

    @classmethod
    def _parse_log_file(
        cls,
        source_log_item: dict,
    ) -> dict:
        """Parse MarkLogic logs list item."""
        file_name = source_log_item["nameref"]
        host = source_log_item["roleref"]
        match = cls._FILENAME_RE.match(file_name)
        server = match.group(2)
        log_type = LogType.get(match.group(3))
        days_ago = int(match.group(5) or 0)
        return {
            "host": host,
            "file-name": file_name,
            "server": server,
            "log-type": log_type,
            "days-ago": days_ago,
        }

    @staticmethod
    def _group_log_files(
        parsed_log_items: list[dict],
    ) -> dict:
        """Group parsed logs items."""
        grouped = {}
        for item in parsed_log_items:
            host = item["host"]
            file_name = item["file-name"]
            server = item["server"]
            log_type = item["log-type"]
            days_ago = item["days-ago"]

            if host not in grouped:
                grouped[host] = {}
            if server not in grouped[host]:
                grouped[host][server] = {}
            if log_type not in grouped[host][server]:
                grouped[host][server][log_type] = {}
            grouped[host][server][log_type][days_ago] = file_name

        return grouped


class AsyncLogsService(LogsService):
    """Async higher-level service for /manage/v2/logs endpoint."""

    def __init__(self, manage: AsyncManageApi):
        self._manage = manage

    async def get(  # type: ignore[override]
        self,
        app_server: int | str | None = None,
        log_type: LogType | str = LogType.ERROR,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        regex: str | None = None,
        host: str | None = None,
        timeout=UNSET,
    ) -> Iterator[dict]:
        """Return logs from a MarkLogic server.

        Parameters
        ----------
        app_server : int | str | None, default None
            An app server (port) with logs to retrieve
        log_type : LogType | str, default LogType.ERROR
            A log type (enum or string: "error", "access", "request", "audit")
        start_time : str | None, default None
            A start time to search error logs
        end_time : str | None, default None
            An end time to search error logs
        regex : str | None, default None
            A regex to search error logs
        host : str | None, default None
            A host name with logs to retrieve
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them.

        Returns
        -------
        Iterator[dict]
            A log details generator.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        """
        if isinstance(log_type, str):
            log_type = LogType.get(log_type)
        is_error = log_type == LogType.ERROR
        resp = await self._manage.logs.get(
            self._filename(app_server, log_type),
            data_format="json",
            host=host,
            start_time=start_time if is_error else None,
            end_time=end_time if is_error else None,
            regex=regex if is_error else None,
            timeout=timeout,
        )
        MLResponseParser.raise_for_status(resp)
        return self._parse_logs(log_type, resp.json())

    async def list(  # type: ignore[override]
        self,
        host: str | None = None,
        *,
        timeout=UNSET,
    ) -> dict:
        """Return a logs list from a MarkLogic server.

        Parameters
        ----------
        host : str | None, default None
            A host name with log files to retrieve
        timeout : httpx.Timeout | float | None, default unset
            A per-request HTTP timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them.

        Returns
        -------
        dict
            A parsed list of log files in the MarkLogic server

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic returns an error
        """
        resp = await self._manage.logs.get(
            filename=None,
            data_format="json",
            host=host,
            timeout=timeout,
        )
        resp_body = resp.json()
        if "errorResponse" in resp_body:
            raise MarkLogicError(resp_body["errorResponse"])

        return self._parse_logs_list(resp_body)
