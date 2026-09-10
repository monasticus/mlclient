"""Admin API group for /admin/v1/* endpoints (AdminApi / AsyncAdminApi).

Requires the Admin server (port 8001 by default).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import ApiCall
from mlclient.calls.admin import ServerConfigGetCall, TimestampGetCall
from mlclient.connection import UNSET

if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient


class AdminApi:
    """Admin API group for /admin/v1/* endpoints.

    Requires the Admin server (port 8001 by default).
    """

    def __init__(self, api: ApiClient):
        self._api = api

    def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall.

        Parameters
        ----------
        call_ : ApiCall
            A specific endpoint call implementation
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response
        """
        return self._api.call(call_, timeout=timeout)

    def get_timestamp(self, *, timeout=UNSET) -> Response:
        """Verify that MarkLogic Server is up and accepting requests.

        Returns a plain text timestamp of the last restart. Can be used to
        detect when a restart triggered by an administrative operation has
        completed.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/timestamp

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``text/plain`` body containing the timestamp
        """
        return self._api.call(TimestampGetCall(), timeout=timeout)

    def get_server_config(self, *, timeout=UNSET) -> Response:
        """Retrieve server configuration information for cluster join.

        Returns the host configuration as XML, suitable for use as input to
        ``POST /admin/v1/cluster-config`` when adding this host to a cluster.

        Documentation: https://docs.marklogic.com/REST/GET/admin/v1/server-config

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this call. Unset uses the client's
            configured timeout; None disables every HTTP timeout; a number sets
            all four components to that many seconds; an httpx.Timeout overrides
            them. It is an execution option, never sent as a request parameter.

        Returns
        -------
        Response
            An HTTP response with ``application/xml`` body containing
            the server configuration
        """
        return self._api.call(ServerConfigGetCall(), timeout=timeout)


class AsyncAdminApi:
    """Async Admin API group for /admin/v1/* endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def call(self, call_: ApiCall, *, timeout=UNSET) -> Response:
        """Send a custom ApiCall."""
        return await self._api.call(call_, timeout=timeout)

    async def get_timestamp(self, *, timeout=UNSET) -> Response:
        """Verify that MarkLogic Server is up and accepting requests."""
        return await self._api.call(TimestampGetCall(), timeout=timeout)

    async def get_server_config(self, *, timeout=UNSET) -> Response:
        """Retrieve server configuration information for cluster join."""
        return await self._api.call(ServerConfigGetCall(), timeout=timeout)
