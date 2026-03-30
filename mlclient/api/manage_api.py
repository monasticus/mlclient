"""Management API group for /manage/v2/* endpoints (ManageApi / AsyncManageApi).

Requires the Manage server (port 8002 by default).
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from httpx import Response

from mlclient.calls import ApiCall

# Avoid circular import: ApiClient -> api classes -> ApiClient
if TYPE_CHECKING:
    from mlclient.clients.api_client import ApiClient, AsyncApiClient

from .databases import AsyncDatabasesApi, DatabasesApi
from .forests import AsyncForestsApi, ForestsApi
from .logs import AsyncLogsApi, LogsApi
from .roles import AsyncRolesApi, RolesApi
from .servers import AsyncServersApi, ServersApi
from .users import AsyncUsersApi, UsersApi


class ManageApi:
    """Management API group for /manage/v2/* endpoints.

    Requires the Manage server (port 8002 by default).
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

    @cached_property
    def databases(self) -> DatabasesApi:
        """Return the databases API group."""
        return DatabasesApi(self._api)

    @cached_property
    def forests(self) -> ForestsApi:
        """Return the forests API group."""
        return ForestsApi(self._api)

    @cached_property
    def logs(self) -> LogsApi:
        """Return the logs API group."""
        return LogsApi(self._api)

    @cached_property
    def roles(self) -> RolesApi:
        """Return the roles API group."""
        return RolesApi(self._api)

    @cached_property
    def servers(self) -> ServersApi:
        """Return the servers API group."""
        return ServersApi(self._api)

    @cached_property
    def users(self) -> UsersApi:
        """Return the users API group."""
        return UsersApi(self._api)


class AsyncManageApi:
    """Async Management API group for /manage/v2/* endpoints."""

    def __init__(self, api: AsyncApiClient):
        self._api = api

    async def call(self, call_: ApiCall) -> Response:
        """Send a custom ApiCall."""
        return await self._api.call(call_)

    @cached_property
    def databases(self) -> AsyncDatabasesApi:
        """Return the databases API group."""
        return AsyncDatabasesApi(self._api)

    @cached_property
    def forests(self) -> AsyncForestsApi:
        """Return the forests API group."""
        return AsyncForestsApi(self._api)

    @cached_property
    def logs(self) -> AsyncLogsApi:
        """Return the logs API group."""
        return AsyncLogsApi(self._api)

    @cached_property
    def roles(self) -> AsyncRolesApi:
        """Return the roles API group."""
        return AsyncRolesApi(self._api)

    @cached_property
    def servers(self) -> AsyncServersApi:
        """Return the servers API group."""
        return AsyncServersApi(self._api)

    @cached_property
    def users(self) -> AsyncUsersApi:
        """Return the users API group."""
        return AsyncUsersApi(self._api)
