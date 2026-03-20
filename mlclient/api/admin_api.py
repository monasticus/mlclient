"""Admin API group for /admin/v1/* endpoints.

Requires the Admin server (port 8001 by default).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import ApiCall
from mlclient.calls.admin import ServerConfigGetCall, TimestampGetCall

if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient


class AdminApi:
    """Admin API group for /admin/v1/* endpoints.

    Requires the Admin server (port 8001 by default).
    """

    def __init__(self, client: ApiClient):
        self._client = client

    def call(self, call_: ApiCall) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self._client.call(call_)

    def get_timestamp(self) -> Response:
        """Get the Admin server timestamp.

        Returns
        -------
        Response
            An HTTP response
        """
        return self._client.call(TimestampGetCall())

    def get_server_config(self) -> Response:
        """Get the Admin server configuration.

        Returns
        -------
        Response
            An HTTP response
        """
        return self._client.call(ServerConfigGetCall())
