"""Management API group for /manage/v2/* endpoints.

Requires the Manage server (port 8002 by default).
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import RestCall

# Avoid circular import: RestClient -> api classes -> RestClient
if TYPE_CHECKING:
    from mlclient.clients.rest_client import RestClient

from .databases import DatabasesApi
from .forests import ForestsApi
from .logs import LogsApi
from .roles import RolesApi
from .servers import ServersApi
from .users import UsersApi


class ManageApi:
    """Management API group for /manage/v2/* endpoints.

    Requires the Manage server (port 8002 by default).
    """

    def __init__(self, client: RestClient):
        self._client = client

    def call(self, call_: RestCall) -> Response:
        """Send a custom RestCall.

        Parameters
        ----------
        call_ : RestCall
            A specific endpoint call implementation

        Returns
        -------
        Response
            An HTTP response
        """
        return self._client.call(call_)

    @cached_property
    def databases(self) -> DatabasesApi:
        """Return the databases API group."""
        return DatabasesApi(self._client)

    @cached_property
    def forests(self) -> ForestsApi:
        """Return the forests API group."""
        return ForestsApi(self._client)

    @cached_property
    def logs(self) -> LogsApi:
        """Return the logs API group."""
        return LogsApi(self._client)

    @cached_property
    def roles(self) -> RolesApi:
        """Return the roles API group."""
        return RolesApi(self._client)

    @cached_property
    def servers(self) -> ServersApi:
        """Return the servers API group."""
        return ServersApi(self._client)

    @cached_property
    def users(self) -> UsersApi:
        """Return the users API group."""
        return UsersApi(self._client)
