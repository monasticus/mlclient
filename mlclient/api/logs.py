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
        *,
        data_format: str | None = None,
        host: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        regex: str | None = None,
    ) -> Response:
        """Send a GET request to the /manage/v2/logs endpoint.

        Parameters
        ----------
        filename : str
            The log file to be returned.
        data_format : str
            The format of the data in the log file. The supported formats are xml, json
            or html.
        host : str
            The host from which to return the log data.
        start_time : str
            The start time for the log data.
        end_time : str
            The end time for the log data.
        regex : str
            Filters the log data, based on a regular expression.

        Returns
        -------
        Response
            An HTTP response
        """
        call = LogsCall(
            filename=filename,
            data_format=data_format,
            host=host,
            start_time=start_time,
            end_time=end_time,
            regex=regex,
        )
        return self._rest.call(call)
