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

    def __init__(self, api: ApiClient):
        self._api = api

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
        return self._api.call(call_)

    def get_timestamp(self) -> Response:
        """Verify that MarkLogic Server is up and accepting requests.

        Returns a plain text timestamp of the last restart. Can be used to
        detect when a restart triggered by an administrative operation has
        completed.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/timestamp

        Returns
        -------
        Response
            An HTTP response with ``text/plain`` body containing the timestamp
        """
        return self._api.call(TimestampGetCall())

    def get_server_config(self) -> Response:
        """Retrieve server configuration information for cluster join.

        Returns the host configuration as XML, suitable for use as input to
        ``POST /admin/v1/cluster-config`` when adding this host to a cluster.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/server-config

        Returns
        -------
        Response
            An HTTP response with ``application/xml`` body containing
            the server configuration
        """
        return self._api.call(ServerConfigGetCall())
