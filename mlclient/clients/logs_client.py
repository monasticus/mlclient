"""The ML Logs Client module.

It exports high-level classes to easily read MarkLogic logs:
    * LogsClient
        An MLResourceClient calling /manage/v2/logs endpoint.
    * LogType
        An enumeration class representing MarkLogic log types.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Iterator

from mlclient.calls import LogsCall
from mlclient.clients import MLResourceClient
from mlclient.exceptions import InvalidLogTypeError, MarkLogicError


class LogType(Enum):
    """An enumeration class representing MarkLogic log types."""

    ERROR = "ErrorLog"
    ACCESS = "AccessLog"
    REQUEST = "RequestLog"
    AUDIT = "AuditLog"

    @staticmethod
    def get(
            logs_type: str,
    ) -> LogType:
        """Get a specific LogType enum for a string value.

        Parameters
        ----------
        logs_type : str,
            A log type

        Returns
        -------
        LogType
            A LogType enum
        """
        if logs_type.lower() == "error":
            return LogType.ERROR
        if logs_type.lower() == "access":
            return LogType.ACCESS
        if logs_type.lower() == "request":
            return LogType.REQUEST
        if logs_type.lower() == "audit":
            return LogType.AUDIT
        msg = "Invalid log type! Allowed values are: error, access, request."
        raise InvalidLogTypeError(msg)

    def __lt__(
            self,
            other: LogType,
    ):
        """Compare LogTypes with LT operator.

        Parameters
        ----------
        other : LogType
            An other LogType instance

        Returns
        -------
        bool
            A comparison result.
        """
        return self.value < other.value


class LogsClient(MLResourceClient):
    """An MLResourceClient calling /manage/v2/logs endpoint.

    It is a high-level class parsing MarkLogic response and extracting logs from
    the server.
    """

    _LOG_TYPES_RE = "|".join(t.value[:-3] for t in LogType)
    _FILENAME_RE = re.compile(rf"((.+)_)?({_LOG_TYPES_RE})Log(_([1-6]))?\.txt")

    def get_logs(
            self,
            app_server: int | str | None = None,
            log_type: LogType = LogType.ERROR,
            start_time: str | None = None,
            end_time: str | None = None,
            regex: str | None = None,
            host: str | None = None,
    ) -> Iterator[dict]:
        """Return logs from a MarkLogic server.

        Parameters
        ----------
        app_server : int | str | None, default None
            An app server (port) with logs to retrieve
        log_type : LogType, default LogType.ERROR
            A log type
        start_time : str | None, default None
            A start time to search error logs
        end_time : str | None, default None
            An end time to search error logs
        regex : str | None, default None
            A regex to search error logs
        host : str | None, default None
            A host name with logs to retrieve

        Returns
        -------
        Iterator[dict]
            A log details generator.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error (most likely XDMP-NOSUCHHOST)
        """
        call = self._get_call(
            app_server=app_server,
            log_type=log_type,
            start_time=start_time,
            end_time=end_time,
            regex=regex,
            host=host)

        resp = self.call(call)
        resp_body = resp.json()
        if "errorResponse" in resp_body:
            raise MarkLogicError(resp_body["errorResponse"])

        return self._parse_logs(log_type, resp_body)

    def get_logs_list(
            self,
    ) -> dict:
        """Return a logs list from a MarkLogic server.

        Result of this method is a parsed dict of log files with 3 keys:
        * source: points to origin log list items
        * parsed: points to parsed log list items
          includes a filename, server, log type and a number of days
        * grouped: points to a dictionary
          { <server>: { <log-type>: { <num-of-days>: <file-name> } } }

        Returns
        -------
        list
            A parsed list of log files in the MarkLogic server

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error
        """
        call = self._get_call()

        resp = self.call(call)
        resp_body = resp.json()
        if "errorResponse" in resp_body:
            raise MarkLogicError(resp_body["errorResponse"])

        return self._parse_logs_list(resp_body)

    @staticmethod
    def _get_call(
            app_server: int | str | None = None,
            log_type: LogType | None = None,
            start_time: str | None = None,
            end_time: str | None = None,
            regex: str | None = None,
            host: str | None = None,
    ) -> LogsCall:
        """Prepare a LogsCall instance.

        It initializes a LogsCall instance with adjusted parameters. When log type
        is not ERROR, search params are ignored: start_time, end_time and regex.

        Parameters
        ----------
        app_server : int | str | None, default None
            An app server (port) with logs to retrieve
        log_type : LogType | None, default None
            A log type
        start_time : str | None, default None
            A start time to search error logs
        end_time : str | None, default None
            An end time to search error logs
        regex : str | None, default None
            A regex to search error logs
        host : str | None, default None
            The host from which to return the log data.

        Returns
        -------
        LogsCall
            A prepared LogsCall instance
        """
        if app_server in [0, "0"]:
            app_server = "TaskServer"
        if log_type is None:
            file_name = None
        elif app_server is None:
            file_name = f"{log_type.value}.txt"
        else:
            file_name = f"{app_server}_{log_type.value}.txt"
        params = {
            "filename": file_name,
            "data_format": "json",
            "host": host,
        }
        if log_type == LogType.ERROR:
            params.update({
                "start_time": start_time,
                "end_time": end_time,
                "regex": regex,
            })

        return LogsCall(**params)

    @staticmethod
    def _parse_logs(
            log_type: LogType,
            resp_body: dict,
    ) -> Iterator[dict]:
        """Parse MarkLogic logs depending on their type.

        Parameters
        ----------
        log_type : LogType
            A log type
        resp_body : dict
            A JSON response body from an MarkLogic server

        Returns
        -------
        Iterator[dict]
            A log details generator.
        """
        logfile = resp_body["logfile"]
        if log_type == LogType.ERROR:
            logs = logfile.get("log", ())
            return iter(sorted(logs, key=lambda log: log["timestamp"]))
        if "message" not in logfile:
            return iter([])
        return ({"message": log} for log in logfile["message"].split("\n"))

    @classmethod
    def _parse_logs_list(
            cls,
            resp_body: dict,
    ) -> dict:
        """Parse MarkLogic logs list.

        Parameters
        ----------
        resp_body : dict
            A JSON response body from an MarkLogic server

        Returns
        -------
        dict
            A compiled information about ML log files
        """
        source_items = resp_body["log-default-list"]["list-items"]["list-item"]
        parsed = [cls._parse_log_file(log_item) for log_item in source_items]
        grouped = cls._group_log_files(parsed)

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
        """Parse MarkLogic logs list item.

        Parameters
        ----------
        source_log_item : dict
            A source item of log list received from an ML server.

        Returns
        -------
        dict
            A parsed log item
        """
        file_name = source_log_item["nameref"]
        match = cls._FILENAME_RE.match(file_name)
        server = match.group(2)
        log_type = LogType.get(match.group(3))
        days_ago = int(match.group(5) or 0)
        return {
            "file-name": file_name,
            "server": server,
            "log-type": log_type,
            "days-ago": days_ago,
        }

    @staticmethod
    def _group_log_files(
            parsed_log_items: list[dict],
    ) -> dict:
        """Group parsed logs items.

        Parameters
        ----------
        parsed_log_items : list[dict]
            Parsed log items

        Returns
        -------
        dict
            Log items grouped by server, log type and number of days
        """
        grouped = {}
        for item in parsed_log_items:
            file_name = item["file-name"]
            server = item["server"]
            log_type = item["log-type"]
            days_ago = item["days-ago"]

            if server not in grouped:
                grouped[server] = {}
            if log_type not in grouped[server]:
                grouped[server][log_type] = {}
            grouped[server][log_type][days_ago] = file_name

        return grouped
