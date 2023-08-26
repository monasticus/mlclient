from __future__ import annotations

from enum import Enum
from typing import Iterator

from mlclient import MLResourceClient
from mlclient.calls import LogsCall


class LogType(Enum):
    ERROR = "ErrorLog"
    ACCESS = "AccessLog"
    REQUEST = "RequestLog"


class LogsClient(MLResourceClient):

    def get_logs(
            self,
            app_server_port: int,
            log_type: LogType = LogType.ERROR,
            start_time: str | None = None,
            end_time: str | None = None,
            regex: str | None = None,
            host: str | None = None,
    ) -> Iterator[dict]:
        call = self._get_call(app_server_port, log_type, start_time, end_time, regex, host)
        logfile = self.call(call).json()["logfile"]
        if log_type == LogType.ERROR:
            logs = logfile["log"]
            return iter(sorted(logs, key=lambda log: log["timestamp"]))
        return ({"message": log} for log in logfile["message"].split("\n"))

    @staticmethod
    def _get_call(
            app_server_port: int,
            log_type: LogType = LogType.ERROR,
            start_time: str | None = None,
            end_time: str | None = None,
            regex: str | None = None,
            host: str | None = None,
    ) -> LogsCall:
        file_name = f"{app_server_port}_{log_type.value}.txt"
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


