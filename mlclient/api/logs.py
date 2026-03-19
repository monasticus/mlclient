"""LogsApi - mid-level access to MarkLogic logs endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import LogsCall

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient


class LogsApi:
    """Mid-level API for /manage/v2/logs endpoint."""

    def __init__(self, rest: RestClient):
        self._rest = rest

    def get(
        self,
        filename: str,
        data_format: str | None = None,
        host: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        regex: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/logs endpoint."""
        call = LogsCall(
            filename=filename,
            data_format=data_format,
            host=host,
            start_time=start_time,
            end_time=end_time,
            regex=regex,
        )
        return self._rest.call(call)
