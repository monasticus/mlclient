"""LogsApi - mid-level access to MarkLogic logs endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import LogsCall

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient


class LogsApi:
    """Mid-level API for ``/manage/v2/logs`` endpoint.

    Retrieve log file contents from MarkLogic Server.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

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
        """Retrieve the contents of a log file.

        Documentation: https://docs.marklogic.com/REST/GET/manage/v2/logs

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
            An HTTP response containing the log data
        """
        call = LogsCall(
            filename=filename,
            data_format=data_format,
            host=host,
            start_time=start_time,
            end_time=end_time,
            regex=regex,
        )
        return self._api.call(call)
