"""The ML Logs Client module.

It exports high-level classes to easily read MarkLogicLogs:
    * LogsClient
        An MLResourceClient calling /manage/v2/logs endpoint.
    * LogType
        An enumeration class representing MarkLogic log types.
"""
from __future__ import annotations

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
        msg = "Invalid log type! Allowed values are: error, access, request."
        raise InvalidLogTypeError(msg)


class LogsClient(MLResourceClient):
    """An MLResourceClient calling /manage/v2/logs endpoint.

    It is a high-level class parsing MarkLogic response and extracting logs from
    the server.
    """

    def get_logs(
            self,
            app_server: int | str,
            log_type: LogType = LogType.ERROR,
            start_time: str | None = None,
            end_time: str | None = None,
            regex: str | None = None,
            host: str | None = None,
    ) -> Iterator[dict]:
        """Return logs from a MarkLogic server.

        Parameters
        ----------
        app_server : int | str
            An app server (port) with logs to retrieve
        log_type : LogType, default LogType.ERROR
            A log type
        start_time : str | None = None
            A start time to search error logs
        end_time : str | None = None
            An end time to search error logs
        regex : str | None = None
            A regex to search error logs
        host : str | None = None
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

        resp_json = self.call(call).json()
        if "errorResponse" in resp_json:
            raise MarkLogicError(resp_json["errorResponse"])

        return self._parse_logs(log_type, resp_json)

    @staticmethod
    def _get_call(
            app_server: int | str,
            log_type: LogType,
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
        app_server : int | str
            An app server (port) with logs to retrieve
        log_type : LogType
            A log type
        start_time : str | None = None
            A start time to search error logs
        end_time : str | None = None
            An end time to search error logs
        regex : str | None = None
            A regex to search error logs
        host : str | None = None
            The host from which to return the log data.

        Returns
        -------
        LogsCall
            A prepared LogsCall instance
        """
        if app_server in [0, "0"]:
            app_server = "TaskServer"
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
            resp_json: dict,
    ) -> Iterator[dict]:
        """Parse MarkLogic logs depending on their type.

        Parameters
        ----------
        log_type : LogType
            A log type
        resp_json : dict
            A JSON response from an MarkLogic server

        Returns
        -------
        Iterator[dict]
            A log details generator.
        """
        logfile = resp_json["logfile"]
        if log_type == LogType.ERROR:
            logs = logfile.get("log", ())
            return iter(sorted(logs, key=lambda log: log["timestamp"]))
        return ({"message": log} for log in logfile["message"].split("\n"))


